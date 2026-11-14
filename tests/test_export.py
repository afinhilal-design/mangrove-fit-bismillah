import json,csv,io
from copy import deepcopy
from mangrove_fit.report_service import export_csv,export_geojson,export_html,export_markdown
from mangrove_fit.services import analyse_zone
from mangrove_fit.data_io import parse_upload

def test_geojson_roundtrip(zones):
    raw=export_geojson([analyse_zone(z) for z in zones]);zs,_=parse_upload(raw,'r.geojson')
    assert zs==zones
    p=json.loads(raw)['features'][0]['properties']
    assert all(k in p for k in ('analysis_mode','data_quality','model_version','analysis_timestamp','watermark'))
    assert 'SIMULASI' in p['watermark']

def test_csv_roundtrip(zones):
    zs,_=parse_upload(export_csv([analyse_zone(z) for z in zones]),'r.csv')
    assert zs==zones

def test_formula_injection(zones):
    z=deepcopy(zones[0]);z['zone_name']='=HYPERLINK("bad")'
    rows=list(csv.DictReader(io.StringIO(export_csv([analyse_zone(z)]).decode('utf-8-sig'))))
    assert rows[0]['zone_name'].startswith("'=") and rows[0]['latitude'].startswith('-')

def test_html_escape(zones):
    z=deepcopy(zones[0]);z['zone_name']='<script>alert(1)</script>'
    out=export_html([analyse_zone(z)]).decode()
    assert '<script>' not in out and '&lt;script&gt;' in out

def test_report_has_metadata(zones):
    out=export_markdown([analyse_zone(zones[0])]).decode()
    assert 'SIMULASI' in out and 'RULE_BASED' in out and 'SYNTHETIC_DEMO' in out
