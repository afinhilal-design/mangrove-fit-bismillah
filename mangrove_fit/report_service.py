import csv
import io
import json
import html
from .config import WATERMARK, STATUS_LABELS
from .geospatial import area_ha, center
from .schemas import values

def flat_result(result):
    z=result['feature_snapshot']
    lat,lon=center(z['geometry'])
    return {'zone_id':z['zone_id'],'zone_name':z['zone_name'],'longitude':lon,'latitude':lat,'geometry':json.dumps(z['geometry'],ensure_ascii=False),'area_ha':area_ha(z['geometry']),'landcover_type':z['landcover_type'],'legal_status':z['legal_status'],**values(z),'observations':json.dumps(z['observations'],ensure_ascii=False),'provenance':json.dumps(z['provenance'],ensure_ascii=False),'analysis_mode':result['analysis_mode'],'data_quality':result['data_quality'],'quality_flag':'demo' if z['is_demo'] else None,'model_status':result['model']['status'],'model_version':result['model']['version'],'analysis_timestamp':result['analysis_timestamp'],'screening_status':result['screening']['status'],'screening_reasons':' | '.join(result['screening']['reasons']),'rules_version':result['screening']['rules_version'],'rules_checksum':result['screening']['rules_checksum'],'completeness_pct':result['completeness']['percent'],'recommended_action':result['recommendation']['action'],'review_notes':json.dumps(result.get('reviews',[]),ensure_ascii=False),'watermark':WATERMARK if z['is_demo'] else 'PENYARINGAN AWAL — WAJIB TINJAUAN AHLI'}

def safe_cell(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')): return "'"+value
    return value

def export_csv(results):
    rows=[flat_result(r) for r in results]
    if not rows: return b''
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=list(rows[0]))
    writer.writeheader()
    for r in rows: writer.writerow({k:safe_cell(v) for k,v in r.items()})
    return out.getvalue().encode('utf-8-sig')

def export_geojson(results):
    features=[]
    for r in results:
        z=r['feature_snapshot']
        p=flat_result(r)
        for k in ('geometry','longitude','latitude'): p.pop(k,None)
        p['observations']=z['observations']
        p['provenance']=z['provenance']
        p['review_notes']=r.get('reviews',[])
        features.append({'type':'Feature','geometry':z['geometry'],'properties':p})
    return json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,allow_nan=False,indent=2).encode('utf-8')

def export_markdown(results):
    lines=['# MANGROVE-FIT — Laporan penyaringan awal','','Kesesuaian habitat bukan persentase keberhasilan rehabilitasi. Hasil wajib ditinjau ahli.','']
    for r in results:
        z=r['feature_snapshot']
        lines += [f"## {z['zone_id']} — {z['zone_name']}",'',f"**{WATERMARK if z['is_demo'] else 'DATA PENGGUNA — BELUM DIVERIFIKASI INDEPENDEN'}**",'',f"Mode: {r['analysis_mode']} · Kualitas: {r['data_quality']} · Waktu UTC: {r['analysis_timestamp']}",f"Model: {r['model']['status']} · model_version: null",f"Aturan: {r['screening']['rules_version']} · SHA-256: {r['screening']['rules_checksum']}",'',f"Status: **{r['screening']['status']}**",f"Tindakan: **{r['recommendation']['action']}**",f"Arah kajian: {r['recommendation']['focus']}",'']
        lines += ['- '+reason for reason in r['screening']['reasons']]
        lines += ['','Langkah pemeriksaan:','']+['- '+s for s in r['recommendation']['next_steps']]
        lines += ['','Data observasi:', '']
        for k,o in z['observations'].items():
            lines.append(f"- {k}: {o['value'] if o['value'] is not None else 'BELUM TERSEDIA'} {o['unit']}; sumber={o['source']}; tanggal={o['date']}; kualitas={o['quality_flag']}; metode={o['method']}; datum={o['datum']}")
        lines += ['','Catatan: ' + ' | '.join(r['warnings']), '', 'Verifikasi ahli: '+json.dumps(r.get('reviews',[]),ensure_ascii=False),'']
    return '\n'.join(lines).encode('utf-8')

def export_html(results):
    # Semua konten pengguna di-escape; laporan dapat dicetak menjadi PDF di browser.
    body=html.escape(export_markdown(results).decode('utf-8'))
    return f'''<!doctype html><html lang="id"><meta charset="utf-8"><title>Laporan MANGROVE-FIT</title><style>body{{max-width:960px;margin:40px auto;padding:24px;color:#193a30;font:15px/1.7 system-ui;background:#fafbf8}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}}@media print{{body{{margin:0;background:white}}}}</style><pre>{body}</pre></html>'''.encode('utf-8')
