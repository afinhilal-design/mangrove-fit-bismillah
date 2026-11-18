"""Penjelasan SHAP untuk prediksi XGBoost.

Sumber utama: TreeSHAP bawaan XGBoost (`pred_contribs`) — algoritma yang sama dengan
`shap.TreeExplainer`, dalam ruang margin (log-odds). Bila paket `shap` terpasang, nilai yang
sama dihitung ulang dengan `shap.TreeExplainer` sebagai pemeriksaan konsistensi; bila berbeda,
penjelasan ditahan.
"""
from .config import MODEL_DIR
from .model_service import predict_zone

SHAP_TOLERANCE = 1e-3


def explain_unavailable():
    return {'status':'NO_MODEL_AVAILABLE','factors':None,'message':'SHAP hanya tersedia setelah model XGBoost tervalidasi terhubung. Alasan screening bukan nilai SHAP.'}


def shap_library_check(pred, model_dir=None):
    """Bandingkan pred_contribs dengan shap.TreeExplainer. Tidak wajib: bila `shap` tidak ada, dilewati."""
    try:
        import shap
    except ModuleNotFoundError:
        return {'available': False, 'ok': None, 'message': 'Paket shap tidak terpasang; hanya TreeSHAP bawaan XGBoost yang dipakai.'}
    except ImportError:  # mis. DLL scikit-learn diblokir kebijakan Windows
        return {'available': False, 'ok': None, 'message': 'Paket shap terpasang tetapi gagal dimuat di sistem ini; hanya TreeSHAP bawaan XGBoost yang dipakai.'}
    try:
        import numpy as np
        import xgboost as xgb
        booster = xgb.Booster()
        booster.load_model(str((model_dir or MODEL_DIR) / 'model.ubj'))
        features = list(pred['contributions'])
        row = np.array([[pred['inputs'][k] for k in features]], dtype=float)
        values = shap.TreeExplainer(booster).shap_values(row)
        values = np.asarray(values[1] if isinstance(values, list) else values).reshape(-1)
        diff = float(max(abs(values[i] - pred['contributions'][k]) for i, k in enumerate(features)))
        return {'available': True, 'ok': diff <= SHAP_TOLERANCE, 'max_abs_diff': diff, 'shap_version': shap.__version__,
                'message': 'Nilai shap.TreeExplainer konsisten dengan TreeSHAP XGBoost.' if diff <= SHAP_TOLERANCE else 'Nilai shap.TreeExplainer berbeda dari TreeSHAP XGBoost.'}
    except Exception as exc:  # versi shap/xgboost tidak cocok, dll.
        return {'available': True, 'ok': None, 'message': f'Pemeriksaan shap gagal dijalankan: {type(exc).__name__}.'}


def explain_zone(zone, screening, model_dir=None, cross_check=True):
    """Kontribusi TreeSHAP per fitur (ruang margin/log-odds), diurutkan menurut besar pengaruh."""
    pred = predict_zone(zone, screening, model_dir)
    if pred['status'] != 'OK':
        return {**explain_unavailable(), **{k: v for k, v in pred.items() if k in ('missing', 'outside')}, 'status': pred['status'], 'message': pred['message']}
    if not pred['additivity_ok']:
        return {'status':'EXPLANATION_INVALID','factors':None,'message':'Kontribusi tidak aditif terhadap output model; penjelasan ditahan.'}
    check = shap_library_check(pred, model_dir) if cross_check else {'available': False, 'ok': None, 'message': 'Pemeriksaan shap dilewati.'}
    if check['ok'] is False:
        return {'status':'EXPLANATION_INVALID','factors':None,'shap_check':check,'message':check['message']+' Penjelasan ditahan.'}
    factors = sorted(pred['contributions'].items(), key=lambda kv: -abs(kv[1]))
    return {'status':'OK','factors':factors,'bias':pred['bias'],'margin':pred['margin'],'score':pred['score'],'inputs':pred['inputs'],
            'space':'margin (log-odds)','shap_check':check,'version':pred['version'],'message':pred['message']}
