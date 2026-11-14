import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mangrove_fit.data_io import parse_upload
from mangrove_fit.config import ROOT
@pytest.fixture
def zones():
    return parse_upload((ROOT/'data/demo/zona_simulasi.geojson').read_bytes(),'demo.geojson')[0]
