"""Konversi dataset D01 'sea-site' (van Bijsterveldt dkk., 2020; pesisir Demak) ke tabel latih MANGROVE-FIT.

Berkas asli: sea-site_dataset_withNAs.csv (4TU.ResearchData, DOI 10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23).
Keanehan format yang ditangani:
  - pengodean Windows-1252 (karakter 'µ' pada nama kolom sedimen);
  - setiap baris dibungkus sebagai SATU field ber-tanda-kutip, dengan kutip ganda di dalamnya.

Pemetaan (tanpa imputasi; NA tetap kosong):
  transect          -> blok                       (blok spasial untuk pembagian train/val/test)
  SeedlingPresence  -> seedling_presence          (target 0/1: semai alami ditemukan pada titik)
  %t_submerged      -> inundation_duration_h_day  (= fraksi waktu tergenang 0–1 × 24 jam; nilai turunan)
  pH                -> soil_ph
  redox             -> redox_mv                   (satuan diasumsikan mV; verifikasi dengan metadata 4TU)
  slope             -> bed_slope                  (rasio; definisi persis perlu dicek di metadata 4TU)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import ROOT

DATASET_ID = 'D01'
CITATION = ('van Bijsterveldt, C. E. J., dkk. (2020). How to restore mangroves for greenbelt creation along eroding '
            'coasts with abandoned aquaculture ponds. 4TU.ResearchData. https://doi.org/10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23')
TARGET = 'seedling_presence'
BLOCK = 'blok'
FEATURES = ['inundation_duration_h_day', 'soil_ph', 'redox_mv', 'bed_slope']
RAW_DIR = ROOT / 'data' / 'raw' / DATASET_ID
TRAIN_CSV = ROOT / 'data' / 'training' / 'D01_sea_site_seedling.csv'
MANIFEST = ROOT / 'data' / 'manifests' / 'D01.json'
REQUIRED = ['transect', 'station', 'lat', 'lon', 'treatment', 'pH', 'redox', '%t_submerged', 'slope', 'SeedlingPresence']


def read_sea_site(path) -> pd.DataFrame:
    """Baca berkas sea-site asli (atau CSV biasa dengan kolom yang sama)."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    lines = [line for line in text.splitlines() if line.strip()]
    first = next(csv.reader([lines[0]]))
    if len(first) == 1 and ',' in first[0]:  # baris dibungkus satu field
        lines = [next(csv.reader([line]))[0] for line in lines]
    frame = pd.read_csv(io.StringIO('\n'.join(lines)), na_values=['NA'])
    absent = [c for c in REQUIRED if c not in frame.columns]
    if absent:
        raise ValueError('Kolom sea-site tidak ditemukan: ' + ', '.join(absent) + '.')
    return frame


def convert_sea_site(src, out_csv=None, manifest_path=None, raw_dir=None) -> dict:
    src = Path(src)
    out_csv = Path(out_csv or TRAIN_CSV)
    manifest_path = Path(manifest_path or MANIFEST)
    raw_dir = Path(raw_dir or RAW_DIR)
    frame = read_sea_site(src)
    sub = frame['%t_submerged']
    if ((sub < 0) | (sub > 1)).any():
        raise ValueError('%t_submerged di luar 0–1; pemetaan ke jam/hari tidak berlaku.')
    labels = frame['SeedlingPresence']
    if not labels.isin([0, 1]).all():
        raise ValueError('SeedlingPresence harus 0/1.')
    out = pd.DataFrame({
        BLOCK: 'T' + frame['transect'].astype(int).astype(str).str.zfill(2),
        'titik': frame['transect'].astype(int).astype(str) + '-' + frame['station'].astype(int).astype(str),
        'latitude': frame['lat'], 'longitude': frame['lon'], 'perlakuan': frame['treatment'],
        TARGET: labels.astype(int),
        'inundation_duration_h_day': (sub * 24).round(4),
        'soil_ph': frame['pH'], 'redox_mv': frame['redox'], 'bed_slope': frame['slope'],
        'seedling_density_raw': frame['SeedlingDen'],
    })
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)

    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = raw_dir / src.name
    if src.resolve() != raw_copy.resolve():
        shutil.copy2(src, raw_copy)  # salinan byte-identik, tidak diubah
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    manifest = {
        'dataset_id': DATASET_ID, 'citation': CITATION,
        'license': 'Periksa lisensi di halaman 4TU sebelum distribusi ulang.',
        'source_file': raw_copy.relative_to(ROOT).as_posix() if ROOT in raw_copy.resolve().parents else str(raw_copy),
        'source_sha256': sha(raw_copy), 'source_encoding': 'cp1252 (baris terbungkus kutip)',
        'converted_file': out_csv.relative_to(ROOT).as_posix() if ROOT in out_csv.resolve().parents else str(out_csv),
        'converted_sha256': sha(out_csv),
        'converted_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'rows': int(len(out)), 'blocks': int(out[BLOCK].nunique()),
        'target': {'column': TARGET, 'source': 'SeedlingPresence', 'positives': int(out[TARGET].sum()),
                   'definition': 'Semai mangrove alami ditemukan (1) atau tidak (0) pada titik pengamatan sea-site.'},
        'block_column': BLOCK,
        'features': {
            'inundation_duration_h_day': {'source': '%t_submerged', 'transform': 'x * 24 (fraksi waktu tergenang → jam/hari)', 'missing': int(out['inundation_duration_h_day'].isna().sum())},
            'soil_ph': {'source': 'pH', 'transform': 'identitas', 'missing': int(out['soil_ph'].isna().sum())},
            'redox_mv': {'source': 'redox', 'transform': 'identitas (satuan diasumsikan mV)', 'missing': int(out['redox_mv'].isna().sum())},
            'bed_slope': {'source': 'slope', 'transform': 'identitas (rasio; definisi perlu dicek)', 'missing': int(out['bed_slope'].isna().sum())},
        },
        'not_used': 'Variabel sedimen (24–26 NA dari 56), orgC, BulkDen, ShearStrngth, indeks Sentinel-2 dan kolom vegetasi tidak dipakai; '
                    'S2/vegetasi 2016 berisiko kebocoran label, sedimen terlalu banyak kosong.',
        'known_limitations': ['56 titik, 10 transek; semua titik positif berada pada 5 transek perlakuan RS.',
                              'Satuan redox dan definisi slope belum diverifikasi terhadap metadata asli.'],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest
