"""Read every supplied source without changing historical measurements."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dataset_d02 import _read_wrapped_csv


def read_source_csv(path):
    path = Path(path)
    if path.name.startswith('Q2_'):
        return pd.read_csv(path, sep=';', decimal=',', na_values=['NA'])
    if 'dataset_withNAs' in path.name:
        return _read_wrapped_csv(path)
    return pd.read_csv(path, na_values=['NA'])


def profile(frame):
    return {'rows': len(frame), 'columns': [str(c) for c in frame.columns],
            'missing': {str(c): int(frame[c].isna().sum()) for c in frame.columns},
            'numeric_ranges': {str(c): {'min': float(frame[c].min()), 'max': float(frame[c].max())}
                               for c in frame.select_dtypes(include='number') if frame[c].notna().any()}}


def audit_sources(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records, daily, physical = [], [], []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        record = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.suffix == '.csv':
            frame = read_source_csv(path)
            record['tables'] = {'csv': profile(frame)}
            if path.name.startswith('Bathymetry_'):
                coords = frame[['LAT', 'LON']].apply(pd.to_numeric, errors='raise')
                valid = coords.LAT.between(-90, 90) & coords.LON.between(-180, 180)
                record['invalid_coordinate_rows'] = (coords.index[~valid] + 2).tolist()
                record.update(role='spatial_support', reason='Koordinat saja, tanpa label biologis atau nilai kedalaman; tidak menjadi sampel survival.')
            elif path.name == 'pond_dataset_withNAs.csv':
                other = read_source_csv(source_dir / 'pond_dataset_withNAs_UTF8.csv')
                # Encoding variants have identical observations; exclude the copy.
                pd.testing.assert_frame_equal(frame, other)
                record.update(role='duplicate_verified', reason='Isi tabel sama dengan pond_dataset_withNAs_UTF8.csv; tidak dihitung dua kali.')
            elif path.name.startswith('Q1_'):
                record.update(role='ecological_context', reason='Tidak memiliki kunci plot yang terverifikasi ke target semai/survival.')
                if 'year' in frame:
                    summary = frame.groupby(['year', 'area', 'Type']).surface_area_ha.sum(min_count=1).reset_index()
                else:
                    summary = frame.groupby(['rep', 'habitat']).agg(trees=('DBH', 'size'), median_dbh=('DBH', 'median'), basal_area_cm2=('basal_area_cm2', 'sum')).reset_index()
                summary.to_csv(output_dir / (path.stem + '_summary.csv'), index=False)
            elif 'natural_seedling_establishment' in path.name:
                record.update(role='unresolved_target', reason='Kolom survival memuat kode 0/1/2; tanpa kamus kode atau ID bibit. Tidak mengasumsikan 2=hidup/mati.')
                frame.groupby(['blockname', 'species', 'survival']).size().rename('count').reset_index().to_csv(output_dir / 'q3_natural_code_counts.csv', index=False)
            else:
                record.update(role='model_input', reason='Digunakan pada eksperimen dengan target dan fitur yang eksplisit.')
        elif path.suffix == '.xlsx':
            tables = pd.read_excel(path, sheet_name=None)
            record['tables'] = {name: profile(frame) for name, frame in tables.items()}
            record.update(role='physical_context', reason='Belum ada hubungan lokasi/waktu/datum terverifikasi dengan target biologis; tidak diubah menjadi pengukuran di A-C.')
            for sheet, frame in tables.items():
                if {'time', 'water_level'} <= set(frame):
                    dates = pd.to_datetime(frame.time, errors='coerce')
                    values = pd.to_numeric(frame.water_level, errors='coerce')
                    grouped = pd.DataFrame({'date': dates.dt.date, 'water_level': values}).groupby('date').water_level
                    summary = grouped.agg(['size', 'count', 'min', 'max', 'mean']).reset_index()
                    summary['source_file'] = path.name
                    daily.append(summary)
                    record['tables'][sheet]['invalid_timestamps'] = int(dates.isna().sum())
                    record['tables'][sheet]['time_min'] = str(dates.min())
                    record['tables'][sheet]['time_max'] = str(dates.max())
                    record['tables'][sheet]['duplicate_timestamps'] = int(dates.duplicated().sum())
                else:
                    # Preserve raw last-column measurement and its literal unit label.
                    values = pd.to_numeric(frame.iloc[:, -1], errors='coerce')
                    physical.append({'source_file': path.name, 'sheet': sheet, 'rows': len(frame),
                                     'measurement_column': str(frame.columns[-1]),
                                     'numeric_count': int(values.notna().sum()),
                                     'zero_count': int(values.eq(0).sum()),
                                     'min': values.min(), 'max': values.max(), 'median': values.median()})
            if path.name == 'PoleData.xlsx':
                record['reason'] += ' Nilai nol pada tanggal akhir dipertahankan dan ditandai; maknanya belum dikonfirmasi.'
        else:
            raise ValueError(f'Format belum didukung: {path.name}')
        records.append(record)
    if daily:
        pd.concat(daily, ignore_index=True).to_csv(output_dir / 'water_level_daily.csv', index=False)
    pd.DataFrame(physical).to_csv(output_dir / 'physical_measurement_summary.csv', index=False)
    # JSON null, not a fabricated zero, for absent numerical summaries.
    payload = json.loads(pd.Series(records).to_json(orient='values'))
    (output_dir / 'source_audit.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    pd.DataFrame([{k: r[k] for k in ('file', 'sha256', 'role', 'reason')} for r in records]).to_csv(output_dir / 'source_usage.csv', index=False)
    return records
