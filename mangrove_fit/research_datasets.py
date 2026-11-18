"""Explicit research schemas, separate from the application's observation schema."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from .data_audit import read_source_csv
from .survival_training import prepare_survival


def coordinate_groups(frame):
    """Keep whole transects and shared coordinates in the same connected component."""
    parent = {str(t): str(t) for t in frame['transect']}
    def root(t):
        while parent[t] != t:
            t = parent[t]
        return t
    for _, part in frame.groupby(['lat', 'lon']):
        values = part.transect.astype(str).unique()
        for t in values[1:]:
            parent[root(t)] = root(values[0])
    return frame.transect.astype(str).map(lambda t: 'component_' + root(t))


def build_tasks(source_dir, output_dir):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    sea = read_source_csv(source_dir / 'sea-site_dataset_withNAs.csv')
    pond = read_source_csv(source_dir / 'pond_dataset_withNAs_UTF8.csv')
    sea['target'] = sea.SeedlingPresence
    pond['target'] = pond['Seedling density class'].map({'absent': 0, 'present': 1, 'multiple': 1})
    if pond.target.isna().any() or not sea.target.isin([0, 1]).all():
        raise ValueError('Label keberadaan semai tidak valid.')
    sea['zone_type'], pond['zone_type'] = 'sea', 'pond'
    presence = pd.concat([sea, pond], ignore_index=True)
    presence['group'] = coordinate_groups(presence)
    presence['row_id'] = presence.zone_type + '_' + presence.transect.astype(str) + '_' + presence.station.astype(str)
    common = [c for c in sea.columns if c in pond.columns and c not in
              ['transect', 'station', 'lat', 'lon', 'SeedlingDen', 'target', 'zone_type']]
    # Raw field names and units remain in the schema; no speculative unit conversion.
    common = [c for c in common if pd.api.types.is_numeric_dtype(presence[c])]
    survival_dir = output_dir / 'q4_preparation'
    prepare_survival(source_dir / 'Q4_EMR-and-planting.csv', survival_dir)
    q4 = pd.read_csv(survival_dir / 'training.csv')
    raw = read_source_csv(source_dir / 'Q4_EMR-and-planting.csv')
    initial = raw[raw.month.eq(0)][['ID', 'length']]
    initial = initial[initial.ID.isin(q4.seedling_id)]
    q4 = q4.merge(initial, left_on='seedling_id', right_on='ID', validate='one_to_one')
    q4 = q4.rename(columns={'seedling_id': 'row_id', 'blok': 'group', 'seedling_survival_16_month': 'target'})
    q3raw = read_source_csv(source_dir / 'Q3_EMR-dams_seedling_survival_exp.csv')
    if q3raw.duplicated(['ID', 'month']).any():
        raise ValueError('ID/bulan Q3 ganda; perlu audit.')
    if (q3raw.groupby('ID')[['blockname', 'PlantingTreatment', 'SiteCondition']].nunique() > 1).any().any():
        raise ValueError('Identitas bibit Q3 tidak konsisten.')
    q3 = q3raw[q3raw.month.eq(3) & q3raw.survival.eq(1)].drop(columns='survival')
    q3 = q3.merge(q3raw[q3raw.month.eq(10)][['ID', 'survival']], on='ID', how='left', validate='one_to_one')
    q3 = q3.rename(columns={'ID': 'row_id', 'blockname': 'group', 'survival': 'target'})
    q2 = read_source_csv(source_dir / 'Q2_EMR-hydrology_propagules.csv')
    ambiguous = q2.duplicated(['trap_ID', 'date', 'species'], keep=False)
    q2.loc[ambiguous].to_csv(output_dir / 'q2_ambiguous_excluded.csv', index=False)
    q2 = q2.loc[~ambiguous].copy()
    counts = pd.to_numeric(q2.prop_count, errors='raise')
    if counts.dropna().lt(0).any():
        raise ValueError('Jumlah propagul negatif.')
    q2['target'] = (counts > 0).astype(float).where(counts.notna())
    dates = pd.to_datetime(q2.date, errors='raise')
    q2['day_sin'] = np.sin(2 * np.pi * dates.dt.dayofyear / 365.25)
    q2['day_cos'] = np.cos(2 * np.pi * dates.dt.dayofyear / 365.25)
    q2['row_id'] = q2.trap_ID.astype(str) + '_' + q2.date + '_' + q2.species
    q2['group'] = q2.trap_ID.astype(str)
    tasks = {
        'presence_expanded': (presence, common, ['zone_type'], ['%t_submerged', 'pH', 'redox'],
                              'Keberadaan semai alami; lokasi dengan koordinat sama digabung dalam grup validasi.'),
        'q4_survival_expanded': (q4, ['sediment_level_cm', 'length'], ['species'], ['sediment_level_cm'],
                                 'Survival bulan 16 pada bibit hidup bulan 0; fitur hanya bulan 0.'),
        'q3_survival_conditional': (q3, [], ['SiteCondition', 'PlantingTreatment'], None,
                                   'Survival bulan 10, bersyarat masih hidup bulan 3; bukan survival sejak tanam.'),
        'q2_propagule_presence': (q2, ['day_sin', 'day_cos'], ['zone', 'species'], None,
                                  'Propagul ditemukan pada perangkap/tanggal/spesies; bukan survival atau prediksi tahun mendatang.'),
    }
    preparation = {
        'q2_ambiguous_rows_excluded': int(ambiguous.sum()),
        'q2_missing_labels': int(q2.target.isna().sum()),
        'q3_source_rows': len(q3raw), 'q3_cohort_alive_month3': len(q3),
        'presence_coordinate_connected_groups': int(presence.group.nunique()),
        'presence_common_numeric_features': common,
        'raw_sources_unchanged': True,
    }
    (output_dir / 'preparation.json').write_text(json.dumps(preparation, indent=2), encoding='utf-8')
    return tasks
