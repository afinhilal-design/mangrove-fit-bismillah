"""Uji pipeline pelatihan & persetujuan.

Data di sini dibangkitkan acak di folder sementara HANYA untuk menguji kode.
Tidak ada model atau metrik dari uji ini yang disimpan ke repositori.
"""
import json
import numpy as np
import pandas as pd
import pytest

from mangrove_fit.training import (TrainingError, approve_candidate, classification_metrics,
                                   load_training_table, spatial_block_split, train_candidate)
from mangrove_fit.model_service import get_model_status, predict_zone, load_card
from mangrove_fit.explain_service import explain_zone

FEATURES = ['salinity_ppt', 'inundation_duration_h_day', 'elevation_m']


def _make_csv(path, n_blocks=12, per_block=25, seed=0, learnable=True):
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(n_blocks):
        sal = rng.uniform(0, 40, per_block); inu = rng.uniform(0, 24, per_block); ele = rng.uniform(-1, 3, per_block)
        y = ((sal < 25) & (inu > 6)).astype(int) if learnable else rng.integers(0, 2, per_block)
        for i in range(per_block):
            rows.append({'blok': f'B{b:02d}', 'label': int(y[i]), 'salinity_ppt': sal[i],
                         'inundation_duration_h_day': inu[i], 'elevation_m': ele[i]})
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


@pytest.fixture
def xgb():
    return pytest.importorskip('xgboost')


def test_metrics_known_values():
    m = classification_metrics([1, 1, 0, 0], [0.9, 0.2, 0.8, 0.1])
    assert m['confusion'] == {'tp': 1, 'fp': 1, 'tn': 1, 'fn': 1}
    assert m['balanced_accuracy'] == 0.5 and m['f1'] == 0.5
    # Urutan skor: 1(0.9),0(0.8),1(0.2),0(0.1) -> AP = (1/1 + 2/3)/2
    assert m['pr_auc'] == round((1 + 2 / 3) / 2, 4)
    assert classification_metrics([1, 0], [1.0, 0.0])['balanced_accuracy'] == 1.0


def test_average_precision_ties_are_order_independent():
    assert classification_metrics([1, 1, 0, 0], [0.5] * 4)['pr_auc'] == 0.5
    assert classification_metrics([0, 0, 1, 1], [0.5] * 4)['pr_auc'] == 0.5
    assert classification_metrics([], [])['pr_auc'] is None


def test_candidate_shap_export(tmp_path, xgb):
    from mangrove_fit.training_report import export_candidate_report
    candidate = tmp_path / 'report'
    candidate.mkdir()
    source = _make_csv(candidate / 'training.csv')
    card = train_candidate(source, 'label', FEATURES, 'blok', candidate, num_rounds=20)
    report = export_candidate_report(candidate)
    assert report['additivity_ok']
    rows = pd.read_csv(candidate / 'predictions_shap.csv')
    assert len(rows) == card['training']['rows_used']
    assert set(rows.loc[rows['split'] == 'test', 'blok']) == set(card['training']['blocks']['test'])
    assert np.allclose(rows['bias_log_odds'] + rows[['shap_' + f for f in FEATURES]].sum(axis=1),
                       rows['margin_log_odds'], atol=1e-5)
    source.write_text('changed')
    with pytest.raises(TrainingError, match='Checksum'):
        export_candidate_report(candidate)


def test_block_split_is_disjoint_and_complete(tmp_path):
    frame, _ = load_training_table(_make_csv(tmp_path / 'd.csv'), 'label', FEATURES, 'blok')
    split = spatial_block_split(frame, 'blok')
    sets = [set(v) for v in split.values()]
    assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])
    assert set().union(*sets) == set(frame['blok'])
    with pytest.raises(TrainingError):
        spatial_block_split(frame[frame['blok'].isin(['B00', 'B01'])], 'blok')


def test_load_table_validates_and_does_not_impute(tmp_path):
    p = _make_csv(tmp_path / 'd.csv', n_blocks=4, per_block=5)
    df = pd.read_csv(p); df.loc[0, 'salinity_ppt'] = None; df.loc[1, 'label'] = None; df.to_csv(p, index=False)
    frame, dropped = load_training_table(p, 'label', FEATURES, 'blok')
    assert dropped == 2 and len(frame) == 18 and frame['salinity_ppt'].notna().all()
    df.loc[2, 'label'] = 3; df.to_csv(p, index=False)
    with pytest.raises(TrainingError, match='biner'):
        load_training_table(p, 'label', FEATURES, 'blok')
    with pytest.raises(TrainingError, match='numerik'):
        load_training_table(p, 'label', ['substrate_type'], 'blok')


def test_synthetic_data_is_blocked_and_never_approvable(tmp_path, xgb):
    p = _make_csv(tmp_path / 'DEMO_SYNTHETIC_latih.csv')
    with pytest.raises(TrainingError, match='sintetis'):
        train_candidate(p, 'label', FEATURES, 'blok', tmp_path / 'cand')
    card = train_candidate(p, 'label', FEATURES, 'blok', tmp_path / 'cand', allow_synthetic=True)
    assert card['status'] == 'SYNTHETIC_TEST_ONLY' and card['synthetic']
    with pytest.raises(TrainingError, match='sintetis'):
        approve_candidate('Peninjau', candidate_dir=tmp_path / 'cand', active_dir=tmp_path / 'active', archive_dir=tmp_path / 'arch')
    # Bahkan bila kartu diubah manual menjadi APPROVED, gerbang inferensi tetap menolak.
    card.update(status='APPROVED', approved_by='x')
    (tmp_path / 'cand' / 'model_card.json').write_text(json.dumps(card))
    assert get_model_status(tmp_path / 'cand')['status'] == 'MODEL_INVALID'


def test_train_approve_predict_explain(tmp_path, xgb, zones):
    p = _make_csv(tmp_path / 'latih.csv')
    card = train_candidate(p, 'label', FEATURES, 'blok', tmp_path / 'cand')
    assert card['status'] == 'PENDING_REVIEW' and card['approved_by'] is None
    blocks = card['training']['blocks']
    assert not set(blocks['train']) & set(blocks['test'])
    assert card['metrics']['test']['balanced_accuracy'] > card['metrics']['baseline_prevalence']['test']['balanced_accuracy']
    # Kandidat belum aktif.
    assert get_model_status(tmp_path / 'cand')['status'] == 'MODEL_INVALID'

    active = tmp_path / 'active'
    approve_candidate('Peninjau Uji', 'uji kode', tmp_path / 'cand', active, tmp_path / 'arch')
    assert get_model_status(active)['status'] == 'MODEL_READY'

    z = zones[0]
    for k, v in {'salinity_ppt': 15.0, 'inundation_duration_h_day': 10.0, 'elevation_m': 1.0}.items():
        z['observations'][k]['value'] = v
    r = predict_zone(z, {'status': 'ELIGIBLE'}, active)
    assert r['status'] == 'OK' and r['additivity_ok'] and 0 <= r['score'] <= 1
    e = explain_zone(z, {'status': 'ELIGIBLE'}, active)
    assert e['status'] == 'OK' and [k for k, _ in e['factors']] and len(e['factors']) == 3
    assert abs(e['bias'] + sum(v for _, v in e['factors']) - e['margin']) < 1e-4
    if e['shap_check']['available'] and e['shap_check']['ok'] is not None:
        assert e['shap_check']['ok'], e['shap_check']

    # Persetujuan kedua mengarsipkan model lama.
    old_version = load_card(active)[0]['version']
    train_candidate(_make_csv(tmp_path / 'latih2.csv', seed=1), 'label', FEATURES, 'blok', tmp_path / 'cand')
    approve_candidate('Peninjau Uji', '', tmp_path / 'cand', active, tmp_path / 'arch')
    assert (tmp_path / 'arch' / old_version / 'model.ubj').exists()


def test_approval_rejects_no_better_than_baseline(tmp_path, xgb):
    card = train_candidate(_make_csv(tmp_path / 'latih.csv'), 'label', FEATURES, 'blok', tmp_path / 'cand')
    card['metrics']['test']['balanced_accuracy'] = 0.5
    (tmp_path / 'cand' / 'model_card.json').write_text(json.dumps(card))
    with pytest.raises(TrainingError, match='baseline'):
        approve_candidate('Peninjau', candidate_dir=tmp_path / 'cand', active_dir=tmp_path / 'active', archive_dir=tmp_path / 'arch')
    with pytest.raises(TrainingError, match='peninjau'):
        approve_candidate('  ', candidate_dir=tmp_path / 'cand', active_dir=tmp_path / 'active', archive_dir=tmp_path / 'arch')
