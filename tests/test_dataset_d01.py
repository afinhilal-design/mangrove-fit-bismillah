"""Uji konverter D01 sea-site, migrasi parameter baru, dan stratifikasi blok.

Baris CSV di sini adalah fixture format (ditulis ke folder sementara) untuk menguji parser,
bukan data lapangan.
"""
import json
import pandas as pd
import pytest

from mangrove_fit.dataset_d01 import read_sea_site, convert_sea_site, FEATURES, TARGET, BLOCK
from mangrove_fit.schemas import PARAMETERS, upgrade_observations
from mangrove_fit.training import spatial_block_split, approve_candidate, TrainingError

HEADER = ['transect', 'station', 'lat', 'lon', 'treatment', 'pH', 'redox', 'SD50MUM_2 (µm)', '%t_submerged', 'slope', 'SeedlingDen', 'SeedlingPresence']


def _wrapped(rows):
    """Tulis seperti berkas asli: cp1252, setiap baris dibungkus satu field berkutip."""
    def line(values):
        inner = ','.join(f'"{v}"' if isinstance(v, str) and v != 'NA' else str(v) for v in values)
        return '"' + inner.replace('"', '""') + '"'
    return ('\n'.join(line(r) for r in [HEADER, *rows]) + '\n').encode('cp1252')


ROWS = [[1, '1', -6.9, 110.5, 'ES', 7.0, -150.0, 'NA', 0.5, 0.01, 0, 0],
        [1, '2', -6.9, 110.5, 'ES', 'NA', 'NA', 'NA', 0.25, -0.02, 0, 0],
        [2, '1', -6.91, 110.49, 'RS', 6.9, -170.0, 12.0, 1.0, 0.0, 3, 1]]


def test_reads_wrapped_cp1252_file(tmp_path):
    p = tmp_path / 'sea.csv'; p.write_bytes(_wrapped(ROWS))
    df = read_sea_site(p)
    assert len(df) == 3 and 'SD50MUM_2 (µm)' in df.columns
    assert df['pH'].isna().sum() == 1 and df['SeedlingPresence'].tolist() == [0, 0, 1]


def test_convert_maps_without_imputation(tmp_path):
    p = tmp_path / 'sea.csv'; p.write_bytes(_wrapped(ROWS))
    m = convert_sea_site(p, tmp_path / 'out.csv', tmp_path / 'm.json', tmp_path / 'raw')
    out = pd.read_csv(tmp_path / 'out.csv')
    assert out['inundation_duration_h_day'].tolist() == [12.0, 6.0, 24.0]
    assert out['soil_ph'].isna().sum() == 1 and out['redox_mv'].isna().sum() == 1  # NA tetap NA
    assert out[BLOCK].tolist() == ['T01', 'T01', 'T02'] and out[TARGET].sum() == 1
    assert (tmp_path / 'raw' / 'sea.csv').read_bytes() == p.read_bytes()  # salinan asli identik
    assert m['source_sha256'] and m['features']['soil_ph']['missing'] == 1
    assert set(FEATURES) <= set(PARAMETERS)


def test_convert_rejects_bad_submergence(tmp_path):
    rows = [r[:] for r in ROWS]; rows[0][8] = 1.5
    p = tmp_path / 'sea.csv'; p.write_bytes(_wrapped(rows))
    with pytest.raises(ValueError, match='0–1'):
        convert_sea_site(p, tmp_path / 'o.csv', tmp_path / 'm.json', tmp_path / 'raw')


def test_old_zone_gets_new_parameters_as_missing():
    z = {'observations': {'salinity_ppt': {'value': 20.0}}}
    upgrade_observations(z)
    for k in ('soil_ph', 'redox_mv', 'bed_slope'):
        assert z['observations'][k]['value'] is None and z['observations'][k]['quality_flag'] == 'missing'
    assert z['observations']['salinity_ppt']['value'] == 20.0


def test_stratified_split_spreads_positive_blocks():
    rows = []
    for b in range(10):
        for i in range(5):
            rows.append({'blok': f'B{b}', 'y': int(b < 5 and i == 0)})
    frame = pd.DataFrame(rows)
    for seed in range(20):
        split = spatial_block_split(frame, 'blok', seed=seed, label_col='y')
        for part in split.values():
            assert frame[frame['blok'].isin(part)]['y'].nunique() == 2


def test_approval_rejects_chance_level_cross_validation(tmp_path):
    from tests.test_training import _make_csv, FEATURES as F
    pytest.importorskip('xgboost')
    from mangrove_fit.training import train_candidate
    card = train_candidate(_make_csv(tmp_path / 'l.csv'), 'label', F, 'blok', tmp_path / 'cand')
    assert 'cv_leave_one_block_out' in card['metrics']
    card['metrics']['cv_leave_one_block_out']['balanced_accuracy'] = 0.5
    (tmp_path / 'cand' / 'model_card.json').write_text(json.dumps(card))
    with pytest.raises(TrainingError, match='acak'):
        approve_candidate('Peninjau', candidate_dir=tmp_path / 'cand', active_dir=tmp_path / 'a', archive_dir=tmp_path / 'ar')
