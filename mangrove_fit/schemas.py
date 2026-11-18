"""Skema dan validasi rentang fisik, bukan ambang kesesuaian habitat."""
from datetime import date
import json
import math
import re

PARAMETERS = {
    'mangrove_cover_pct': {'label': 'Tutupan mangrove', 'unit': '%', 'range': (0,100)},
    'ndvi': {'label': 'NDVI', 'unit': 'indeks', 'range': (-1,1)},
    'ndmi': {'label': 'NDMI', 'unit': 'indeks', 'range': (-1,1)},
    'elevation_m': {'label': 'Elevasi', 'unit': 'm', 'range': (None,None)},
    'inundation_duration_h_day': {'label': 'Lama genangan', 'unit': 'jam/hari', 'range': (0,24)},
    'tidal_connectivity': {'label': 'Konektivitas pasang surut', 'unit': 'kategori', 'choices': ['baik','terganggu','tidak_diketahui']},
    'salinity_ppt': {'label': 'Salinitas', 'unit': 'ppt', 'range': (0,None)},
    'substrate_type': {'label': 'Substrat', 'unit': 'kategori', 'choices': ['lumpur','pasir','campuran','lainnya','tidak_diketahui']},
    'wave_exposure': {'label': 'Paparan gelombang', 'unit': 'kategori', 'choices': ['rendah','sedang','tinggi','tidak_diketahui']},
    'shoreline_change_m_y': {'label': 'Perubahan garis pantai', 'unit': 'm/tahun', 'range': (None,None)},
    # Parameter tanah & morfologi (v0.2, 18 Nov 2026) — dipakai model kandidat dari dataset D01 sea-site.
    'soil_ph': {'label': 'pH tanah', 'unit': 'pH', 'range': (0,14)},
    'redox_mv': {'label': 'Potensial redoks', 'unit': 'mV', 'range': (-1000,1000)},
    'bed_slope': {'label': 'Kemiringan dasar', 'unit': 'rasio', 'range': (-1,1)},
    'natural_recruitment': {'label': 'Regenerasi alami', 'unit': 'kategori', 'choices': ['ada','tidak','tidak_diketahui']},
    'propagule_supply': {'label': 'Pasokan propagul', 'unit': 'kategori', 'choices': ['cukup','terbatas','tidak_diketahui']},
    'accessibility': {'label': 'Akses lokasi', 'unit': 'kategori', 'choices': ['mudah','sedang','sulit','tidak_diketahui']},
}
LANDCOVERS = ['coastal_mudflat','degraded_coastal','mangrove','sandy_beach','coral_reef','seagrass','open_water','built_area','tidak_diketahui']
LEGAL = ['terverifikasi','perlu_verifikasi','dilarang','tidak_diketahui']
QUALITIES = ['measured','modelled','estimated','demo','missing']

class ValidationError(ValueError):
    pass

def missing(value):
    return value is None or (isinstance(value,str) and value.strip().lower() in ('','null','none','nan','tidak_diketahui'))

def valid_date(value):
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)):
            raise ValueError()
        parsed = date.fromisoformat(str(value))
        if parsed > date.today():
            raise ValueError()
        return parsed.isoformat()
    except (ValueError, TypeError):
        raise ValidationError('Tanggal pengamatan harus YYYY-MM-DD dan tidak boleh di masa depan.')

def normalize_zone(properties, geometry):
    from .geospatial import validate_geometry
    if not isinstance(properties, dict):
        raise ValidationError('Properties harus berupa object.')
    p = dict(properties)
    zid = str(p.get('zone_id') or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', zid):
        raise ValidationError('zone_id wajib 1–64 karakter huruf, angka, titik, garis bawah, atau tanda hubung.')
    name = str(p.get('zone_name') or '').strip()
    if not name or len(name) > 200:
        raise ValidationError(f'{zid}: zone_name wajib diisi, maksimal 200 karakter.')
    land = p.get('landcover_type') or 'tidak_diketahui'
    legal = p.get('legal_status') or 'tidak_diketahui'
    if land not in LANDCOVERS or legal not in LEGAL:
        raise ValidationError(f'{zid}: kategori landcover_type/legal_status tidak dikenal.')
    raw_observations = p.get('observations') or {}
    if isinstance(raw_observations,str):
        try: raw_observations = json.loads(raw_observations)
        except ValueError: raise ValidationError(f'{zid}: observations bukan JSON sah.')
    if not isinstance(raw_observations,dict):
        raise ValidationError('observations harus object parameter → metadata.')
    observations = {}
    for key, meta in PARAMETERS.items():
        raw = raw_observations.get(key, {})
        if not isinstance(raw,dict):
            raise ValidationError(f'{key}: metadata harus object.')
        raw = dict(raw)
        value = raw.get('value', p.get(key))
        if missing(value):
            observations[key] = {'value': None, 'unit': meta['unit'], 'quality_flag':'missing', 'source':None,'date':None,'method':None,'datum':None}
            continue
        if 'range' in meta:
            if isinstance(value, bool): raise ValidationError(f'{key}: nilai boolean bukan angka.')
            try: value = float(value)
            except (ValueError,TypeError): raise ValidationError(f'{key}: harus angka atau kosong.')
            lo,hi = meta['range']
            if not math.isfinite(value) or (lo is not None and value < lo) or (hi is not None and value > hi):
                raise ValidationError(f'{key}: di luar rentang fisik {lo} sampai {hi}.')
        elif value not in meta['choices']:
            raise ValidationError(f'{key}: kategori tidak dikenal: {value}.')
        unit = raw.get('unit', meta['unit'])
        if unit != meta['unit']:
            raise ValidationError(f'{key}: satuan harus {meta["unit"]}, bukan {unit}.')
        source = raw.get('source', p.get('data_source'))
        quality = raw.get('quality_flag', p.get('quality_flag'))
        if not isinstance(source,str) or not source.strip():
            raise ValidationError(f'{key}: sumber data wajib diisi.')
        if quality not in QUALITIES or quality == 'missing':
            raise ValidationError(f'{key}: kualitas wajib measured/modelled/estimated/demo.')
        observed = valid_date(raw.get('date', p.get('observation_date')))
        method = raw.get('method', p.get('processing_method')) or 'Belum didokumentasikan'
        datum = (raw.get('datum', p.get('elevation_datum')) or None) if key=='elevation_m' else None
        observations[key] = {'value':value, 'unit':unit, 'source':source.strip(), 'quality_flag':quality, 'date':observed, 'method':str(method), 'datum':datum}
    provenance = p.get('provenance') or {}
    if isinstance(provenance,str):
        try: provenance = json.loads(provenance)
        except ValueError: raise ValidationError('provenance harus JSON object.')
    if not isinstance(provenance,dict): raise ValidationError('provenance harus object.')
    demo = p.get('quality_flag') == 'demo' or any(o['quality_flag']=='demo' for o in observations.values()) or p.get('data_quality') in ('DEMO','MIXED_DEMO')
    return {'zone_id':zid,'zone_name':name,'geometry':validate_geometry(geometry),'landcover_type':land,'legal_status':legal,'observations':observations,'is_demo':demo,'provenance':provenance}

def upgrade_observations(zone):
    """Migrasi baca: zona lama yang belum punya parameter baru diberi entri kosong (missing), tanpa imputasi."""
    obs = zone.setdefault('observations', {})
    for key, meta in PARAMETERS.items():
        if key not in obs:
            obs[key] = {'value': None, 'unit': meta['unit'], 'quality_flag': 'missing', 'source': None, 'date': None, 'method': None, 'datum': None}
    return zone

def values(zone):
    return {k:v['value'] for k,v in zone['observations'].items()}
