"""Gerbang inferensi. Paket ini tidak berisi model, pickle loader, atau angka AI buatan."""

def get_model_status():
    return {'status':'NO_MODEL_AVAILABLE','version':None,'target':None,'suitability_score':None,'shap_factors':None,'message':'Model belum tersedia; penilaian berbasis aturan digunakan.'}

def check_model_inputs(zone, required_features):
    absent = [k for k in required_features if k not in zone['observations'] or zone['observations'][k]['value'] is None]
    return {'status':'MISSING_REQUIRED_FEATURES' if absent else 'INPUTS_AVAILABLE','missing':absent}
