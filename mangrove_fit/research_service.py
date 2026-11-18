"""Read-only research inference; never approves models or writes zone observations."""
import hashlib
import json
import math

import numpy as np
import pandas as pd

from .config import ROOT

RESEARCH_ROOT = ROOT / 'models/experiments/all_data_v2'
MODELS = {
    'q4_survival_expanded': 'Survival Q4 · bulan 0 ke 16',
    'presence_expanded': 'Keberadaan semai alami',
    'q3_survival_conditional': 'Survival Q3 · bulan 3 ke 10',
    'q2_propagule_presence': 'Keberadaan propagul Q2',
}


class ResearchError(ValueError):
    pass


def predict_scenario_reference(zone):
    """Explain the matching historical record, never claim a forecast of current conditions."""
    from .scenario_service import load_scenario_zones
    mapping = {'ss_1-1': 'sea_1_1', 'ss_14-2': 'sea_14_2', 'pd_12-1': 'pond_12_1'}
    known = {z['zone_id']: z for z in load_scenario_zones()}
    if zone != known.get(zone.get('zone_id')):
        raise ResearchError('Zona tidak cocok dengan skenario sumber tervalidasi.')
    source_id = zone['provenance']['source_row_id']
    result = predict_research('presence_expanded', historical_id=mapping[source_id])
    result['scenario_reference'] = zone['zone_id']
    result['note'] = ('Demonstrasi baris historis yang sesuai dengan titik skenario; bukan prediksi kondisi 19 November 2026. '
                      'Fitur model berasal dari tabel riset lengkap, bukan pengisian parameter zona yang kosong. '
                      'Balanced accuracy validasi luar model ini 48,8%; belum layak untuk keputusan lapangan.')
    return result


def available_models():
    return [key for key in MODELS if (RESEARCH_ROOT / key / 'model_card.json').is_file()]


def load_research(key):
    if key not in MODELS:
        raise ResearchError('Model riset tidak dikenal.')
    directory = RESEARCH_ROOT / key
    try:
        card = json.loads((directory / 'model_card.json').read_text(encoding='utf-8'))
        encoder = json.loads((directory / 'encoder.json').read_text(encoding='utf-8'))
        for name, expected in [('model.ubj', card['sha256']), ('training.csv', card['data_sha256'])]:
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
                raise ResearchError(f'Checksum {name} tidak cocok. Pulihkan artefak riset asli.')
        if card['status'] != 'RESEARCH_ONLY' or card.get('synthetic'):
            raise ResearchError('Status atau provenance model riset tidak sesuai.')
        frame = pd.read_csv(directory / 'training.csv')
        features = encoder['numeric'] + encoder['categorical']
        sources = encoder['numeric'] + [c for c in encoder['categorical'] for _ in encoder['categories'][c]]
        if features != card['features'] or sources != encoder['source_features']:
            raise ResearchError('Skema encoder tidak cocok dengan model.')
        if encoder['encoded_names'] != [f'f{i}' for i in range(len(sources))]:
            raise ResearchError('Urutan fitur encoder tidak sesuai.')
        for feature in encoder['categorical']:
            if encoder['categories'][feature] != sorted(frame[feature].dropna().astype(str).unique()):
                raise ResearchError('Kategori encoder tidak cocok dengan data sumber.')
        return directory, card, encoder, frame
    except (OSError, KeyError, TypeError, json.JSONDecodeError, pd.errors.ParserError) as exc:
        raise ResearchError('Artefak riset belum lengkap atau rusak. Jalankan kembali pipeline riset.') from exc


def predict_research(key, inputs=None, historical_id=None):
    directory, card, encoder, frame = load_research(key)
    historical = historical_id is not None
    if historical:
        selected = frame[frame.row_id.astype(str).eq(str(historical_id))]
        if len(selected) != 1:
            raise ResearchError('Observasi historis tidak ditemukan atau ambigu.')
        inputs = selected.iloc[0][card['features']].to_dict()
    inputs = inputs or {}
    values, clean = [], {}
    for feature in encoder['numeric']:
        value = inputs.get(feature)
        if value is None or pd.isna(value):
            if not historical:
                raise ResearchError(f'Isi {feature}; nilai kosong tidak diisi otomatis.')
            value = np.nan
        else:
            if isinstance(value, (bool, str)) or not math.isfinite(float(value)):
                raise ResearchError(f'{feature} harus berupa angka terbatas.')
            value = float(value)
            bounds = pd.to_numeric(frame[feature], errors='raise')
            if not bounds.min() <= value <= bounds.max():
                raise ResearchError(f'{feature} di luar rentang data latih ({bounds.min():g}–{bounds.max():g}).')
        values.append(value)
        clean[feature] = None if pd.isna(value) else value
    for feature in encoder['categorical']:
        value = inputs.get(feature)
        if value not in encoder['categories'][feature]:
            raise ResearchError(f'Pilih kategori {feature} yang tersedia pada data latih.')
        clean[feature] = value
        values.extend(float(value == category) for category in encoder['categories'][feature])
    try:
        import xgboost as xgb
    except ImportError as exc:
        raise ResearchError('Paket XGBoost belum terpasang. Pasang requirements-ml.txt.') from exc
    try:
        model = xgb.Booster()
        model.load_model(str(directory / 'model.ubj'))
        if model.feature_names != encoder['encoded_names']:
            raise ResearchError('Urutan fitur pada model tidak cocok.')
        dm = xgb.DMatrix([values], feature_names=encoder['encoded_names'])
        probability = float(model.predict(dm)[0])
        margin = float(model.predict(dm, output_margin=True)[0])
        shap = model.predict(dm, pred_contribs=True, approx_contribs=False)[0]
    except xgb.core.XGBoostError as exc:
        raise ResearchError('Model tidak dapat dimuat atau dijalankan. Periksa akses berkas model dan versi XGBoost.') from exc
    if not np.isfinite(shap).all() or abs(float(shap.sum()) - margin) > 1e-4 or not 0 <= probability <= 1:
        raise ResearchError('Pemeriksaan prediksi atau aditivitas SHAP gagal.')
    parts = {f: float(sum(shap[i] for i, s in enumerate(encoder['source_features']) if s == f)) for f in card['features']}
    return {'status': 'RESEARCH_ONLY', 'model': key, 'target': card['description'],
            'watermark': 'RISET HISTORIS — BUKAN VALIDASI BARU' if historical else 'SIMULASI INPUT HIPOTETIS — BUKAN SURVEI',
            'historical_id': str(historical_id) if historical else None,
            'inputs': clean, 'probability': probability, 'threshold': card['final_threshold'],
            'prediction': int(probability >= card['final_threshold']), 'bias': float(shap[-1]),
            'margin': margin, 'contributions': parts, 'additivity_ok': True,
            'model_sha256': card['sha256'],
            'note': 'Skor belum dikalibrasi; bukan rekomendasi tanam. SHAP bukan sebab-akibat.'}
