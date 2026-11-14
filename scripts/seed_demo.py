from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mangrove_fit.database import init_db, list_zones, save_zones
from mangrove_fit.data_io import parse_upload
from mangrove_fit.config import ROOT

def seed(path=None):
    init_db(path)
    if not list_zones('demo',path):
        zones,_=parse_upload((ROOT/'data/demo/zona_simulasi.geojson').read_bytes(),'demo.geojson')
        save_zones(zones,scope='demo',path=path)
if __name__=='__main__':
    seed()
    print('Tiga zona SINTETIS tersedia. Data lokal tidak diubah.')
