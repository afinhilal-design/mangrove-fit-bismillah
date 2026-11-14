import sqlite3
import json
from datetime import datetime, timezone
from .config import DB_PATH

def now(): return datetime.now(timezone.utc).isoformat()

def connect(path=None):
    path = path or DB_PATH
    from pathlib import Path
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def init_db(path=None):
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS zones (zone_id TEXT PRIMARY KEY, payload TEXT NOT NULL, scope TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS observations (zone_id TEXT REFERENCES zones(zone_id), parameter TEXT, value_json TEXT, metadata_json TEXT, PRIMARY KEY(zone_id, parameter));
        CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY, zone_id TEXT REFERENCES zones(zone_id), timestamp TEXT NOT NULL, result_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, analysis_id INTEGER REFERENCES analyses(id), reviewer TEXT NOT NULL, notes TEXT NOT NULL, decision TEXT NOT NULL, reviewed_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS datasets (id INTEGER PRIMARY KEY, name TEXT, checksum TEXT, date_imported TEXT, metadata_json TEXT);
        CREATE TABLE IF NOT EXISTS models (id INTEGER PRIMARY KEY, version TEXT, target TEXT, status TEXT, metadata_json TEXT);
        ''')

def save_zones(zones, scope='local', replace=False, path=None, dataset=None):
    if scope not in ('local','demo'): raise ValueError('Scope tidak sah.')
    ids = [z['zone_id'] for z in zones]
    if len(ids)!=len(set(ids)): raise ValueError('ID zona duplikat dalam berkas.')
    with connect(path) as db:
        for z in zones:
            current = db.execute('SELECT scope FROM zones WHERE zone_id=?',(z['zone_id'],)).fetchone()
            if current and (not replace or current['scope']!=scope):
                raise ValueError(f"ID {z['zone_id']} sudah ada. Gunakan ID baru atau aktifkan pembaruan data lokal.")
        for z in zones:
            stamp=now()
            db.execute('INSERT INTO zones VALUES (?,?,?,?,?) ON CONFLICT(zone_id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at',(z['zone_id'],json.dumps(z,ensure_ascii=False,allow_nan=False),scope,stamp,stamp))
            db.execute('DELETE FROM observations WHERE zone_id=?',(z['zone_id'],))
            for k,o in z['observations'].items():
                db.execute('INSERT INTO observations VALUES (?,?,?,?)',(z['zone_id'],k,json.dumps(o['value']),json.dumps(o,ensure_ascii=False)))
        if dataset:
            db.execute('INSERT INTO datasets(name,checksum,date_imported,metadata_json) VALUES (?,?,?,?)',(dataset['name'],dataset['checksum'],now(),json.dumps(dataset,ensure_ascii=False)))

def list_zones(scope='local', path=None):
    with connect(path) as db:
        return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM zones WHERE scope=? ORDER BY zone_id',(scope,))]

def save_analysis(result, path=None):
    with connect(path) as db:
        cur=db.execute('INSERT INTO analyses(zone_id,timestamp,result_json) VALUES (?,?,?)',(result['zone_id'],result['analysis_timestamp'],json.dumps(result,ensure_ascii=False,allow_nan=False)))
        return cur.lastrowid

def latest_analysis(zone_id,path=None):
    with connect(path) as db:
        row=db.execute('SELECT id,result_json FROM analyses WHERE zone_id=? ORDER BY id DESC LIMIT 1',(zone_id,)).fetchone()
        return {'id':row['id'],'result':json.loads(row['result_json'])} if row else None

def save_review(analysis_id,reviewer,notes,decision,path=None):
    if not reviewer.strip() or not notes.strip(): raise ValueError('Nama peninjau dan catatan wajib diisi.')
    with connect(path) as db:
        db.execute('INSERT INTO reviews(analysis_id,reviewer,notes,decision,reviewed_at) VALUES (?,?,?,?,?)',(analysis_id,reviewer.strip(),notes.strip(),decision,now()))

def get_reviews(zone_id,path=None):
    with connect(path) as db:
        return [dict(r) for r in db.execute('SELECT r.* FROM reviews r JOIN analyses a ON a.id=r.analysis_id WHERE a.zone_id=? ORDER BY r.id DESC',(zone_id,))]

def list_datasets(path=None):
    with connect(path) as db:
        return [dict(r) for r in db.execute('SELECT * FROM datasets ORDER BY id DESC')]
