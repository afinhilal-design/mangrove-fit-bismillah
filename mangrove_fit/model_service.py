"""Gerbang inferensi, hanya aktif bila ada artefak model yang disetujui.

Tanpa `models/active/model_card.json`, perilaku sama seperti MVP 0.1: NO_MODEL_AVAILABLE.
Paket ini tidak berisi model, data latih, pickle/joblib loader, atau angka AI buatan.

Kontrak artefak (lihat models/README.md):
  models/active/model.ubj          model XGBoost format native (bukan pickle)
  models/active/model_card.json    status=APPROVED, version, target, features, sha256,
                                   domain {fitur:[min,maks]}, output_space, approved_by

Penjelasan memakai kontribusi TreeSHAP bawaan XGBoost (`pred_contribs`), yaitu algoritma
yang sama dengan SHAP TreeExplainer, dalam ruang margin/log-odds. Tidak ada dependensi `shap`.
"""
import hashlib
import json
from .config import MODEL_DIR

CARD_FIELDS = ('status', 'version', 'target', 'features', 'sha256', 'domain', 'output_space', 'approved_by')
NO_MODEL = {'status':'NO_MODEL_AVAILABLE','version':None,'target':None,'suitability_score':None,'shap_factors':None,'message':'Model belum tersedia; penilaian berbasis aturan digunakan.'}

def _unavailable(status, message):
    return {**NO_MODEL, 'status': status, 'message': message}

def load_card(model_dir=None):
    """Kembalikan (card, error). (None, None) bila tidak ada kartu model sama sekali."""
    d = model_dir or MODEL_DIR
    card_path = d / 'model_card.json'
    if not card_path.exists():
        return None, None
    try:
        card = json.loads(card_path.read_text(encoding='utf-8'))
    except ValueError:
        return None, 'model_card.json bukan JSON sah.'
    absent = [k for k in CARD_FIELDS if k not in card]
    if absent:
        return None, 'model_card.json tidak lengkap: ' + ', '.join(absent) + '.'
    if card.get('synthetic'):
        return None, 'Model dilatih dari data sintetis; hanya untuk uji kode dan tidak boleh diaktifkan.'
    if card['status'] != 'APPROVED':
        return None, 'Model belum berstatus APPROVED oleh peninjau ahli.'
    if not card['approved_by']:
        return None, 'Nama peninjau (approved_by) kosong.'
    if not isinstance(card['features'], list) or not card['features']:
        return None, 'Daftar fitur model kosong.'
    if card['output_space'] not in ('probability', 'raw'):
        return None, 'output_space harus probability atau raw.'
    weights = d / 'model.ubj'
    if not weights.exists():
        return None, 'model.ubj tidak ditemukan.'
    if hashlib.sha256(weights.read_bytes()).hexdigest() != card['sha256']:
        return None, 'Checksum model.ubj tidak cocok dengan model_card.json.'
    return card, None

def get_model_status(model_dir=None):
    card, error = load_card(model_dir)
    if error:
        return _unavailable('MODEL_INVALID', error)
    if card is None:
        return dict(NO_MODEL)
    return {'status':'MODEL_READY','version':card['version'],'target':card['target'],'suitability_score':None,'shap_factors':None,'message':'Model terpasang. Skor dihitung per zona oleh predict_zone setelah pemeriksaan screening, fitur, dan domain.'}

def check_model_inputs(zone, required_features):
    absent = [k for k in required_features if k not in zone['observations'] or zone['observations'][k]['value'] is None]
    return {'status':'MISSING_REQUIRED_FEATURES' if absent else 'INPUTS_AVAILABLE','missing':absent}

def _load_booster(model_dir):
    import xgboost as xgb  # impor malas: tidak wajib untuk MVP
    booster = xgb.Booster()
    booster.load_model(str((model_dir or MODEL_DIR) / 'model.ubj'))
    return xgb, booster

def predict_zone(zone, screening, model_dir=None):
    """Skor + kontribusi per fitur, hanya bila semua gerbang keselamatan lolos."""
    status = get_model_status(model_dir)
    if status['status'] != 'MODEL_READY':
        return {'status': status['status'], 'message': status['message']}
    if screening['status'] == 'EXCLUDED':
        return {'status':'SCREENING_EXCLUDED','message':'Zona dikecualikan oleh screening; model tidak dijalankan.'}
    card, _ = load_card(model_dir)
    features = card['features']
    check = check_model_inputs(zone, features)
    if check['status'] != 'INPUTS_AVAILABLE':
        return {'status':'MISSING_REQUIRED_FEATURES','missing':check['missing'],'message':'Fitur wajib model belum lengkap; tidak ada imputasi.'}
    row = {k: zone['observations'][k]['value'] for k in features}
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in row.values()):
        return {'status':'MODEL_INVALID','message':'Fitur kategorik belum didukung adapter; gunakan fitur numerik.'}
    outside = [k for k, v in row.items() if k in card['domain'] and not card['domain'][k][0] <= v <= card['domain'][k][1]]
    if outside:
        return {'status':'OUT_OF_DOMAIN','outside':outside,'message':'Nilai berada di luar domain data latih; prediksi tidak diberikan.'}
    try:
        xgb, booster = _load_booster(model_dir)
    except ImportError:
        return {'status':'MODEL_INVALID','message':'Paket xgboost belum terpasang (pip install -r requirements-ml.txt).'}
    dm = xgb.DMatrix([[row[k] for k in features]], feature_names=features)
    margin = float(booster.predict(dm, output_margin=True)[0])
    contrib = booster.predict(dm, pred_contribs=True)[0]
    parts = {k: float(v) for k, v in zip(features, contrib[:-1])}
    bias = float(contrib[-1])
    additive = abs(sum(parts.values()) + bias - margin) < 1e-4
    score = float(booster.predict(dm)[0]) if card['output_space'] == 'probability' else margin
    return {'status':'OK','version':card['version'],'target':card['target'],'output_space':card['output_space'],'score':score,'margin':margin,'inputs':row,'contributions':parts,'bias':bias,'additivity_ok':additive,'message':'Skor model bukan persen keberhasilan tanam; kontribusi bukan bukti sebab-akibat.'}
