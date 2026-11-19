"""Tabular import and local storage for the coastal workspace."""
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import zipfile
from pathlib import Path
from itertools import islice

import pandas as pd

from . import database
from .config import MAX_UPLOAD_BYTES, ROOT
from .geospatial import center, validate_geometry
from .schemas import ValidationError

DATA = ROOT / 'data' / 'pesisir'
FORMATS = ('csv', 'tsv', 'txt', 'xlsx', 'xls', 'xlsb', 'ods', 'json', 'jsonl', 'geojson', 'parquet', 'pdf', 'docx')
EXCEL = {'xlsx', 'xls', 'xlsb', 'ods'}
DOCUMENTS = {'pdf', 'docx'}
LIMIT = 20_000
FIELDS = {
    'lokasi': ('Nama lokasi', 'nama lokasi|desa|kelurahan|kecamatan|zone_name|site|lokasi survei|nama zona|stasiun|wilayah'),
    'kabupaten_kota': ('Kabupaten / kota', 'kabupaten|kota|kab kota|kabupaten kota|region'),
    'tanggal': ('Tanggal pengamatan', 'date|observation_date|tanggal pengukuran|akhir_pengamatan|tanggal survei'),
    'ndvi': ('NDVI sekarang', 'ndvi sekarang|ndvi akhir|ndvi terbaru|ndvi mean|ndvi rata rata|current ndvi'),
    'ndvi_sebelumnya': ('NDVI pembanding', 'ndvi awal|ndvi pembanding|baseline ndvi|previous ndvi'),
    'piksel_menurun_pct': ('Piksel dengan penurunan NDVI ≥0,10 (%)', 'piksel turun pct|piksel menurun persen'),
    'tutupan_pct': ('Tutupan tajuk (%)', 'tutupan tajuk|canopy cover pct|canopy cover|tutupan mangrove persen|tutupan persen|tutupan pct|persen tutupan|tutupan kanopi|tutupan kanopi pct'),
    'kehilangan_pct': ('Kehilangan luas mangrove (%)', 'kehilangan mangrove|kehilangan tutupan|kehilangan persen|loss pct|mangrove loss pct'),
    'kerapatan': ('Kerapatan (pohon/ha)', 'kerapatan pohon ha|kerapatan mangrove|tree density|kerapatan pohon per ha'),
    'luas_awal_ha': ('Luas mangrove pembanding (ha)', 'luas awal|luas awal ha|luas sebelumnya ha|baseline area ha'),
    'luas_akhir_ha': ('Luas mangrove sekarang (ha)', 'luas akhir|luas mangrove ha|luas ha|luas sekarang ha|area ha'),
    'legal_status': ('Status izin', 'status legal|status izin|status hukum'),
    'landcover_type': ('Jenis tutupan lahan', 'tutupan lahan|jenis lahan|land cover'),
    'longitude': ('Bujur', 'lon|lng|bujur|long'),
    'latitude': ('Lintang', 'lat|lintang'),
}
BOUNDS = {'ndvi': (-1, 1), 'ndvi_sebelumnya': (-1, 1), 'piksel_menurun_pct': (0, 100),
          'tutupan_pct': (0, 100), 'kehilangan_pct': (0, 100), 'kerapatan': (0, float('inf')),
          'luas_awal_ha': (0, float('inf')), 'luas_akhir_ha': (0, float('inf')),
          'longitude': (-180, 180), 'latitude': (-90, 90)}
MISSING = {'', 'na', 'n/a', 'null', 'nan', 'none', '-', '—'}


def active_edition():
    version = (DATA/'aktif.txt').read_text(encoding='ascii').strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-f0-9]{12}', version):
        raise ValueError('Penanda edisi datasheet bawaan tidak sah.')
    return DATA / version


def fold(value):
    value = unicodedata.normalize('NFKD', str(value).lower().replace('%', ' pct '))
    return ' '.join(re.findall(r'[a-z0-9]+', value))


def auto_columns(columns):
    names = {fold(col): col for col in columns}
    result = {}
    for key, (label, aliases) in FIELDS.items():
        for alias in (key, label, *aliases.split('|')):
            if fold(alias) in names:
                result[key] = names[fold(alias)]
                break
    return result


def _check_file(raw, name):
    extension = Path(name).suffix.lower().lstrip('.')
    if extension not in FORMATS:
        raise ValueError('Pilih tabel CSV, Excel, ODS, TSV, TXT, JSON, GeoJSON atau Parquet.')
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError('Berkas kosong atau melebihi batas unggahan 10 MB.')
    if extension in EXCEL | {'docx'} and zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 120 * 1024**2:
                raise ValueError('Buku kerja terlalu besar setelah dibuka. Ekspor lembar yang diperlukan ke CSV.')
    return extension


def document_tables(raw, ext):
    tables = {}
    if ext == 'docx':
        from docx import Document
        try:
            doc = Document(io.BytesIO(raw))
            for i, table in enumerate(doc.tables, 1):
                tables[f'Tabel {i}'] = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        except Exception as exc:
            raise ValueError('Dokumen Word tidak dapat dibaca. Simpan tabel sebagai DOCX atau Excel.') from exc
    else:
        import pdfplumber
        try:
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                if len(pdf.pages) > 100:
                    raise ValueError('Ekspor halaman yang berisi tabel saja (maksimal 100 halaman).')
                for i, page in enumerate(pdf.pages, 1):
                    for j, table in enumerate(page.extract_tables(), 1):
                        tables[f'Halaman {i} · Tabel {j}'] = table
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('PDF tidak dapat dibaca. Ekspor tabel sebagai Excel atau CSV.') from exc
    tables = {k:v for k,v in tables.items() if len(v) >= 2 and len(v[0]) >= 2}
    if not tables:
        raise ValueError('Tabel teks belum terbaca. Untuk hasil pindai atau tabel tanpa garis, ekspor ke Excel atau CSV.')
    return tables


def _from_grid(grid, header=1):
    if header > len(grid) or not grid[header-1]:
        raise ValueError('Nomor baris judul berada di luar tabel.')
    columns = [' '.join(str(c or '').split()) for c in grid[header-1]]
    if not all(columns) or len(columns) != len(set(columns)):
        raise ValueError('Judul kolom kosong atau ganda. Pilih baris judul yang tepat atau perbaiki nama kolom.')
    rows = []
    for number, row in enumerate(grid[header:], header+1):
        if not any(str(v).strip() for v in row if v is not None):
            continue
        if len(row) != len(columns):
            raise ValueError(f'Baris {number} berisi {len(row)} sel, sedangkan judul memiliki {len(columns)} kolom.')
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def sheet_names(raw, name):
    ext = _check_file(raw, name)
    if ext in DOCUMENTS:
        return list(document_tables(raw, ext))
    if ext not in EXCEL:
        return []
    try:
        with pd.ExcelFile(io.BytesIO(raw), engine='calamine') as book:
            return book.sheet_names
    except Exception as exc:
        raise ValueError('Buku kerja tidak dapat dibaca. Coba simpan kembali sebagai XLSX atau CSV.') from exc


def _json_rows(doc):
    if isinstance(doc, dict) and doc.get('type') == 'FeatureCollection':
        features = doc.get('features')
        if not isinstance(features, list) or len(features) > LIMIT:
            raise ValueError('Daftar fitur GeoJSON tidak sah atau terlalu panjang.')
        crs = doc.get('crs')
        if crs and (not isinstance(crs, dict) or crs.get('properties', {}).get('name') not in
                    ('EPSG:4326', 'urn:ogc:def:crs:OGC:1.3:CRS84', 'urn:ogc:def:crs:EPSG::4326')):
            raise ValueError('Ubah CRS GeoJSON ke WGS84 (EPSG:4326).')
        rows = []
        for number, f in enumerate(features, 1):
            if not isinstance(f, dict) or f.get('type') != 'Feature' or not isinstance(f.get('properties') or {}, dict):
                raise ValueError(f'Fitur GeoJSON ke-{number} tidak sah.')
            row = dict(f.get('properties') or {})
            if f.get('geometry') is not None:
                try:
                    row['latitude'], row['longitude'] = center(validate_geometry(f['geometry']))
                except ValidationError as exc:
                    raise ValueError(f'Geometri pada fitur {number} perlu diperiksa. {exc}') from exc
            rows.append(row)
        return rows
    if isinstance(doc, dict):
        doc = doc.get('data', doc.get('records'))
    if not isinstance(doc, list) or not all(isinstance(r, dict) for r in doc):
        raise ValueError('JSON perlu berisi daftar baris, data, records, atau FeatureCollection.')
    return doc


def read_table(raw, name, sheet=None, header_row=1):
    ext = _check_file(raw, name)
    buffer = io.BytesIO(raw)
    try:
        if ext in EXCEL:
            frame = pd.read_excel(buffer, sheet_name=sheet if sheet is not None else 0, engine='calamine',
                                  header=header_row-1, nrows=LIMIT+1, dtype=object)
        elif ext in DOCUMENTS:
            tables = document_tables(raw, ext)
            frame = _from_grid(tables[sheet or next(iter(tables))], header_row)
        elif ext in ('csv', 'tsv', 'txt'):
            try:
                content = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = raw.decode('cp1252')
            lines = io.StringIO(content)
            for _ in range(header_row-1):
                lines.readline()
            sample = lines.getvalue()[lines.tell():][:8192]
            try:
                sep = csv.Sniffer().sniff(sample, delimiters='\t;,|').delimiter
            except csv.Error:
                first = sample.splitlines()[0] if sample.splitlines() else ''
                sep = max((';', '\t', ',', '|'), key=first.count)
            grid = list(islice(csv.reader(lines, delimiter=sep, strict=True), LIMIT+2))
            frame = _from_grid(grid)
        elif ext == 'jsonl':
            records = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
            frame = pd.DataFrame(_json_rows(records))
        elif ext == 'parquet':
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(buffer)
            if pf.metadata.num_rows > LIMIT or pf.metadata.num_columns > 250 or sum(
                pf.metadata.row_group(i).total_byte_size for i in range(pf.num_row_groups)) > 120 * 1024**2:
                raise ValueError('Tabel Parquet melebihi batas impor.')
            frame = pf.read().to_pandas()
        else:
            frame = pd.DataFrame(_json_rows(json.loads(raw.decode('utf-8-sig'))))
    except (ValueError, OSError, KeyError, TypeError, IndexError, OverflowError, RuntimeError, csv.Error) as exc:
        raise ValueError(f'Berkas tidak dapat dibaca. {exc}') from exc
    frame = frame.dropna(how='all')
    frame.columns = [str(c).strip() for c in frame.columns]
    if frame.empty or len(frame) > LIMIT or len(frame.columns) > 250:
        raise ValueError('Gunakan tabel berisi 1–20.000 baris dan maksimal 250 kolom.')
    if len(set(frame.columns)) != len(frame.columns):
        raise ValueError('Berikan nama yang berbeda untuk setiap kolom.')
    if Path(name).stem.upper().startswith('DEMO_SYNTHETIC_'):
        frame['is_demo'] = True
    return frame


def numeric(value):
    if pd.isna(value) or str(value).strip().lower() in MISSING:
        return None
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, str):
        text = value.strip().rstrip('%').strip().replace(' ', '').replace('−', '-')
        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                text = text.replace('.', '').replace(',', '.')
            else:
                text = text.replace(',', '')
        else:
            text = text.replace(',', '.')
        value = text
    result = float(value)
    if not math.isfinite(result):
        raise ValueError
    return result


def clean_table(frame, columns):
    if not columns.get('lokasi'):
        raise ValueError('Pilih kolom yang berisi nama lokasi, desa, atau kecamatan.')
    mapped = {key: col for key, col in columns.items() if key in FIELDS and col is not None}
    if len(set(mapped.values())) != len(mapped):
        raise ValueError('Setiap kolom sumber hanya dapat dipakai untuk satu isian.')
    if any(col not in frame.columns for col in mapped.values()):
        raise ValueError('Kolom sumber berubah. Periksa kembali pemetaannya.')
    raw = frame[list(mapped.values())].rename(columns={col: key for key, col in mapped.items()})
    # Preserve provenance flags independently of editable measurement mappings.
    flags = [c for c in frame if fold(c) in ('is demo', 'sintetis', 'simulasi', 'quality flag', 'kualitas data')]
    demo_values = {'true', '1', '1 0', 'ya', 'demo', 'synthetic', 'sintetis', 'simulasi'}
    if flags:
        raw['is_demo'] = frame[flags].map(lambda v: fold(v) in demo_values).any(axis=1)
    issues, cleaned = [], []
    for row_no, r in enumerate(raw.to_dict('records'), 1):
        row = {}
        for key, value in r.items():
            if key == 'is_demo':
                row[key] = bool(value)
                continue
            if not pd.api.types.is_scalar(value):
                issues.append((row_no, FIELDS[key][0], 'Nilai perlu berupa satu angka atau teks.'))
                continue
            if pd.isna(value) or str(value).strip().lower() in MISSING:
                continue
            if key in BOUNDS:
                try:
                    v = numeric(value)
                    if not BOUNDS[key][0] <= v <= BOUNDS[key][1]:
                        raise ValueError
                    row[key] = v
                except (ValueError, TypeError, OverflowError):
                    issues.append((row_no, FIELDS[key][0], 'Angka atau satuan tidak sesuai.'))
            elif key == 'tanggal':
                try:
                    if isinstance(value, (float, int)) or str(value).strip().isdigit():
                        raise ValueError
                    text = str(value).strip()
                    dt = pd.to_datetime(text, dayfirst=not bool(re.match(r'^\d{4}[-/]', text)))
                    row[key] = dt.date().isoformat()
                except (ValueError, TypeError, OverflowError):
                    issues.append((row_no, FIELDS[key][0], 'Tanggal tidak terbaca. Gunakan YYYY-MM-DD.'))
            else:
                row[key] = str(value).strip()
        if not row.get('lokasi'):
            issues.append((row_no, 'Nama lokasi', 'Baris dilewati karena nama lokasi kosong.'))
            continue
        row.setdefault('kabupaten_kota', '')
        if ('latitude' in row) != ('longitude' in row):
            row.pop('latitude', None)
            row.pop('longitude', None)
            issues.append((row_no, 'Koordinat', 'Bujur dan lintang perlu berpasangan untuk peta.'))
        cleaned.append(row)
    if not cleaned:
        raise ValueError('Belum ada baris dengan nama lokasi.')
    if len({r.get('is_demo', False) for r in cleaned}) > 1:
        raise ValueError('Pisahkan baris simulasi dan pengamatan ke dalam dua datasheet untuk dianalisis.')
    return pd.DataFrame(cleaned), pd.DataFrame(issues, columns=['Baris data', 'Kolom', 'Catatan'])


def store_sheet(name, raw, filename, sheet, mapping, header, frame):
    title = name.strip()
    if not title:
        raise ValueError('Isi nama datasheet sebelum menyimpan.')
    sha = hashlib.sha256(raw).hexdigest()
    config = json.dumps([sha, sheet, header, mapping], ensure_ascii=False, sort_keys=True)
    identity = hashlib.sha256(config.encode()).hexdigest()
    with database.session() as db:
        db.execute('INSERT INTO coastal_sheets(id,name,filename,sheet,checksum,config_json,rows_json,created_at) '
                   'VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',
                   (identity, title, Path(filename).name, sheet, sha, config,
                    frame.to_json(orient='records', force_ascii=False, double_precision=15), database.now()))
    return identity


def saved_sheets():
    with database.session() as db:
        return [dict(r) for r in db.execute('SELECT id,name,filename,sheet,created_at FROM coastal_sheets ORDER BY created_at DESC, id')]


def load_sheet(identity):
    with database.session() as db:
        row = db.execute('SELECT rows_json FROM coastal_sheets WHERE id=?', (identity,)).fetchone()
    if not row:
        raise ValueError('Datasheet sudah dihapus. Pilih data lain.')
    return pd.DataFrame(json.loads(row['rows_json']))


def delete_sheet(identity):
    with database.session() as db:
        db.execute('DELETE FROM coastal_sheets WHERE id=?', (identity,))
