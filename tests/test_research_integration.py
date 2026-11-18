import json
import shutil

import pytest

from mangrove_fit import research_service as service
from mangrove_fit.model_service import get_model_status


@pytest.fixture
def research():
    pytest.importorskip('xgboost')
    if len(service.available_models()) != 4:
        pytest.skip('Artefak empat model riset belum tersedia.')
    return service


def test_all_models_predict_and_explain_without_activation(research):
    before = get_model_status()
    for key in research.available_models():
        _, card, _, frame = research.load_research(key)
        result = research.predict_research(key, historical_id=str(frame.row_id.iloc[0]))
        assert result['status'] == 'RESEARCH_ONLY'
        assert 0 <= result['probability'] <= 1
        assert abs(result['bias'] + sum(result['contributions'].values()) - result['margin']) < 1e-4
        assert set(result['contributions']) == set(card['features'])
        assert 'HISTORIS' in result['watermark']
    assert get_model_status() == before


def test_manual_missing_invalid_and_outside_inputs_rejected(research):
    key = 'q4_survival_expanded'
    _, _, _, frame = research.load_research(key)
    with pytest.raises(service.ResearchError, match='Isi'):
        research.predict_research(key, {})
    values = frame.iloc[0][['length', 'sediment_level_cm', 'species']].to_dict()
    result = research.predict_research(key, values)
    assert 'SIMULASI' in result['watermark']
    for bad in [float('inf'), True, '12']:
        with pytest.raises(service.ResearchError):
            research.predict_research(key, {**values, 'length': bad})
    with pytest.raises(service.ResearchError, match='rentang'):
        research.predict_research(key, {**values, 'length': float(frame.length.max()) + 1})
    with pytest.raises(service.ResearchError, match='kategori'):
        research.predict_research(key, {**values, 'species': 'unknown'})
    with pytest.raises(service.ResearchError):
        research.load_research('../active')


def test_corrupt_artifacts_are_rejected(research, monkeypatch, tmp_path):
    key = 'q4_survival_expanded'
    shutil.copytree(research.RESEARCH_ROOT / key, tmp_path / key)
    monkeypatch.setattr(research, 'RESEARCH_ROOT', tmp_path)
    encoder_path = tmp_path / key / 'encoder.json'
    original = encoder_path.read_text(encoding='utf-8')
    encoder = json.loads(original)
    encoder['categories']['species'].reverse()
    encoder_path.write_text(json.dumps(encoder), encoding='utf-8')
    with pytest.raises(service.ResearchError, match='Kategori'):
        research.load_research(key)
    encoder_path.write_text(original, encoding='utf-8')
    (tmp_path / key / 'model.ubj').write_bytes(b'corrupt')
    with pytest.raises(service.ResearchError, match='Checksum'):
        research.load_research(key)


def test_research_page_interaction(research):
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(service.ROOT / 'pages/7_Riset.py'), default_timeout=30).run()
    assert not app.exception
    app.button(key='research_predict').click().run()
    assert not app.exception and not app.error
    assert any('Skor model' in m.label for m in app.metric)
    app.radio(key='research_mode_q4_survival_expanded').set_value('Input simulasi manual').run()
    assert not any('Skor model' in m.label for m in app.metric)
    app.button(key='research_predict').click().run()
    assert app.error and not app.exception
    _, _, _, frame = research.load_research('q4_survival_expanded')
    row = frame.iloc[0]
    app.number_input(key='research_input_q4_survival_expanded_length').set_value(float(row.length))
    app.number_input(key='research_input_q4_survival_expanded_sediment_level_cm').set_value(float(row.sediment_level_cm))
    app.selectbox(key='research_input_q4_survival_expanded_species').set_value(row.species)
    app.button(key='research_predict').click().run()
    assert not app.exception and not app.error
    for key in research.available_models():
        app.selectbox(key='research_model').set_value(key).run()
        assert not app.exception


def test_empty_research_page(monkeypatch, tmp_path):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(service, 'RESEARCH_ROOT', tmp_path)
    app = AppTest.from_file(str(service.ROOT / 'pages/7_Riset.py')).run()
    assert not app.exception
    assert any('Belum ada artefak' in x.value for x in app.warning)
