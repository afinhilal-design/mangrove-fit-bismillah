import sqlite3, gc
from copy import deepcopy
from mangrove_fit.database import init_db, save_zones, save_analysis, latest_analyses, reviews_for_analyses, save_review, latest_analysis, session
from mangrove_fit.services import analyse_zone
from mangrove_fit.config import load_rules

def test_batch_latest_matches_single(tmp_path, zones):
    p=tmp_path/'t.db'; init_db(p); save_zones(zones,path=p)
    for z in zones[:2]:
        save_analysis(analyse_zone(z),path=p); save_analysis(analyse_zone(z),path=p)
    batch=latest_analyses([z['zone_id'] for z in zones],path=p)
    assert set(batch)=={zones[0]['zone_id'],zones[1]['zone_id']}
    for zid,v in batch.items():
        assert v['id']==latest_analysis(zid,path=p)['id']
    save_review(batch[zones[0]['zone_id']]['id'],'A','n','Tunda intervensi',path=p)
    rv=reviews_for_analyses([v['id'] for v in batch.values()],path=p)
    assert len(rv[batch[zones[0]['zone_id']]['id']])==1

def test_session_closes_connection(tmp_path):
    p=tmp_path/'t.db'; init_db(p)
    with session(p) as db: pass
    try: db.execute('SELECT 1'); closed=False
    except sqlite3.ProgrammingError: closed=True
    assert closed

def test_session_rolls_back(tmp_path):
    p=tmp_path/'t.db'; init_db(p)
    try:
        with session(p) as db:
            db.execute("INSERT INTO datasets(name) VALUES ('x')"); raise RuntimeError
    except RuntimeError: pass
    with session(p) as db: assert db.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]==0

def test_rules_cached_and_stable():
    assert load_rules() is load_rules() and len(load_rules()['checksum'])==64
