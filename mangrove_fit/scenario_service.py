"""Validated, read-only scenario overlay; never writes historical data to SQLite."""
import hashlib
import json
import math

import pandas as pd

from .config import ROOT
from .schemas import PARAMETERS, ValidationError, normalize_zone

SCENARIO_FILE = ROOT / 'data/demo/DEMO_SYNTHETIC_skenario_tiga_titik.json'
SCENARIO_LABEL = 'Skenario Demak A–C'

SOURCE_COLUMNS = {
    'inundation_duration_h_day': '%t_submerged', 'soil_ph': 'pH', 'redox_mv': 'redox',
    'bed_slope': 'slope', 'shear_strength_kpa': 'ShearStrngth', 'water_content_pct': 'WC',
    'organic_carbon_pct': 'orgC', 'bulk_density_g_cm3': 'BulkDen',
    'shelter_width_m': 'max_shelter_width_linestudy',
}


def processing_method(feature):
    column = SOURCE_COLUMNS.get(feature, feature)
    if feature == 'inundation_duration_h_day':
        return 'Fraksi waktu tergenang (%t_submerged, 0–1) × 24; dibulatkan 4 desimal menjadi jam/hari. Periode rekaman asli belum dikonfirmasi.'
    return f'Salin nilai kolom {column} pada titik sumber yang sama, tanpa imputasi. Metode/instrumen pengukuran asli belum terdokumentasi pada berkas; satuan mengikuti pemetaan proyek.'


def load_scenario_zones():
    try:
        config = json.loads(SCENARIO_FILE.read_text(encoding='utf-8'))
        source = (ROOT / config['source_table']).resolve()
        if not source.is_relative_to(ROOT.resolve()):
            raise ValidationError('Lokasi sumber skenario berada di luar workspace.')
        if hashlib.sha256(source.read_bytes()).hexdigest() != config['source_table_sha256']:
            raise ValidationError('Checksum sumber skenario tidak cocok.')
        if config['scope'] != 'demo' or not config['read_only'] or config['training_allowed']:
            raise ValidationError('Skenario harus demo, baca-saja, dan bukan data training.')
        frame = pd.read_csv(source).set_index('titik')
        points = config['points']
        if len(points) != 3 or {p['scenario_location'] for p in points} != {'A', 'B', 'C'}:
            raise ValidationError('Skenario harus berisi tiga titik A, B, dan C yang berbeda.')
        zones = []
        for point in points:
            row = frame.loc[point['source_row_id']]
            if isinstance(row, pd.DataFrame):
                raise ValidationError('ID sumber skenario ambigu.')
            for field in ['latitude', 'longitude']:
                if not math.isclose(float(row[field]), point[field], rel_tol=0, abs_tol=1e-10):
                    raise ValidationError('Koordinat skenario tidak cocok dengan sumber.')
            observations = {}
            for feature, value in point['historical_features'].items():
                if feature not in PARAMETERS or not math.isclose(float(row[feature]), value, rel_tol=0, abs_tol=1e-9):
                    raise ValidationError('Nilai skenario tidak cocok dengan sumber historis.')
                observations[feature] = {
                    'value': value, 'unit': PARAMETERS[feature]['unit'], 'quality_flag': 'demo',
                    'date': config['scenario_date'],
                    'source': f"Skenario dari observasi historis {point['source_row_id']}; {config['source_table']}",
                    'method': processing_method(feature) + ' Tanggal ini tanggal skenario, bukan tanggal survei.',
                }
            props = {'zone_id': 'SKENARIO-' + point['scenario_location'],
                     'zone_name': f"Titik {point['scenario_location']} Demak · {point['source_row_id']}",
                     'landcover_type': 'tidak_diketahui', 'legal_status': 'tidak_diketahui',
                     'quality_flag': 'demo', 'observations': observations,
                     'provenance': {'scenario': True, 'read_only': True, 'scenario_date': config['scenario_date'],
                                    'source_observation_date': point['source_observation_date'],
                                    'source_row_id': point['source_row_id'], 'source_block': point['source_block'],
                                    'source_table': config['source_table'], 'source_table_sha256': config['source_table_sha256'],
                                    'coordinate_origin': 'Koordinat historis sumber, bukan koordinat buatan.',
                                    'watermark': config['watermark'], 'assumption': point['assumption'],
                                    'unit_note': config.get('unit_note'),
                                    'unavailable_parameters': [f for f in PARAMETERS if f not in observations]}}
            zones.append(normalize_zone(props, {'type': 'Point', 'coordinates': [point['longitude'], point['latitude']]}))
        return zones
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValidationError('Konfigurasi skenario atau sumber belum lengkap. Periksa berkas skenario A–C.') from exc
