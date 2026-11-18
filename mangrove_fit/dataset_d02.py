"""Konversi dataset D02 gabungan sea-site + pond ke tabel latih MANGROVE-FIT.

Berkas asli:
  - sea-site_dataset_withNAs.csv (van Bijsterveldt dkk., 2020; 4TU)
  - pond_dataset_withNAs_UTF8.csv (van Bijsterveldt dkk., 2020; 4TU)

Strategi:
  - Gabungkan kedua dataset yang memiliki kolom identik (pH, redox, %t_submerged,
    ShearStrngth, dsb.) untuk meningkatkan jumlah sampel dari 56 menjadi ~111.
  - Tambahkan kolom zone_type (sea/pond) sebagai informasi konteks.
  - Target: SeedlingPresence (sea-site, sudah 0/1) dan Seedling density class
    (pond, dibinarisasi: absent→0, present/multiple→1).
  - Fitur dipilih dari kolom yang memiliki sedikit/tanpa NA di KEDUA dataset.
  - Blok spasial = kombinasi zone_type + transect.

Pemetaan kolom ke parameter MANGROVE-FIT (tanpa imputasi; NA tetap kosong):
  %t_submerged      → inundation_duration_h_day  (fraksi × 24)
  pH                → soil_ph
  redox             → redox_mv
  slope             → bed_slope               (hanya sea-site; pond tidak punya)
  ShearStrngth      → shear_strength_kpa       (PARAMETER BARU)
  WC                → water_content_pct         (PARAMETER BARU)
  orgC              → organic_carbon_pct         (PARAMETER BARU)
  BulkDen           → bulk_density_g_cm3        (PARAMETER BARU)
  max_shelter_width → shelter_width_m           (PARAMETER BARU, hanya sea-site)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import ROOT

DATASET_ID = 'D02'
CITATION = ('van Bijsterveldt, C. E. J., dkk. (2020). How to restore mangroves for greenbelt creation '
            'along eroding coasts with abandoned aquaculture ponds. 4TU.ResearchData. '
            'https://doi.org/10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23')
TARGET = 'seedling_presence'
BLOCK = 'blok'
# Fitur yang tersedia di KEDUA dataset, tanpa atau minimal NA:
FEATURES = [
    'inundation_duration_h_day',   # 0 NA di keduanya
    'soil_ph',                     # 2 NA di sea-site, 0 di pond (→ 2/111)
    'redox_mv',                    # 2 NA di sea-site, 1 di pond (→ 3/111)
    'bed_slope',                   # 0 NA di sea-site, NA di pond (→ 55/111) — terlalu banyak NA → TIDAK DIPAKAI
    'shear_strength_kpa',          # 7 NA di sea-site, 0 di pond (→ 7/111)
]
# Fitur akhir yang BENAR-BENAR dipakai (cukup lengkap di gabungan):
FINAL_FEATURES = [
    'inundation_duration_h_day',
    'soil_ph',
    'redox_mv',
    'shear_strength_kpa',
]
TRAIN_CSV = ROOT / 'data' / 'training' / 'D02_combined_seedling.csv'
MANIFEST = ROOT / 'data' / 'manifests' / 'D02.json'


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_wrapped_csv(path: Path) -> pd.DataFrame:
    """Baca CSV yang baris-barisnya dibungkus kutip ganda (format 4TU sea-site/pond)."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    lines = [l for l in text.splitlines() if l.strip()]
    first = next(csv.reader([lines[0]]))
    if len(first) == 1 and ',' in first[0]:
        lines = [next(csv.reader([l]))[0] for l in lines]
    return pd.read_csv(io.StringIO('\n'.join(lines)), na_values=['NA'])


def convert_combined(sea_site_path, pond_path, out_csv=None, manifest_path=None) -> dict:
    """Gabungkan sea-site + pond dan tulis tabel latih D02."""
    sea_site_path = Path(sea_site_path)
    pond_path = Path(pond_path)
    out_csv = Path(out_csv or TRAIN_CSV)
    manifest_path = Path(manifest_path or MANIFEST)

    # --- Baca sea-site ---
    ss = _read_wrapped_csv(sea_site_path)
    required_ss = ['transect', 'station', 'lat', 'lon', 'pH', 'redox',
                   '%t_submerged', 'slope', 'ShearStrngth', 'SeedlingPresence']
    absent = [c for c in required_ss if c not in ss.columns]
    if absent:
        raise ValueError('Kolom sea-site tidak ditemukan: ' + ', '.join(absent))

    ss_out = pd.DataFrame({
        'zone_type': 'sea',
        BLOCK: 'sea_T' + ss['transect'].astype(int).astype(str).str.zfill(2),
        'titik': 'ss_' + ss['transect'].astype(int).astype(str) + '-' + ss['station'].astype(int).astype(str),
        'latitude': ss['lat'],
        'longitude': ss['lon'],
        TARGET: ss['SeedlingPresence'].astype(int),
        'inundation_duration_h_day': (ss['%t_submerged'] * 24).round(4),
        'soil_ph': ss['pH'],
        'redox_mv': ss['redox'],
        'bed_slope': ss['slope'],
        'shear_strength_kpa': ss['ShearStrngth'],
        'water_content_pct': ss['WC'],
        'organic_carbon_pct': ss['orgC'],
        'bulk_density_g_cm3': ss['BulkDen'],
        'shelter_width_m': ss['max_shelter_width_linestudy'],
        'seedling_density_raw': ss['SeedlingDen'],
    })

    # --- Baca pond ---
    pond = _read_wrapped_csv(pond_path)
    required_pond = ['transect', 'station', 'lat', 'lon', 'pH', 'redox',
                     '%t_submerged', 'ShearStrngth', 'Seedling density class']
    absent_p = [c for c in required_pond if c not in pond.columns]
    if absent_p:
        raise ValueError('Kolom pond tidak ditemukan: ' + ', '.join(absent_p))

    # Binarisasi target: absent→0, present/multiple→1
    pond_target = pond['Seedling density class'].map(
        {'absent': 0, 'present': 1, 'multiple': 1}
    )
    if pond_target.isna().any():
        raise ValueError('Seedling density class pond memiliki nilai tak dikenal.')

    pond_out = pd.DataFrame({
        'zone_type': 'pond',
        BLOCK: 'pond_T' + pond['transect'].astype(int).astype(str).str.zfill(2),
        'titik': 'pd_' + pond['transect'].astype(int).astype(str) + '-' + pond['station'].astype(int).astype(str),
        'latitude': pond['lat'],
        'longitude': pond['lon'],
        TARGET: pond_target.astype(int),
        'inundation_duration_h_day': (pond['%t_submerged'] * 24).round(4),
        'soil_ph': pond['pH'],
        'redox_mv': pond['redox'],
        'bed_slope': float('nan'),  # pond tidak punya slope
        'shear_strength_kpa': pond['ShearStrngth'],
        'water_content_pct': pond['WC'],
        'organic_carbon_pct': pond['orgC'],
        'bulk_density_g_cm3': pond['BulkDen'],
        'shelter_width_m': float('nan'),  # pond tidak punya shelter
        'seedling_density_raw': pond['SeedlingDen'],
    })

    # --- Gabungkan ---
    combined = pd.concat([ss_out, pond_out], ignore_index=True)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_csv, index=False)

    # --- Manifest ---
    manifest = {
        'dataset_id': DATASET_ID,
        'citation': CITATION,
        'license': 'Periksa lisensi di halaman 4TU sebelum distribusi ulang.',
        'source_files': {
            'sea_site': {
                'name': sea_site_path.name,
                'sha256': _sha256(sea_site_path),
                'rows': int(len(ss)),
            },
            'pond': {
                'name': pond_path.name,
                'sha256': _sha256(pond_path),
                'rows': int(len(pond)),
            },
        },
        'converted_file': out_csv.name,
        'converted_sha256': _sha256(out_csv),
        'converted_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'rows': int(len(combined)),
        'rows_per_zone': {'sea': int(len(ss_out)), 'pond': int(len(pond_out))},
        'blocks': int(combined[BLOCK].nunique()),
        'target': {
            'column': TARGET,
            'source_sea': 'SeedlingPresence (0/1)',
            'source_pond': 'Seedling density class (absent→0, present/multiple→1)',
            'positives': int(combined[TARGET].sum()),
            'negatives': int((combined[TARGET] == 0).sum()),
            'definition': 'Semai mangrove alami ditemukan (1) atau tidak (0) pada titik pengamatan.',
        },
        'block_column': BLOCK,
        'features': {},
        'known_limitations': [
            f'{len(combined)} titik pengamatan, {combined[BLOCK].nunique()} blok; ukuran kecil.',
            'Pond tidak memiliki data slope dan shelter width.',
            'Target biner digabung dari dua definisi berbeda (presence vs density class).',
            'Semua data berasal dari satu wilayah (Demak, Jawa Tengah).',
        ],
    }
    # Catat NA per fitur
    all_features = ['inundation_duration_h_day', 'soil_ph', 'redox_mv', 'bed_slope',
                    'shear_strength_kpa', 'water_content_pct', 'organic_carbon_pct',
                    'bulk_density_g_cm3', 'shelter_width_m']
    for f in all_features:
        manifest['features'][f] = {
            'missing': int(combined[f].isna().sum()),
            'available': int(combined[f].notna().sum()),
        }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest
