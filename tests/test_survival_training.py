from pathlib import Path

import pandas as pd
import pytest

from mangrove_fit.config import ROOT
from mangrove_fit.survival_training import prepare_survival
from mangrove_fit.training import TrainingError


@pytest.fixture
def source():
    path = ROOT / 'datamangroveit/Q4_EMR-and-planting.csv'
    if not path.exists():
        pytest.skip('Dataset Q4 lokal tidak tersedia.')
    return path


def test_cohort_preserves_baseline_and_fixed_horizon(source, tmp_path):
    manifest = prepare_survival(source, tmp_path / 'out')
    table = pd.read_csv(tmp_path / 'out/training.csv')
    raw = pd.read_csv(source)
    assert 'J4' in manifest['ambiguous_ids_excluded']
    assert 'J4' not in set(table.seedling_id)
    assert table.seedling_id.is_unique
    initial = raw[raw.month.eq(0) & raw.ID.isin(table.seedling_id)].set_index('ID')
    final = raw[raw.month.eq(16) & raw.ID.isin(table.seedling_id)].set_index('ID')
    result = table.set_index('seedling_id')
    assert initial.survival.eq(1).all()
    pd.testing.assert_series_equal(result.sediment_level_cm.sort_index(), initial.sediment_raw.sort_index(), check_names=False)
    pd.testing.assert_series_equal(result.seedling_survival_16_month.sort_index(), final.survival.sort_index(), check_names=False)


def test_missing_baseline_is_not_backfilled(source, tmp_path):
    raw = pd.read_csv(source)
    selected = raw.loc[raw.month.eq(0) & raw.survival.eq(1) & raw.ID.ne('J4'), 'ID'].iloc[0]
    raw.loc[raw.month.eq(0) & raw.ID.eq(selected), 'sediment_raw'] = None
    edited = tmp_path / 'masked.csv'
    raw.to_csv(edited, index=False)
    prepare_survival(edited, tmp_path / 'out')
    result = pd.read_csv(tmp_path / 'out/training.csv').set_index('seedling_id')
    assert pd.isna(result.loc[selected, 'sediment_level_cm'])


def test_invalid_survival_is_rejected(source, tmp_path):
    raw = pd.read_csv(source)
    raw.loc[0, 'survival'] = 2
    edited = tmp_path / 'invalid.csv'
    raw.to_csv(edited, index=False)
    with pytest.raises(TrainingError, match='Survival'):
        prepare_survival(edited, tmp_path / 'out')
