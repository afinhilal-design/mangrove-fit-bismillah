"""Offline mixed-feature XGBoost with nested group validation and out-of-fold SHAP.

Research artifacts deliberately cannot pass the application model approval gate.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold

from .training import classification_metrics, _sha256

GRID = [{'max_depth': depth, 'rounds': rounds} for depth in (2, 3) for rounds in (40, 100)]


class FeatureEncoder:
    def __init__(self, numeric, categorical):
        self.numeric, self.categorical = list(numeric), list(categorical)

    def fit(self, frame):
        self.categories = {c: sorted(frame[c].dropna().astype(str).unique()) for c in self.categorical}
        self.sources = self.numeric + [c for c, values in self.categories.items() for _ in values]
        self.names = [f'f{i}' for i in range(len(self.sources))]
        if not self.names:
            raise ValueError('Tidak ada fitur yang bisa digunakan.')
        return self

    def transform(self, frame):
        cols = [pd.to_numeric(frame[c], errors='raise').to_numpy(float) for c in self.numeric]
        for c, values in self.categories.items():
            for v in values:
                # Missing categorical measurements remain NaN, never silently imputed.
                cols.append(frame[c].astype(str).eq(v).astype(float).where(frame[c].notna()).to_numpy())
        result = np.column_stack(cols)
        if np.isinf(result).any():
            raise ValueError('Fitur mengandung infinity.')
        return result

    def manifest(self):
        return {'numeric': self.numeric, 'categorical': self.categorical,
                'categories': self.categories, 'encoded_names': self.names, 'source_features': self.sources,
                'missing_policy': 'NaN native XGBoost, tanpa imputasi; kategori tak dikenal menjadi all-zero indikator.'}


def fit_model(frame, numeric, categorical, config):
    enc = FeatureEncoder(numeric, categorical).fit(frame)
    dm = xgb.DMatrix(enc.transform(frame), label=frame.target.to_numpy(int), feature_names=enc.names)
    params = {'objective': 'binary:logistic', 'eval_metric': 'logloss', 'eta': 0.05,
              'max_depth': config['max_depth'], 'min_child_weight': 3, 'lambda': 5,
              'subsample': 1, 'colsample_bytree': 1, 'seed': 42, 'nthread': 2}
    model = xgb.train(params, dm, num_boost_round=config['rounds'])
    return model, enc


def predict(model, enc, frame):
    dm = xgb.DMatrix(enc.transform(frame), feature_names=enc.names)
    return model.predict(dm)


def folds(frame, maximum):
    n = min(maximum, frame.group.nunique())
    if n < 2:
        raise ValueError('Minimal dua grup untuk validasi.')
    return list(GroupKFold(n_splits=n).split(frame, frame.target, frame.group))


def select_config(frame, numeric, categorical):
    splits = folds(frame, 3)
    choices = []
    for config in GRID:
        prob = np.full(len(frame), np.nan)
        for train, valid in splits:
            tr, va = frame.iloc[train], frame.iloc[valid]
            if tr.target.nunique() < 2:
                prob[valid] = tr.target.mean()
            else:
                model, enc = fit_model(tr, numeric, categorical, config)
                prob[valid] = predict(model, enc, va)
        score = classification_metrics(frame.target, prob)
        choices.append((score['pr_auc'] if score['pr_auc'] is not None else -1, config, prob))
    _, config, prob = max(choices, key=lambda item: item[0])
    thresholds = [0.5, 0.4, 0.3, 0.2, 0.6]
    threshold = max(thresholds, key=lambda t: classification_metrics(frame.target, prob, t)['balanced_accuracy'] or 0)
    return config, threshold


def train_research(frame, numeric, categorical, baseline_features, description, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=False)
    features = list(numeric) + list(categorical)
    if set(features) & {'target', 'group', 'row_id'} or len(features) != len(set(features)):
        raise ValueError('Skema fitur berisi label, identitas, atau duplikat.')
    if not frame.target.dropna().isin([0, 1]).all():
        raise ValueError('Target riset harus biner.')
    if frame[['group', 'row_id']].isna().any().any() or frame.row_id.duplicated().any():
        raise ValueError('Identitas baris/grup kosong atau ganda.')
    input_rows = len(frame)
    frame = frame.dropna(subset=['target']).copy().reset_index(drop=True)
    frame['group'] = frame.group.astype(str)
    if frame.group.nunique() < 3 or frame.target.nunique() < 2:
        raise ValueError('Minimal tiga grup dan dua kelas diperlukan.')
    frame[['row_id', 'group', 'target', *features]].to_csv(out / 'training.csv', index=False)
    records, shap_records, fold_cards = [], [], []
    for fold, (train, test) in enumerate(folds(frame, 4)):
        tr, te = frame.iloc[train], frame.iloc[test]
        if tr.target.nunique() < 2:
            raise ValueError('Training outer fold hanya satu kelas; eksperimen ditolak.')
        config, threshold = select_config(tr, numeric, categorical)
        model, enc = fit_model(tr, numeric, categorical, config)
        dm = xgb.DMatrix(enc.transform(te), feature_names=enc.names)
        prob = model.predict(dm)
        shap = model.predict(dm, pred_contribs=True, approx_contribs=False)
        margin = model.predict(dm, output_margin=True)
        error = float(np.max(np.abs(shap.sum(axis=1) - margin)))
        if not np.allclose(shap.sum(axis=1), margin, atol=1e-5, rtol=1e-5):
            raise ValueError('Aditivitas SHAP gagal.')
        baseline_prob = np.full(len(te), tr.target.mean())
        simple_prob = None
        if baseline_features:
            simple, simple_enc = fit_model(tr, baseline_features, [], {'max_depth': 3, 'rounds': 100})
            simple_prob = predict(simple, simple_enc, te)
        rows = te[['row_id', 'group', 'target']].copy()
        rows['fold'], rows['probability'], rows['threshold'] = fold, prob, threshold
        rows['prediction_tuned'] = (prob >= threshold).astype(int)
        rows['baseline_probability'] = baseline_prob
        if simple_prob is not None:
            rows['simple_model_probability'] = simple_prob
        records.append(rows)
        contributions = te[['row_id', 'group']].copy()
        contributions['fold'], contributions['bias'], contributions['margin'] = fold, shap[:, -1], margin
        for feature in features:
            indices = [i for i, c in enumerate(enc.sources) if c == feature]
            contributions['shap_' + feature] = shap[:, indices].sum(axis=1)
        shap_records.append(contributions)
        fold_cards.append({'fold': fold, 'train_groups': sorted(tr.group.unique()), 'test_groups': sorted(te.group.unique()),
                           'config': config, 'threshold_from_inner_cv': threshold, 'shap_max_error': error,
                           'metrics': classification_metrics(te.target, prob, threshold)})
    oof = pd.concat(records).sort_index()
    explanations = pd.concat(shap_records).sort_index()
    oof.to_csv(out / 'oof_predictions.csv', index=False)
    explanations.to_csv(out / 'oof_shap.csv', index=False)
    importance = pd.DataFrame({'feature': features,
        'mean_abs_oof_shap_log_odds': [explanations['shap_' + f].abs().mean() for f in features]})
    importance.sort_values('mean_abs_oof_shap_log_odds', ascending=False).to_csv(out / 'shap_importance.csv', index=False)
    metrics = {'nested_oof_threshold_05': classification_metrics(oof.target, oof.probability),
               'baseline_prevalence': classification_metrics(oof.target, oof.baseline_probability)}
    # Classification metrics at fold-specific thresholds; probabilistic metrics remain original.
    tuned = classification_metrics(oof.target, oof.prediction_tuned)
    for key in ('pr_auc', 'brier', 'prevalence'):
        tuned[key] = metrics['nested_oof_threshold_05'][key]
    tuned['threshold'] = 'selected_in_each_inner_cv'
    metrics['nested_oof_tuned_threshold'] = tuned
    if baseline_features:
        metrics['simple_features_same_outer_folds'] = classification_metrics(oof.target, oof.simple_model_probability)
    config, threshold = select_config(frame, numeric, categorical)
    final, enc = fit_model(frame, numeric, categorical, config)
    final.save_model(str(out / 'model.ubj'))
    (out / 'encoder.json').write_text(json.dumps(enc.manifest(), indent=2, ensure_ascii=False), encoding='utf-8')
    card = {'status': 'RESEARCH_ONLY', 'description': description, 'target': 'target',
            'features': features, 'synthetic': False, 'approved_by': None,
            'rows': len(frame), 'missing_labels_excluded': input_rows - len(frame), 'groups': int(frame.group.nunique()),
            'missing_features': frame[features].isna().sum().astype(int).to_dict(),
            'sha256': _sha256(out / 'model.ubj'), 'data_sha256': _sha256(out / 'training.csv'),
            'xgboost_version': xgb.__version__, 'final_config': config, 'final_threshold': threshold,
            'validation': 'Nested GroupKFold: outer<=4, inner<=3; four fixed configurations; encoder fit on training fold only.',
            'folds': fold_cards, 'metrics': metrics,
            'limitations': ['Exploratory re-analysis of previously inspected data, not an untouched external test.',
                            'OOF SHAP explains different fold models; final all-data model has no new independent evaluation.',
                            'Not approved for application inference; no calendar or location reassignment.',
                            'Grouping does not prove independence of nearby physical sites.']}
    (out / 'model_card.json').write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding='utf-8')
    return card
