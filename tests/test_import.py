import json
import pytest
from mangrove_fit.data_io import parse_upload
from mangrove_fit.schemas import ValidationError
from mangrove_fit.config import ROOT

def test_csv_valid_and_empty_not_zero():
    zs,_=parse_upload((ROOT/'data/demo/titik_simulasi.csv').read_bytes(),'x.csv')
    assert len(zs)==3 and zs[0]['geometry']['coordinates']==(112.5,-6.9)
    assert zs[2]['observations']['salinity_ppt']['value'] is None
    assert zs[2]['observations']['mangrove_cover_pct']['value']==0

def test_latitude_120_rejected():
    with pytest.raises(ValidationError,match='latitude'):
        parse_upload(b'zone_id,zone_name,longitude,latitude\nA,A,112,120\n','x.csv')

@pytest.mark.parametrize('suffix',['.xlsx','.png','.pkl'])
def test_wrong_format(suffix):
    with pytest.raises(ValidationError): parse_upload(b'abc','x'+suffix)

def test_size_limit(monkeypatch):
    import mangrove_fit.data_io as io
    monkeypatch.setattr(io,'MAX_UPLOAD_BYTES',3)
    with pytest.raises(ValidationError,match='ukuran'): io.parse_upload(b'long','x.csv')

def test_duplicate_ids():
    with pytest.raises(ValidationError,match='duplikat'):
        parse_upload(b'zone_id,zone_name,longitude,latitude\nA,A,112,-6\nA,A,112,-6\n','x.csv')

def test_wrong_crs():
    d={'type':'FeatureCollection','crs':{'properties':{'name':'EPSG:3857'}},'features':[]}
    with pytest.raises(ValidationError,match='CRS'): parse_upload(json.dumps(d).encode(),'x.geojson')

def test_source_required():
    with pytest.raises(ValidationError,match='sumber'):
        parse_upload(b'zone_id,zone_name,longitude,latitude,salinity_ppt\nA,A,112,-6,22\n','x.csv')

@pytest.mark.parametrize('bad',['Infinity','false','[]'])
def test_bad_numeric(bad):
    raw=f'zone_id,zone_name,longitude,latitude,salinity_ppt\nA,A,112,-6,{bad}\n'.encode()
    with pytest.raises(ValidationError): parse_upload(raw,'x.csv')

def test_bad_date():
    raw=b'zone_id,zone_name,longitude,latitude,salinity_ppt,data_source,quality_flag,observation_date\nA,A,112,-6,22,test,measured,2026-02-30\n'
    with pytest.raises(ValidationError,match='Tanggal'): parse_upload(raw,'x.csv')

def test_datum_only_on_elevation(zones):
    assert zones[0]['observations']['elevation_m']['datum']
    assert zones[0]['observations']['salinity_ppt']['datum'] is None
