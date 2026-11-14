from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def app(tmp_path,monkeypatch):
    import mangrove_fit.database as db
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'ui.db')
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not at.exception
    return at
@pytest.mark.parametrize('page',['2_Peta.py','3_Analisis.py','4_Perbandingan.py','5_Data_Model.py','6_Metodologi.py'])
def test_pages(app,page):
    app.switch_page('pages/'+page).run();assert not app.exception

def test_zone_switch(app):
    app.switch_page('pages/3_Analisis.py').run()
    app.selectbox(key='analysis_zone_demo').select('SIM-C').run()
    assert not app.exception and any('Tidak memenuhi' in x.value for x in app.subheader)
    assert any('NO_MODEL_AVAILABLE' in x.value for x in app.info)
    app.selectbox(key='analysis_zone_demo').select('SIM-A').run()
    assert any('Fasilitasi regenerasi alami' in x.value for x in app.subheader)

def test_offline_local_empty(app):
    app.switch_page('pages/2_Peta.py').run();app.toggle[0].set_value(True).run()
    assert not app.exception and any('TANPA BASEMAP' in x.value for x in app.markdown)
    app.radio(key='workspace_mode').set_value('Analis lokal').run()
    assert not app.exception and any('Belum ada zona' in x.value for x in app.info)

def test_clearing_zone_does_not_crash(app):
    app.switch_page('pages/3_Analisis.py').run()
    app.selectbox(key='analysis_zone_demo').set_value(None).run()
    assert not app.exception

def test_create_local_zone_save_and_review(app):
    app.radio(key='workspace_mode').set_value('Analis lokal').run()
    app.switch_page('pages/5_Data_Model.py').run()
    assert not app.exception
    next(x for x in app.text_input if x.label=='ID zona').set_value('QA-001')
    next(x for x in app.text_input if x.label=='Nama zona').set_value('Zona uji aplikasi')
    next(x for x in app.button if x.label=='Simpan zona').click().run()
    assert not app.exception
    assert any('Zona tersimpan' in x.value for x in app.success)
    app.switch_page('pages/3_Analisis.py').run()
    assert any('Perlu verifikasi' in x.value for x in app.subheader)
    next(x for x in app.button if x.label=='Simpan analisis saat ini').click().run()
    assert not app.exception
    next(x for x in app.text_input if x.label=='Nama verifikator / ahli').set_value('Penguji sintetik')
    next(x for x in app.text_area if x.label=='Catatan verifikasi').set_value('Hanya uji perangkat lunak; data belum tersedia.')
    next(x for x in app.button if x.label=='Simpan catatan').click().run()
    assert not app.exception
    assert len(app.dataframe)>1
