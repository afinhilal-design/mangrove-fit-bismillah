import io
import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from mangrove_fit import database as db
from mangrove_fit.coastal_analysis import CANDIDATE, INSUFFICIENT, analyse_sheet
from mangrove_fit.coastal_sheets import (active_edition, auto_columns, clean_table, delete_sheet, load_sheet,
                                        read_table, saved_sheets, sheet_names, store_sheet)

ROOT = Path(__file__).resolve().parents[1]


def test_localised_csv_validation_without_filling_missing():
    raw = 'Desa;Kabupaten;NDVI;NDVI awal\nUtara;Pesisir;0,3;0,65\nBarat;Pesisir;0,72;0,7\nTimur;Pesisir;0,56;0,55\nKosong;Pesisir;keliru;2'.encode()
    table = read_table(raw, 'contoh.csv')
    clean, errors = clean_table(table, auto_columns(table))
    assert len(errors)==2
    result = analyse_sheet(clean).set_index('lokasi')
    assert result.loc['Utara','status'] == CANDIDATE
    assert result.loc['Utara','metode'] == 'K-Means'
    assert result.loc['Utara','urutan'] == 1
    assert result.loc['Kosong','status'] == INSUFFICIENT
    assert pd.isna(result.loc['Kosong','urutan'])
    with pytest.raises(ValueError, match='sel'):
        read_table(b'lokasi,ndvi\nA,0.3,other\n', 'x.csv')


def test_unequal_feature_sets_have_separate_ranks_and_degenerate_sample_is_honest():
    frame = pd.DataFrame([{'lokasi':'A','ndvi':0.6},{'lokasi':'B','ndvi':0.6},
                          {'lokasi':'C','ndvi':0.6},{'lokasi':'D','tutupan_pct':70}])
    results = analyse_sheet(frame)
    assert set(results.metode) == {'Indikator saja'}
    assert set(results[results.urutan==1].lokasi)=={'A','D'}
    assert CANDIDATE not in set(results.status)


def test_visits_keep_latest_date_and_observed_coordinate_pair():
    raw = b'lokasi,kabupaten,tanggal,NDVI,latitude,longitude\nA,K,2025-01-12,0.8,-7,111\nA,K,2026-01-12,0.4,-7.1,112\nA,K,2026-01-12,0.6,-7.2,113\n'
    src = read_table(raw, 'a.csv')
    clean, issues = clean_table(src, auto_columns(src))
    assert issues.empty
    r = analyse_sheet(clean).iloc[0]
    assert r.ndvi == 0.5 and r.ndvi_sebelumnya == 0.8 and r.tanggal == '2026-01-12'
    assert r.status == CANDIDATE and (r.latitude, r.longitude) == (-7.1, 112)


def test_excel_multiple_sheets_and_header(tmp_path):
    from openpyxl import Workbook
    buf = io.BytesIO()
    wb = Workbook()
    wb.active.title = 'Catatan'
    ws = wb.create_sheet('Survei')
    for line in [['Tabel survei'], ['Desa','Tutupan (%)'],['Contoh',35]]:
        ws.append(line)
    wb.save(buf)
    assert sheet_names(buf.getvalue(), 'survei.xlsx') == ['Catatan','Survei']
    src = read_table(buf.getvalue(), 'survei.xlsx', 'Survei', 2)
    assert auto_columns(src) == {'lokasi':'Desa','tutupan_pct':'Tutupan (%)'}


def test_json_geojson_parquet_and_word():
    from docx import Document
    f = {'type':'Feature', 'properties':{'lokasi':'Muara','ndvi':0.4},
         'geometry':{'type':'Point','coordinates':[112.8,-7.3]}}
    src = read_table(json.dumps({'type':'FeatureCollection','features':[f]}).encode(),'a.geojson')
    assert (src.longitude[0],src.latitude[0])==(112.8,-7.3)
    f['geometry']['coordinates']=[250,-7.3]
    with pytest.raises(ValueError, match='Geometri'):
        read_table(json.dumps({'type':'FeatureCollection','features':[f]}).encode(),'a.geojson')
    assert len(read_table(b'{"lokasi":"A"}\n{"lokasi":"B"}\n','a.jsonl'))==2
    buf=io.BytesIO()
    src.to_parquet(buf)
    assert read_table(buf.getvalue(),'a.parquet').equals(src)
    word=Document(); table=word.add_table(rows=2, cols=2)
    for cells, values in zip(table.rows, [('Lokasi','NDVI'),('Muara','0.4')]):
        for cell, value in zip(cells.cells, values):
            cell.text=value
    buf=io.BytesIO(); word.save(buf)
    assert read_table(buf.getvalue(),'tabel.docx','Tabel 1').iloc[0,0]=='Muara'


def test_storage_idempotence_and_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'site.db')
    db.init_db()
    data=b'lokasi,ndvi\na,0.4'
    src=read_table(data,'a.csv')
    mapping=auto_columns(src)
    clean,_=clean_table(src,mapping)
    first=store_sheet('A',data,'a.csv',None,mapping,1,clean)
    assert store_sheet('Diganti',data,'a.csv',None,mapping,1,clean)==first
    assert len(saved_sheets())==1 and saved_sheets()[0]['name']=='Diganti'
    assert load_sheet(first).iloc[0]['ndvi']==0.4
    assert db.list_zones('local')==[]
    delete_sheet(first)
    assert not saved_sheets()
    with pytest.raises(ValueError):
        load_sheet(first)


def test_real_snapshot_and_default_navigation(tmp_path, monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'atlas.db')
    base=pd.read_csv(active_edition()/'lokasi.csv')
    assert set(base.kabupaten_kota)=={'Sidoarjo','Kota Surabaya'}
    assert (base.piksel_valid<=base.piksel_acuan).all()
    valid=base[base.ndvi.notna()]
    assert (valid.piksel_valid>=20).all() and (valid.piksel_valid*2>=valid.piksel_acuan).all()
    assert set(valid.kabupaten_kota)==set(base.kabupaten_kota)
    at=AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
    assert not at.exception and at.selectbox(key='coast_source').value=='regional'
    at.selectbox(key='coast_region_regional').select('Sidoarjo').run()
    assert not at.exception
    at.switch_page('pages/9_Datasheet.py').run()
    assert not at.exception and any(t.label=='Impor file' for t in at.tabs)


def test_import_to_saved_result_through_app(tmp_path, monkeypatch):
    import streamlit as st
    monkeypatch.setattr(db, 'DB_PATH', tmp_path/'uploads.db')
    sample = io.BytesIO(b'Desa;Kabupaten;NDVI;NDVI sebelumnya\nMuara;Timur;0,30;0,65\nHilir;Timur;0,65;0,66\nHulu;Barat;0,8;0,78\n')
    sample.name = 'ujicoba.csv'
    monkeypatch.setattr(st, 'file_uploader', lambda *args, **kwargs: sample)
    app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
    app.switch_page('pages/9_Datasheet.py').run()
    assert not app.exception
    next(b for b in app.button if b.label=='Simpan dan buka hasil').click().run()
    assert not app.exception and app.selectbox(key='coast_source').value == saved_sheets()[0]['id']
    result = next(t.value for t in app.dataframe if 'Urutan' in t.value.columns)
    assert result.iloc[0]['Lokasi']=='Muara'
    assert result.iloc[0]['Tindak lanjut']==CANDIDATE


def test_synthetic_provenance_and_explicit_exclusions():
    src = read_table(b'Desa,ndvi,ndvi awal,legal_status,is_demo\nA,0.2,0.7,dilarang,true\nB,0.45,0.6,,true', 'a.csv')
    clean, _ = clean_table(src, auto_columns(src))
    result = analyse_sheet(clean).set_index('lokasi')
    assert result.is_demo.all() and result.loc['A', 'status'] == 'Dikecualikan'
    assert pd.isna(result.loc['A', 'urutan'])
    src.loc[0, 'is_demo'] = 'false'
    with pytest.raises(ValueError, match='Pisahkan'):
        clean_table(src, auto_columns(src))
