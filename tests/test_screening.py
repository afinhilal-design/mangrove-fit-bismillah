from copy import deepcopy
import pytest
from mangrove_fit.services import analyse_zone
from mangrove_fit.screening import run_screening
from mangrove_fit.model_service import check_model_inputs

def test_demo_statuses(zones):
    assert [run_screening(z)['status'] for z in zones]==['ELIGIBLE','NEEDS_REVIEW','EXCLUDED']

def test_missing_salinity_never_eligible(zones):
    z=deepcopy(zones[0]);z['observations']['salinity_ppt']['value']=None;r=analyse_zone(z)
    assert r['screening']['status']=='NEEDS_REVIEW'
    assert r['recommendation']['action']=='Wajib verifikasi lapangan'
    assert r['model']['suitability_score'] is None

@pytest.mark.parametrize('land',['seagrass','coral_reef','open_water','built_area'])
def test_nonhabitat_excluded(zones,land):
    z=deepcopy(zones[0]);z['landcover_type']=land;r=analyse_zone(z)
    assert r['screening']['status']=='EXCLUDED'
    assert r['recommendation']['action']=='Tidak direkomendasikan untuk penanaman'

def test_prohibition_trumps_good_conditions(zones):
    z=deepcopy(zones[0]);z['legal_status']='dilarang'
    assert run_screening(z)['status']=='EXCLUDED'

def test_zero_salinity_is_not_missing(zones):
    z=deepcopy(zones[0]);z['observations']['salinity_ppt']['value']=0
    assert run_screening(z)['status']=='ELIGIBLE'

def test_no_fabricated_model(zones):
    for z in zones:
        r=analyse_zone(z)
        assert r['model']['status']=='NO_MODEL_AVAILABLE'
        assert r['model']['shap_factors'] is None and r['model']['version'] is None

def test_missing_features_guard(zones):
    assert check_model_inputs(zones[2],['salinity_ppt'])=={'status':'MISSING_REQUIRED_FEATURES','missing':['salinity_ppt']}

def test_estimated_core(zones):
    z=deepcopy(zones[0]);z['observations']['salinity_ppt']['quality_flag']='estimated'
    assert run_screening(z)['status']=='NEEDS_REVIEW'
