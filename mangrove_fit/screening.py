from .config import load_rules
from .schemas import missing, values, PARAMETERS

def run_screening(zone, rules=None):
    rules = rules or load_rules()
    v = values(zone)
    excluded = []
    review = []
    if zone['landcover_type'] in rules['excluded_landcovers']:
        excluded.append('Tutupan berupa nonhabitat mangrove; lindungi ekosistem yang sudah ada.')
    if zone['legal_status'] in rules['blocked_legal']:
        excluded.append('Status legal melarang kegiatan di lokasi ini.')
    if zone['landcover_type']=='sandy_beach' and v.get('wave_exposure')=='tinggi':
        excluded.append('Pantai berpasir dengan paparan gelombang tinggi: bukan kandidat penanaman mangrove.')
    if zone['landcover_type'] not in rules['allowed_landcovers']:
        review.append('Kesesuaian jenis tutupan/habitat perlu ditinjau.')
    if zone['legal_status'] not in rules['verified_legal']:
        review.append('Status legal atau izin belum diverifikasi.')
    missing_core = [k for k in rules['core_parameters'] if missing(v.get(k))]
    if missing_core:
        review.append('Parameter inti belum tersedia: '+', '.join(PARAMETERS[k]['label'] for k in missing_core)+'.')
    if any(zone['observations'][k]['quality_flag']=='estimated' for k in rules['core_parameters'] if k in zone['observations']):
        review.append('Parameter inti masih berupa estimasi; verifikasi lapangan diperlukan.')
    if v.get('wave_exposure')=='tinggi':
        review.append('Paparan gelombang tinggi memerlukan kajian dinamika pantai.')
    if v.get('tidal_connectivity')=='terganggu':
        review.append('Konektivitas pasang surut terganggu; perlu kajian hidrologi.')
    if v.get('inundation_duration_h_day') in (0,24):
        review.append('Genangan 0 atau 24 jam/hari perlu verifikasi posisi intertidal dan periode observasi.')
    warnings = []
    if v.get('elevation_m') is not None and not zone['observations']['elevation_m'].get('datum'):
        warnings.append('Datum elevasi belum tersedia; elevasi tidak digunakan untuk menyimpulkan posisi terhadap pasang surut.')
    if any(o['value'] is not None and o.get('method')=='Belum didokumentasikan' for o in zone['observations'].values()):
        warnings.append('Metode sebagian pengukuran belum didokumentasikan.')
    status = 'EXCLUDED' if excluded else 'NEEDS_REVIEW' if review else 'ELIGIBLE'
    return {'status':status,'reasons':excluded+review if excluded else review or ['Data inti dan status legal tersedia untuk evaluasi awal; tetap memerlukan telaah ahli.'], 'missing_core':missing_core,'warnings':warnings,'rules_version':rules['version'],'rules_checksum':rules['checksum']}
