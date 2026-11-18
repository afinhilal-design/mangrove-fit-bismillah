"""Prepare a historical Q4 cohort with baseline predictors and a fixed outcome horizon."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .training import TrainingError, _sha256


def prepare_survival(source, output_dir):
    source, output_dir = Path(source), Path(output_dir)
    frame = pd.read_csv(source, na_values=['NA'])
    required = ['ID', 'blocknumber', 'species', 'month', 'sediment_raw', 'survival']
    if set(required) - set(frame):
        raise TrainingError('Kolom Q4 tidak lengkap: ' + ', '.join(sorted(set(required) - set(frame))))
    if frame[['ID', 'blocknumber', 'species', 'month']].isna().any().any():
        raise TrainingError('Identitas atau waktu pengamatan Q4 kosong.')
    if not frame['survival'].dropna().isin([0, 1]).all():
        raise TrainingError('Survival harus 0/1 atau kosong.')
    if not np.isfinite(frame['month']).all() or (frame['month'] < 0).any():
        raise TrainingError('Bulan pengamatan tidak valid.')
    # An ambiguous ID is excluded at every time point, never silently collapsed.
    ambiguous = set(frame.loc[frame.duplicated(['ID', 'month'], keep=False), 'ID'])
    unstable = frame.groupby('ID')[['blocknumber', 'species']].nunique().max(axis=1)
    ambiguous.update(unstable[unstable > 1].index)
    clean = frame[~frame['ID'].isin(ambiguous)]
    baseline = clean[clean['month'].eq(0)].copy()
    endpoint = clean[clean['month'].eq(16)][['ID', 'survival']].rename(columns={'survival': 'survival_month16'})
    alive = baseline[baseline['survival'].eq(1)]
    joined = alive.merge(endpoint, on='ID', how='left', validate='one_to_one')
    table = pd.DataFrame({
        'seedling_id': joined['ID'],
        'blok': 'B' + joined['blocknumber'].astype(int).astype(str).str.zfill(2),
        'species': joined['species'],
        'baseline_month': 0,
        'target_month': 16,
        'sediment_level_cm': joined['sediment_raw'],
        'seedling_survival_16_month': joined['survival_month16'],
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_dir / 'training.csv', index=False)
    manifest = {
        'source_file': source.name, 'source_sha256': _sha256(source),
        'source_rows': len(frame), 'source_unique_ids': int(frame['ID'].nunique()),
        'ambiguous_ids_excluded': sorted(ambiguous),
        'rows_with_ambiguous_ids': int(frame['ID'].isin(ambiguous).sum()),
        'ids_without_baseline': sorted(set(clean['ID']) - set(baseline['ID'])),
        'baseline_not_alive_or_missing_excluded': baseline.loc[~baseline['survival'].eq(1), 'ID'].tolist(),
        'cohort_rows': len(table), 'blocks': int(table['blok'].nunique()),
        'missing_baseline_sediment': int(table['sediment_level_cm'].isna().sum()),
        'missing_outcome': int(table['seedling_survival_16_month'].isna().sum()),
        'converted_sha256': _sha256(output_dir / 'training.csv'),
        'target': 'Survival biner pada bulan 16, hanya bibit hidup pada bulan 0.',
        'features': {'sediment_level_cm': 'sediment_raw bulan 0; label satuan mengikuti konverter proyek, belum diverifikasi metadata eksternal'},
        'scenario': 'Data historis diasumsikan mewakili kondisi saat ini untuk esai; bukan survei terbaru.',
        'known_limitations': [
            'Hanya satu fitur sedimen awal; spesies dan ukuran bibit belum menjadi fitur model.',
            'Bulan relatif asli dipertahankan; tanggal kalender baru tidak dibuat.',
            'Tidak menggunakan sedimen, growth, atau length setelah bulan 0 sebagai prediktor.',
            'Blok percobaan dipisahkan utuh; generalisasi geografis belum dibuktikan.',
            'Hasil eksperimen historis bukan validasi kondisi saat ini atau rekomendasi operasional.',
        ],
    }
    (output_dir / 'dataset_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest
