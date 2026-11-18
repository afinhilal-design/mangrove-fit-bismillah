"""Konversi dataset D03 Q4 (EMR-and-planting) ke tabel latih MANGROVE-FIT.

Berkas asli: Q4_EMR-and-planting.csv (van Bijsterveldt dkk., 2022; 4TU)

Dataset ini mencatat kelangsungan hidup semai mangrove yang ditanam pada percobaan
rehabilitasi dengan dam permeable (EMR = Ecological Mangrove Rehabilitation).

Strategi:
  - Data longitudinal: setiap bibit diukur pada 7 titik waktu (bulan 0, 0.5, 1, 1.5, 2.5, 8, 16).
  - Untuk training, ambil **observasi terakhir** per bibit (survival final).
  - Fitur: sediment_raw, sediment_rel, spesies (one-hot encoded karena kategorik).
  - Blok spasial = blocknumber (20 blok — cukup untuk pembagian train/val/test).

Target: survival (0/1) pada observasi terakhir per bibit.

Pemetaan fitur ke parameter MANGROVE-FIT:
  sediment_raw  → sediment_level_cm    (PARAMETER BARU; tinggi sedimen mentah dalam cm)
  sediment_rel  → sediment_change_cm   (PARAMETER BARU; perubahan relatif sedimen dalam cm)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import ROOT

DATASET_ID = 'D03'
CITATION = ('van Bijsterveldt, C. E. J., dkk. (2022). To Plant or Not to Plant: '
            'experimental data on mangrove restoration. 4TU.ResearchData. '
            'https://doi.org/10.4121/17927198')
TARGET = 'seedling_survival'
BLOCK = 'blok'
FEATURES = ['sediment_level_cm', 'sediment_change_cm']
TRAIN_CSV = ROOT / 'data' / 'training' / 'D03_q4_planting_survival.csv'
MANIFEST = ROOT / 'data' / 'manifests' / 'D03.json'


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convert_q4(src_path, out_csv=None, manifest_path=None) -> dict:
    """Proses Q4 menjadi tabel latih per bibit (observasi terakhir)."""
    src_path = Path(src_path)
    out_csv = Path(out_csv or TRAIN_CSV)
    manifest_path = Path(manifest_path or MANIFEST)

    q4 = pd.read_csv(src_path, na_values=['NA'])

    required = ['blocknumber', 'ID', 'species', 'month', 'sediment_raw', 'sediment_rel', 'survival']
    absent = [c for c in required if c not in q4.columns]
    if absent:
        raise ValueError('Kolom Q4 tidak ditemukan: ' + ', '.join(absent))

    # Validasi survival
    if not q4['survival'].isin([0, 1]).all():
        raise ValueError('Kolom survival harus berisi 0 atau 1.')

    # Ambil observasi terakhir per bibit (ID unik per blocknumber+species)
    # Sort by month ascending, lalu ambil terakhir per ID
    q4_sorted = q4.sort_values('month')
    last_obs = q4_sorted.groupby('ID').last().reset_index()

    # Buat tabel latih
    out = pd.DataFrame({
        BLOCK: 'B' + last_obs['blocknumber'].astype(int).astype(str).str.zfill(2),
        'seedling_id': last_obs['ID'],
        'species': last_obs['species'],
        'final_month': last_obs['month'],
        TARGET: last_obs['survival'].astype(int),
        'sediment_level_cm': last_obs['sediment_raw'],
        'sediment_change_cm': last_obs['sediment_rel'],
    })

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)

    # Manifest
    manifest = {
        'dataset_id': DATASET_ID,
        'citation': CITATION,
        'license': 'Periksa lisensi di halaman 4TU sebelum distribusi ulang.',
        'source_file': src_path.name,
        'source_sha256': _sha256(src_path),
        'source_rows': int(len(q4)),
        'converted_file': out_csv.name,
        'converted_sha256': _sha256(out_csv),
        'converted_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'rows': int(len(out)),
        'unique_seedlings': int(out['seedling_id'].nunique()),
        'blocks': int(out[BLOCK].nunique()),
        'aggregation': 'Observasi terakhir per bibit (ID); bulan terakhir bervariasi per bibit.',
        'target': {
            'column': TARGET,
            'source': 'survival (0/1) pada observasi terakhir per bibit',
            'positives': int(out[TARGET].sum()),
            'negatives': int((out[TARGET] == 0).sum()),
            'definition': 'Bibit mangrove yang ditanam masih hidup (1) atau mati (0) pada pengamatan terakhir.',
        },
        'block_column': BLOCK,
        'species_distribution': out['species'].value_counts().to_dict(),
        'features': {
            'sediment_level_cm': {
                'source': 'sediment_raw',
                'missing': int(out['sediment_level_cm'].isna().sum()),
                'available': int(out['sediment_level_cm'].notna().sum()),
            },
            'sediment_change_cm': {
                'source': 'sediment_rel',
                'missing': int(out['sediment_change_cm'].isna().sum()),
                'available': int(out['sediment_change_cm'].notna().sum()),
            },
        },
        'known_limitations': [
            'Hanya 2 fitur lingkungan kontinu (sediment); tidak ada pH, salinitas, inundasi.',
            'Variabel spesies kategorik tidak masuk fitur model (hanya numerik).',
            'Data berasal dari satu eksperimen di satu wilayah (Demak, Jawa Tengah).',
            'Observasi terakhir per bibit: bulan pengamatan bervariasi (tidak semua diikuti sampai bulan 16).',
        ],
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest
