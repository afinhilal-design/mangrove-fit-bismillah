from copy import deepcopy
import pytest
from mangrove_fit.database import init_db,save_zones,list_zones,save_analysis,latest_analysis,save_review,get_reviews
from mangrove_fit.services import analyse_zone

def test_atomic_import(tmp_path,zones):
    p=tmp_path/'t.db';init_db(p);save_zones([zones[0]],path=p)
    with pytest.raises(ValueError): save_zones([zones[1],zones[0]],path=p)
    assert len(list_zones(path=p))==1

def test_restart_snapshot_null_and_review(tmp_path,zones):
    p=tmp_path/'t.db';init_db(p);save_zones(zones,path=p)
    r=analyse_zone(zones[2]);aid=save_analysis(r,path=p)
    z=deepcopy(zones[2]);z['zone_name']='Edited';save_zones([z],replace=True,path=p);init_db(p)
    assert list_zones(path=p)[2]['zone_name']=='Edited'
    assert latest_analysis(z['zone_id'],path=p)['result']['feature_snapshot']['zone_name']!=z['zone_name']
    assert list_zones(path=p)[2]['observations']['salinity_ppt']['value'] is None
    save_review(aid,'Ahli','Survei ulang','Tunda intervensi',path=p)
    assert get_reviews(z['zone_id'],path=p)[0]['analysis_id']==aid

def test_cannot_overwrite_demo(tmp_path,zones):
    p=tmp_path/'t.db';init_db(p);save_zones(zones,scope='demo',path=p)
    with pytest.raises(ValueError): save_zones(zones,scope='local',replace=True,path=p)
