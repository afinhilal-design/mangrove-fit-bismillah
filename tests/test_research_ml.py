import json

import numpy as np
import pandas as pd
import pytest

pytest.importorskip('xgboost')
pytest.importorskip('sklearn')
from sklearn.metrics import balanced_accuracy_score, average_precision_score

from mangrove_fit.config import ROOT
from mangrove_fit.research_ml import FeatureEncoder, folds
from mangrove_fit.research_datasets import coordinate_groups, build_tasks
from mangrove_fit.training import approval_blockers


@pytest.fixture
def tasks(tmp_path):
    if not (ROOT / 'datamangroveit/Q4_EMR-and-planting.csv').exists():
        pytest.skip('Data historis lokal belum tersedia.')
    return build_tasks(ROOT / 'datamangroveit', tmp_path)


def test_encoder_preserves_missing_and_learns_categories_only_on_train(tasks):
    q4 = tasks['q4_survival_expanded'][0]
    species = q4.species.iloc[0]
    train = q4[q4.species.eq(species)]
    heldout = q4[~q4.species.eq(species)].head(1).copy()
    enc = FeatureEncoder(['length'], ['species']).fit(train)
    assert enc.categories == {'species': [species]}
    assert enc.transform(heldout)[0, 1] == 0
    heldout['length'], heldout['species'] = np.nan, None
    assert np.isnan(enc.transform(heldout)).all()


def test_nested_groups_are_disjoint(tasks):
    for frame, *_ in tasks.values():
        frame = frame.dropna(subset=['target'])
        for train, test in folds(frame, 4):
            tr, te = frame.iloc[train], frame.iloc[test]
            assert set(tr.group).isdisjoint(te.group)
            for inner_train, inner_valid in folds(tr, 3):
                assert set(tr.iloc[inner_train].group).isdisjoint(tr.iloc[inner_valid].group)
                assert set(tr.iloc[inner_train].group).isdisjoint(te.group)


def test_shared_coordinates_never_cross_groups(tasks):
    presence = tasks['presence_expanded'][0]
    assert presence.groupby(['lat', 'lon']).group.nunique().max() == 1
    assert presence.groupby('transect').group.nunique().max() == 1


def test_outcome_columns_are_not_features_and_horizons_are_fixed(tasks):
    for frame, numeric, categorical, _, _ in tasks.values():
        assert not set(numeric + categorical) & {'target', 'survival', 'SeedlingDen', 'prop_count', 'growth', 'growth_corr'}
        assert frame.row_id.is_unique
    q4 = tasks['q4_survival_expanded'][0]
    assert q4.baseline_month.eq(0).all() and q4.target_month.eq(16).all()
    raw = pd.read_csv(ROOT / 'datamangroveit/Q4_EMR-and-planting.csv')
    baseline = raw[raw.month.eq(0) & raw.ID.isin(q4.row_id)].set_index('ID')
    assert baseline.survival.eq(1).all()
    pd.testing.assert_series_equal(q4.set_index('row_id').length.sort_index(), baseline.length.sort_index(), check_names=False)
    q3 = tasks['q3_survival_conditional'][0]
    original = pd.read_csv(ROOT / 'datamangroveit/Q3_EMR-dams_seedling_survival_exp.csv')
    expected = original[original.month.eq(10)].set_index('ID').survival
    assert np.array_equal(q3.target.to_numpy(), expected.loc[q3.row_id].to_numpy())


def test_saved_oof_results_and_shap_reconcile():
    directory = ROOT / 'models/experiments/all_data_v2'
    if not (directory / 'summary.json').exists():
        pytest.skip('Artefak riset lokal tidak tersedia.')
    for path in directory.glob('*/model_card.json'):
        card = json.loads(path.read_text(encoding='utf-8'))
        pred = pd.read_csv(path.parent / 'oof_predictions.csv')
        shap = pd.read_csv(path.parent / 'oof_shap.csv')
        assert pred.row_id.is_unique and len(pred) == card['rows']
        assert round(balanced_accuracy_score(pred.target, pred.prediction_tuned), 4) == card['metrics']['nested_oof_tuned_threshold']['balanced_accuracy']
        assert round(average_precision_score(pred.target, pred.probability), 4) == card['metrics']['nested_oof_threshold_05']['pr_auc']
        assert np.allclose(shap.bias + shap.filter(like='shap_').sum(axis=1), shap.margin, atol=1e-5)
        assert approval_blockers(card, path.parent)


def test_all_supplied_files_have_audit_and_unchanged_hash():
    import hashlib
    path = ROOT / 'models/experiments/all_data_v2/audit/source_audit.json'
    if not path.exists():
        pytest.skip('Audit lokal tidak tersedia.')
    audit = json.loads(path.read_text(encoding='utf-8'))
    actual = {p.name: p for p in (ROOT / 'datamangroveit').iterdir() if p.is_file()}
    assert {r['file'] for r in audit} == set(actual)
    for row in audit:
        assert row['sha256'] == hashlib.sha256(actual[row['file']].read_bytes()).hexdigest()
        assert row['tables'] and row['reason']
