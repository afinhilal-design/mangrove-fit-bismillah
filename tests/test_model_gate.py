"""Uji gerbang model. Model di sini dilatih pada data acak HANYA untuk menguji kode, bukan klaim ilmiah."""
import hashlib, json
import pytest
from mangrove_fit.model_service import get_model_status, predict_zone
from mangrove_fit.explain_service import explain_zone
from mangrove_fit.screening import run_screening

def test_no_card_means_no_model(tmp_path):
    assert get_model_status(tmp_path)['status']=='NO_MODEL_AVAILABLE'
    assert predict_zone({}, {'status':'ELIGIBLE'}, tmp_path)['status']=='NO_MODEL_AVAILABLE'

def test_unapproved_or_tampered_card_is_invalid(tmp_path):
    (tmp_path/'model_card.json').write_text(json.dumps({k:'x' for k in ('status','version','target','features','sha256','domain','output_space','approved_by')}))
    assert get_model_status(tmp_path)['status']=='MODEL_INVALID'

@pytest.fixture
def synthetic_model(tmp_path):
    xgb=pytest.importorskip('xgboost'); np=pytest.importorskip('numpy')
    rng=np.random.default_rng(0); X=rng.uniform(0,30,(200,2)); y=(X[:,0]>15).astype(int)
    b=xgb.train({'objective':'binary:logistic','max_depth':2},xgb.DMatrix(X,label=y,feature_names=['salinity_ppt','inundation_duration_h_day']),10)
    b.save_model(str(tmp_path/'model.ubj'))
    card={'status':'APPROVED','version':'uji-sintetis','target':'uji','features':['salinity_ppt','inundation_duration_h_day'],'sha256':hashlib.sha256((tmp_path/'model.ubj').read_bytes()).hexdigest(),'domain':{'salinity_ppt':[0,30],'inundation_duration_h_day':[0,30]},'output_space':'probability','approved_by':'uji'}
    (tmp_path/'model_card.json').write_text(json.dumps(card))
    return tmp_path

def _zone(zones, **vals):
    z=zones[0]
    for k,v in vals.items(): z['observations'][k]['value']=v
    return z

def test_prediction_and_additive_shap(zones, synthetic_model):
    z=_zone(zones, salinity_ppt=20.0, inundation_duration_h_day=8.0)
    scr={'status':'ELIGIBLE'}
    r=predict_zone(z,scr,synthetic_model)
    assert r['status']=='OK' and r['additivity_ok']
    e=explain_zone(z,scr,synthetic_model)
    assert e['status']=='OK' and len(e['factors'])==2

def test_gates(zones, synthetic_model):
    z=_zone(zones, salinity_ppt=20.0, inundation_duration_h_day=8.0)
    assert predict_zone(z,{'status':'EXCLUDED'},synthetic_model)['status']=='SCREENING_EXCLUDED'
    z['observations']['salinity_ppt']['value']=99.0
    assert predict_zone(z,{'status':'ELIGIBLE'},synthetic_model)['status']=='OUT_OF_DOMAIN'
    z['observations']['salinity_ppt']['value']=None
    assert predict_zone(z,{'status':'ELIGIBLE'},synthetic_model)['status']=='MISSING_REQUIRED_FEATURES'
