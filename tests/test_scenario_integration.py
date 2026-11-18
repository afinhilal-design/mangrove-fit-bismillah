import json

import pytest
from streamlit.testing.v1 import AppTest

from mangrove_fit.config import ROOT
from mangrove_fit.scenario_service import load_scenario_zones
from mangrove_fit.services import analyse_zone
from mangrove_fit.report_service import export_geojson, export_csv
from mangrove_fit.schemas import normalize_zone, ValidationError


def test_scenario_coordinates_provenance_and_missing_values():
    zones = load_scenario_zones()
    assert [z['zone_id'] for z in zones] == ['SKENARIO-A', 'SKENARIO-B', 'SKENARIO-C']
    assert tuple(zones[0]['geometry']['coordinates']) == (110.504174, -6.893683)
    for z in zones:
        assert z['is_demo'] and z['provenance']['source_observation_date'] is None
        assert z['observations']['salinity_ppt']['value'] is None
        assert z['legal_status'] == 'tidak_diketahui'
        assert z['observations']['soil_ph']['quality_flag'] == 'demo'
        assert 'bukan tanggal survei' in z['observations']['soil_ph']['method']
        result = analyse_zone(z)
        assert result['screening']['status'] == 'NEEDS_REVIEW'
        assert b'SIMULASI' in export_csv([result])
        exported = json.loads(export_geojson([result]))
        feature = exported['features'][0]
        imported = normalize_zone(feature['properties'], feature['geometry'])
        assert imported['is_demo'] and imported['provenance']['source_observation_date'] is None


def test_all_available_source_parameters_are_mapped_without_imputation():
    import pandas as pd
    source = pd.read_csv(ROOT / 'models/experiments/datamangroveit_presence/training.csv').set_index('titik')
    from mangrove_fit.schemas import PARAMETERS
    for zone, count in zip(load_scenario_zones(), [9, 6, 7]):
        row = source.loc[zone['provenance']['source_row_id']]
        assert sum(o['value'] is not None for o in zone['observations'].values()) == count
        for feature in set(PARAMETERS) & set(source.columns):
            value = zone['observations'][feature]['value']
            if pd.isna(row[feature]):
                assert value is None
            else:
                assert value == pytest.approx(row[feature])


def test_scenario_research_scores_use_matching_historical_rows():
    from mangrove_fit.research_service import predict_scenario_reference, ResearchError
    from mangrove_fit.ui_components import observation_rows
    import copy
    for zone, source_id in zip(load_scenario_zones(), ['sea_1_1', 'sea_14_2', 'pond_12_1']):
        result = predict_scenario_reference(zone)
        assert result['historical_id'] == source_id
        assert result['status'] == 'RESEARCH_ONLY'
        assert result['additivity_ok']
        assert 0 <= result['probability'] <= 1
        assert zone['observations']['soil_ph']['quality_flag'] == 'demo'
        row = next(r for r in observation_rows(zone) if r['Parameter'] == 'Potensial redoks')
        assert isinstance(row['Nilai'], float) and row['Nilai'] < 0
        assert row['Kualitas'] == 'Data historis · skenario'
        assert 'Tanggal skenario' in row
        assert 'kolom redox' in row['Metode pengolahan']
        changed = copy.deepcopy(zone)
        changed['observations']['soil_ph']['value'] = 7
        with pytest.raises(ResearchError, match='tidak cocok'):
            predict_scenario_reference(changed)


def test_scenario_cannot_change_source_coordinates(tmp_path, monkeypatch):
    from mangrove_fit import scenario_service
    config = json.loads(scenario_service.SCENARIO_FILE.read_text(encoding='utf-8'))
    config['points'][0]['latitude'] = -7
    path = tmp_path / 'scenario.json'
    path.write_text(json.dumps(config), encoding='utf-8')
    monkeypatch.setattr(scenario_service, 'SCENARIO_FILE', path)
    with pytest.raises(ValidationError, match='Koordinat'):
        scenario_service.load_scenario_zones()


def test_scenario_navigation_readonly_and_local_isolation(tmp_path, monkeypatch):
    import mangrove_fit.database as db
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'ui.db')
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    assert not app.exception
    assert app.radio(key='workspace_mode').value == 'Skenario Demak A–C'
    app.switch_page('pages/2_Peta.py').run()
    assert not app.exception
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert len(app.selectbox(key='map_zone_scenario').options) == 3
    app.selectbox(key='map_zone_scenario').set_value('SKENARIO-B').run()
    app.switch_page('pages/3_Analisis.py').run()
    assert not app.exception
    assert app.selectbox(key='analysis_zone_scenario').value == 'SKENARIO-B'
    assert next(m for m in app.metric if m.label == 'Skor XGBoost riset · semai alami').value != 'Tidak tersedia'
    assert not any(b.label == 'Simpan analisis saat ini' for b in app.button)
    app.selectbox(key='analysis_zone_scenario').set_value('SKENARIO-C').run()
    assert not app.exception
    for page in ['4_Perbandingan.py', '5_Data_Model.py']:
        app.switch_page('pages/' + page).run()
        assert not app.exception
        if page == '4_Perbandingan.py':
            scores = [m for m in app.metric if m.label == 'Skor riset · semai alami']
            assert len(scores) == 3 and all(m.value != 'Tidak tersedia' for m in scores)
            assert app.selectbox(key='comparison_parameter_scenario').value == 'inundation_duration_h_day'
            assert not any('Belum ada nilai untuk parameter ini.' in x.value for x in app.info)
            comparison = app.dataframe[0].value
            assert set(comparison['Parameter tersedia']) == {'9/23', '6/23', '7/23'}
            assert set(comparison['Kualitas']) == {'Data historis · skenario'}
    assert not any(b.label == 'Simpan zona' for b in app.button)
    assert db.list_zones('local') == []
    assert len(db.list_zones('demo')) == 3
    app.radio(key='workspace_mode').set_value('Analis lokal').run()
    app.switch_page('pages/2_Peta.py').run()
    assert any('Belum ada zona' in i.value for i in app.info)
    next(b for b in app.button if b.label == 'Tampilkan skenario Demak A–C').click().run()
    assert not app.exception
    assert app.radio(key='workspace_mode').value == 'Skenario Demak A–C'
