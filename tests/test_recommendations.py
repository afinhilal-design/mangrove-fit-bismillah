from copy import deepcopy
from mangrove_fit.services import analyse_zone
from mangrove_fit.prioritization import survey_sort

def test_regeneration_over_planting(zones):
    assert analyse_zone(zones[0])['recommendation']['action']=='Fasilitasi regenerasi alami'

def test_existing_mangrove(zones):
    z=deepcopy(zones[0]);z['landcover_type']='mangrove'
    assert analyse_zone(z)['recommendation']['action']=='Lindungi dan pantau'

def test_hydrology_review(zones):
    r=analyse_zone(zones[1])
    assert r['recommendation']['action']=='Wajib verifikasi lapangan'
    assert 'hidrologi' in r['recommendation']['focus']

def test_survey_order(zones):
    rs=survey_sort([analyse_zone(z) for z in zones])
    assert [r['zone_id'] for r in rs]==['SIM-B','SIM-A','SIM-C']
