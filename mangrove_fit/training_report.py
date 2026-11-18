"""Export predictions and exact native TreeSHAP for a candidate, without activation."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from .training import TrainingError, _sha256, load_training_table, read_card


def export_candidate_report(candidate_dir) -> dict:
    import xgboost as xgb

    directory = Path(candidate_dir)
    card = read_card(directory)
    if not card or _sha256(directory / 'model.ubj') != card['sha256']:
        raise TrainingError('Kartu atau checksum kandidat tidak valid.')
    source = directory / 'training.csv'
    if _sha256(source) != card['training']['data_sha256']:
        raise TrainingError('Checksum tabel latih tidak cocok dengan kartu model.')
    features, target = card['features'], card['target']
    block = card['training']['block_column']
    frame, _ = load_training_table(source, target, features, block)
    booster = xgb.Booster()
    booster.load_model(str(directory / 'model.ubj'))
    dm = xgb.DMatrix(frame[features].to_numpy(float), feature_names=features)
    contributions = booster.predict(dm, pred_contribs=True, approx_contribs=False)
    margin = booster.predict(dm, output_margin=True)
    error = float(np.max(np.abs(contributions.sum(axis=1) - margin)))
    if not np.allclose(contributions.sum(axis=1), margin, atol=1e-5, rtol=1e-5):
        raise TrainingError('Uji aditivitas SHAP gagal.')
    memberships = {b: name for name, blocks in card['training']['blocks'].items() for b in blocks}
    result = frame[[block, target, *features]].copy()
    result.insert(0, 'source_csv_row', frame.index + 2)
    result['split'] = frame[block].map(memberships)
    result['probability'] = booster.predict(dm)
    result['margin_log_odds'] = margin
    result['bias_log_odds'] = contributions[:, -1]
    for i, feature in enumerate(features):
        result['shap_' + feature] = contributions[:, i]
    result.to_csv(directory / 'predictions_shap.csv', index=False)
    test = result['split'].eq('test').to_numpy()
    importance = pd.DataFrame({'feature': features,
                               'mean_abs_shap_test_log_odds': np.abs(contributions[test, :-1]).mean(axis=0)})
    importance = importance.sort_values('mean_abs_shap_test_log_odds', ascending=False)
    importance.to_csv(directory / 'shap_importance_test.csv', index=False)
    report = {'method': 'XGBoost exact TreeSHAP pred_contribs', 'space': 'log_odds',
              'additivity_ok': True, 'max_additivity_error': error,
              'model_sha256': card['sha256'], 'test_rows': int(test.sum()),
              'interpretation': 'Kontribusi terhadap prediksi model; bukan sebab-akibat atau keberhasilan rehabilitasi.'}
    (directory / 'shap_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
