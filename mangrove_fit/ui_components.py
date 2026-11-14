import html
import json
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from .config import ROOT, WATERMARK, STATUS_LABELS, COLORS, load_rules
from .database import list_zones, save_zones, save_analysis, latest_analysis, save_review, get_reviews, list_datasets
from .schemas import PARAMETERS, LANDCOVERS, LEGAL, QUALITIES, normalize_zone, values, ValidationError
from .geospatial import area_ha, center
from .services import analyse_zone
from .report_service import export_csv, export_geojson, export_markdown, export_html, safe_cell
from .prioritization import survey_sort
from .data_io import parse_upload

def apply_style():
    st.markdown('''<style>
    .block-container{padding-top:2.6rem;padding-bottom:3rem;max-width:1500px}
    h1{letter-spacing:-1.8px;font-weight:650!important;font-size:2.65rem!important;line-height:1.16!important}
    h2{letter-spacing:-.7px;font-size:1.6rem!important}h3{font-size:1.12rem!important}
    [data-testid="stSidebar"]{background:#eaf0e9;border-right:1px solid #dce5dd}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.8rem}
    .brand-mark{background:#174c3d;color:#d6e7ae;border-radius:14px;width:44px;height:44px;font-size:30px;text-align:center;line-height:40px;margin-bottom:12px}
    .brand-name{font-weight:800;font-size:22px;letter-spacing:1px}.brand-name span{font-weight:400;color:#64826e}
    .brand-sub{font-size:9px;letter-spacing:1.4px;color:#61806c;margin-top:5px}
    .eyebrow{font-size:11px;letter-spacing:2px;font-weight:700;color:#66816e;margin-bottom:11px}
    .hero{padding:34px 38px;background:#173f34;color:#f7faf2;border-radius:20px;position:relative;overflow:hidden;margin:4px 0 24px}
    .hero h1{color:#f7faf2!important;max-width:660px;margin:12px 0}.hero p{color:#c4d6c5;max-width:650px;line-height:1.65}.hero .eyebrow{color:#c2d994}
    .hero .ring{position:absolute;width:340px;height:340px;border:1px solid #60866b;border-radius:50%;right:-30px;top:-105px;opacity:.55}
    .hero .ring.two{width:270px;height:270px;right:5px;top:-70px}.hero .ring.three{width:200px;height:200px;right:40px;top:-35px}
    [data-testid="stMetric"]{background:#fff;border:1px solid #dfe7dd;padding:17px 20px;border-radius:14px}
    [data-testid="stMetricValue"]{font-weight:650;letter-spacing:-1px}
    .status-badge{display:inline-block;font-size:12px;font-weight:650;border-radius:30px;padding:7px 12px;background:#edf3ea;color:#295e49;margin-bottom:10px}
    .card{padding:22px 24px;border:1px solid #dde6dc;background:#fff;border-radius:14px;height:100%;margin:8px 0 18px}.card p{color:#66776e;font-size:14px;margin-bottom:0}
    .small-label{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#6d8273}
    .watermark{font-size:11px;letter-spacing:1.3px;color:#8b6424;background:#f6eedc;padding:10px 16px;border-radius:9px;margin-bottom:20px;border:1px solid #e9ddbe}
    .notice{color:#66796c;font-size:13px;border-top:1px solid #dce5db;padding-top:16px;margin-top:24px}
    [data-testid="stButton"] button{border-radius:9px} [data-testid="stDataFrame"]{border-radius:12px}
    @media(max-width:700px){h1{font-size:2rem!important}.block-container{padding-top:1.5rem}.hero{padding:24px}.hero .ring{opacity:.2}}
    </style>''',unsafe_allow_html=True)

def show_table(frame, **kwargs):
    # Protect the built-in dataframe CSV download as well as our export buttons.
    st.dataframe(frame.map(safe_cell), **kwargs)


def scope(): return 'demo' if st.session_state.get('workspace_mode','Demo')=='Demo' else 'local'

def header(eyebrow,title,description):
    st.markdown(f'<div class="eyebrow">{html.escape(eyebrow)}</div>',unsafe_allow_html=True)
    st.title(title)
    st.caption(description)
    if scope()=='demo': watermark()

def watermark():
    st.markdown(f'<div class="watermark">{WATERMARK} · SELURUH NILAI DAN BATAS ZONA BERSIFAT SINTETIS</div>',unsafe_allow_html=True)

def badge(status):
    color=COLORS.get(status,'#89928e')
    st.markdown(f'<span class="status-badge" style="background:{color}18;color:{color}">● {STATUS_LABELS.get(status,status)}</span>',unsafe_allow_html=True)

def choose_zone(zones,key):
    ids=[z['zone_id'] for z in zones]
    current=st.session_state.get('selected_zone')
    if current not in ids: current=ids[0]
    st.session_state[key]=current
    def remember():
        st.session_state['selected_zone']=st.session_state[key]
    selected=st.selectbox('Pilih zona',ids,index=None,format_func=lambda v:next(z['zone_name'] for z in zones if z['zone_id']==v),key=key,on_change=remember)
    if selected is None:
        selected=current
    st.session_state['selected_zone']=selected
    return next(z for z in zones if z['zone_id']==selected)

def empty_state():
    st.info('Belum ada zona dalam ruang kerja ini. Tambahkan titik atau impor CSV/GeoJSON pada Data & model.')
    st.page_link('pages/5_Data_Model.py',label='Buka Data & model',icon=':material/add_location_alt:')

def result_for(zone):
    stored=latest_analysis(zone['zone_id'])
    if stored and stored['result']['feature_snapshot']==zone and stored['result']['screening']['rules_checksum']==load_rules()['checksum']:
        r=stored['result']
        r['reviews']=[x for x in get_reviews(zone['zone_id']) if x['analysis_id']==stored['id']]
        return r,stored['id']
    return analyse_zone(zone),None

def exports(results,key):
    st.caption('Ekspor menyertakan mode, kualitas, versi aturan, waktu analisis, geometri, serta sumber setiap observasi.')
    a,b,c,d=st.columns(4)
    a.download_button('CSV',export_csv(results),'mangrove_fit_hasil.csv','text/csv',key=key+'csv',width='stretch')
    b.download_button('GeoJSON',export_geojson(results),'mangrove_fit_hasil.geojson','application/geo+json',key=key+'geo',width='stretch')
    c.download_button('Laporan HTML',export_html(results),'mangrove_fit_laporan.html','text/html',key=key+'html',width='stretch')
    d.download_button('Markdown',export_markdown(results),'mangrove_fit_laporan.md','text/markdown',key=key+'md',width='stretch')

def observation_rows(zone):
    rows=[]
    for k,m in PARAMETERS.items():
        o=zone['observations'][k]
        rows.append({'Parameter':m['label'],'Nilai':'—' if o['value'] is None else str(o['value']),'Satuan':m['unit'],'Sumber':o['source'] or 'Belum tersedia','Tanggal':o['date'] or '—','Kualitas':o['quality_flag'],'Metode':o.get('method') or '—','Datum':o.get('datum') or '—'})
    return rows

def home():
    st.markdown('''<div class="hero"><div class="ring"></div><div class="ring two"></div><div class="ring three"></div><div class="eyebrow">MANGROVE-FIT / RUANG KERJA PESISIR</div><h1>Pahami habitatnya.<br>Pilih langkah pemulihannya.</h1><p>Mulai dari kondisi pesisir, telusuri faktor pembatas, dan susun prioritas survei sebelum menentukan intervensi.</p><span style="font-size:11px;letter-spacing:1.6px;color:#c2d994">PETA · PENYARINGAN · KAJIAN TINDAKAN</span></div>''',unsafe_allow_html=True)
    if scope()=='demo': watermark()
    zones=list_zones(scope())
    if scope()=='local' and any(z['is_demo'] for z in zones): watermark()
    results=[result_for(z)[0] for z in zones]
    cols=st.columns(4)
    cols[0].metric('Zona tersimpan',len(zones))
    for col,status in zip(cols[1:],['ELIGIBLE','NEEDS_REVIEW','EXCLUDED']):
        col.metric(STATUS_LABELS[status],sum(r['screening']['status']==status for r in results))
    st.write('')
    a,b,c=st.columns(3)
    a.page_link('pages/2_Peta.py',label='Jelajahi peta kawasan',icon=':material/map:',width='stretch')
    b.page_link('pages/3_Analisis.py',label='Mulai analisis lokasi',icon=':material/eco:',width='stretch')
    c.page_link('pages/5_Data_Model.py',label='Impor dataset',icon=':material/upload_file:',width='stretch')
    st.divider()
    left,right=st.columns([1.65,1],gap='large')
    with left:
        st.subheader('Tiga pertanyaan sebelum menanam')
        for n,title,desc in [('01','Apakah habitatnya sesuai?','Saring nonhabitat, batas legal, dan kekurangan data inti.'),('02','Apa yang perlu diperiksa?','Telusuri hidrologi, gelombang, regenerasi, dan pasokan propagul.'),('03','Langkah awal apa yang masuk akal?','Lindungi, kaji regenerasi, tinjau hidrologi, atau lakukan survei tambahan.')]:
            st.markdown(f'<div class="card"><span class="small-label">{n} / KAJIAN</span><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
    with right:
        st.subheader('Status sistem')
        st.success('DEMO · RULE-BASED' if scope()=='demo' else 'RULE-BASED · DATA LOKAL')
        st.code('NO_MODEL_AVAILABLE',language=None)
        st.write('XGBoost dan SHAP belum diaktifkan. Hasil saat ini berasal dari aturan yang dapat diperiksa, bukan prediksi model.')
        st.info('Hijau berarti bisa dikaji lebih lanjut. Tidak berarti siap ditanam atau pasti berhasil.')
        if zones:
            st.caption('RINGKASAN ZONA')
            for z,r in zip(zones,results):
                st.write('**'+z['zone_name']+'**')
                badge(r['screening']['status'])
        else: empty_state()
    st.markdown('<div class="notice">Kesesuaian habitat ≠ keberhasilan rehabilitasi. Setiap tindakan tetap memerlukan verifikasi lapangan dan peninjauan ahli.</div>',unsafe_allow_html=True)

def offline_map(zones,results):
    from shapely.geometry import shape
    bounds=[shape(z['geometry']).bounds for z in zones]
    xmin=min(b[0] for b in bounds); xmax=max(b[2] for b in bounds)
    ymin=min(b[1] for b in bounds); ymax=max(b[3] for b in bounds)
    dx=max(xmax-xmin,.002);dy=max(ymax-ymin,.002)
    xmin-=dx*.12;ymin-=dy*.12;dx*=1.24;dy*=1.24
    def xy(x,y): return (45+720*(x-xmin)/dx,450-390*(y-ymin)/dy)
    paths=[]
    for z,r in zip(zones,results):
        g=shape(z['geometry']);col=COLORS[r['screening']['status']]
        if g.geom_type=='Point':
            x,y=xy(g.x,g.y);paths.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{col}"/>')
        else:
            polys=list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
            for p in polys:
                d=' '.join('M '+' L '.join(f'{xy(x,y)[0]},{xy(x,y)[1]}' for x,y in ring.coords)+' Z' for ring in [p.exterior,*p.interiors])
                paths.append(f'<path d="{d}" fill="{col}" fill-opacity=".3" stroke="{col}" stroke-width="3" fill-rule="evenodd"/>')
        lat,lon=center(z['geometry']);x,y=xy(lon,lat)
        paths.append(f'<text x="{x}" y="{y}" font-size="15" text-anchor="middle" fill="#193a30">{html.escape(z["zone_id"])}</text>')
    grid=''.join(f'<path d="M {x} 35 V 470" stroke="#d4ded5"/>' for x in range(45,800,80))+''.join(f'<path d="M 35 {y} H 785" stroke="#d4ded5"/>' for y in range(50,480,60))
    st.markdown(f'<svg viewBox="0 0 820 510" role="img" aria-label="Peta skematis koordinat zona" style="width:100%;background:#eaf1ec;border-radius:14px">{grid}{"".join(paths)}<text x="38" y="28" font-size="12" fill="#567260">SKEMA KOORDINAT · TANPA BASEMAP · EPSG:4326</text><text x="38" y="497" font-size="11" fill="#567260">Bukan peta jarak/luas · Pilih zona melalui panel di samping</text></svg>',unsafe_allow_html=True)
    st.caption(f'Rentang zona: {min(b[0] for b in bounds):.5f}–{max(b[2] for b in bounds):.5f} BT; {min(b[1] for b in bounds):.5f}–{max(b[3] for b in bounds):.5f} lintang.')

def map_page():
    header('EKSPLORASI / 01','Peta kawasan','Jelajahi zona kandidat dan periksa dasar klasifikasinya.')
    zones=list_zones(scope())
    if scope()=='local' and any(z['is_demo'] for z in zones): watermark()
    if not zones: empty_state();return
    a,b,c=st.columns([1.5,1,1])
    search=a.text_input('Cari zona',placeholder='Nama atau ID zona')
    status=b.selectbox('Status screening',['Semua']+list(STATUS_LABELS),format_func=lambda x:STATUS_LABELS.get(x,x))
    offline=c.toggle('Peta skematis offline',help='Gunakan jika internet, basemap, atau komponen peta gagal dimuat.')
    pairs=[(z,result_for(z)[0]) for z in zones]
    pairs=[(z,r) for z,r in pairs if search.lower() in (z['zone_name']+' '+z['zone_id']).lower() and (status=='Semua' or r['screening']['status']==status)]
    if not pairs: st.info('Tidak ada zona yang sesuai filter.');return
    zs,rs=zip(*pairs)
    left,right=st.columns([2.3,1],gap='large')
    with left:
        if offline: offline_map(zs,rs)
        else:
            import folium
            from streamlit_folium import st_folium
            from shapely.geometry import shape,Point
            m=folium.Map(location=center(zs[0]['geometry']),zoom_start=11,tiles='OpenStreetMap',control_scale=True)
            for z,r in pairs:
                col=COLORS[r['screening']['status']]
                # Folium embeds popup HTML in a JavaScript template literal.
                popup_name=html.escape(z['zone_name']).replace('`','&#96;').replace('$','&#36;')
                popup=folium.Popup(f'<strong>{popup_name}</strong><br>{html.escape(z["zone_id"])}<br>{STATUS_LABELS[r["screening"]["status"]]}',max_width=250)
                if z['geometry']['type']=='Point':
                    folium.CircleMarker(location=center(z['geometry']),radius=9,color=col,fill=True,fill_opacity=.8,popup=popup,tooltip=html.escape(z['zone_id'])).add_to(m)
                else:
                    folium.GeoJson({'type':'Feature','properties':{'zone_id':z['zone_id']},'geometry':z['geometry']},style_function=lambda f,col=col:{'fillColor':col,'color':col,'weight':2,'fillOpacity':.3},highlight_function=lambda f:{'weight':4,'fillOpacity':.5},tooltip=folium.GeoJsonTooltip(fields=['zone_id'],aliases=['Zona']),popup=popup).add_to(m)
            bounds=[shape(z['geometry']).bounds for z in zs]
            m.fit_bounds([[min(b[1] for b in bounds),min(b[0] for b in bounds)],[max(b[3] for b in bounds),max(b[2] for b in bounds)]],max_zoom=14)
            response=st_folium(m,height=510,use_container_width=True,key='coast_map_'+scope(),returned_objects=['last_object_clicked','last_clicked','last_active_drawing'])
            click=response.get('last_object_clicked')
            signature=json.dumps(click,sort_keys=True)
            if click and st.session_state.get('map_last_click_'+scope())!=signature:
                st.session_state['map_last_click_'+scope()]=signature
                p=Point(click['lng'],click['lat'])
                hit=next((z for z in zs if shape(z['geometry']).covers(p)),None)
                if not hit:
                    points=[z for z in zs if z['geometry']['type']=='Point']
                    if points: hit=min(points,key=lambda z:shape(z['geometry']).distance(p))
                if hit:
                    st.session_state['selected_zone']=hit['zone_id']
                    st.session_state['map_zone_'+scope()]=hit['zone_id']
            c=response.get('last_clicked')
            if c: st.caption(f"Koordinat klik: {c['lat']:.6f}, {c['lng']:.6f} (lintang, bujur)")
            st.caption('Basemap © OpenStreetMap contributors. Jika peta kosong, aktifkan Peta skematis offline; data lokal tetap tersedia.')
        st.markdown('**Legenda · hasil penyaringan awal**')
        cols=st.columns(3)
        for c,s in zip(cols,STATUS_LABELS):
            with c: badge(s)
    with right:
        zone=choose_zone(list(zs),'map_zone_'+scope())
        result=next(r for z,r in pairs if z['zone_id']==zone['zone_id'])
        badge(result['screening']['status'])
        ar=area_ha(zone['geometry'])
        st.metric('Luas geometri',f'{ar:,.2f} ha' if ar is not None else 'Titik / tanpa luas')
        st.caption('Luas dari proyeksi metrik. Batas demo bersifat fiktif.')
        st.progress(result['completeness']['percent']/100,text=f"Data inti: {result['completeness']['available']}/{result['completeness']['total']} tersedia")
        st.write('**'+result['recommendation']['action']+'**')
        st.write(result['recommendation']['focus'])
        st.page_link('pages/3_Analisis.py',label='Analisis zona ini',icon=':material/arrow_forward:')
        lat,lon=center(zone['geometry'])
        st.caption(f'ID: {zone["zone_id"]} · EPSG:4326\n\nTitik representatif: {lat:.5f}, {lon:.5f}')

def analysis_page():
    header('KAJIAN / 02','Analisis lokasi','Lihat kelengkapan data, alasan screening, dan opsi pemeriksaan berikutnya.')
    zones=list_zones(scope())
    if scope()=='local' and any(z['is_demo'] for z in zones): watermark()
    if not zones: empty_state();return
    zone=choose_zone(zones,'analysis_zone_'+scope())
    r,aid=result_for(zone)
    if scope()!='demo' and zone['is_demo']: watermark()
    a,b,c=st.columns([1.4,1,1])
    with a: badge(r['screening']['status']);st.caption(r['screening']['status'])
    b.metric('Kelengkapan parameter inti',f"{r['completeness']['percent']}%")
    c.metric('Kesesuaian model','Belum tersedia')
    if aid: st.caption(f"Analisis tersimpan #{aid} · {r['analysis_timestamp']} UTC · {r['screening']['rules_version']}")
    else: st.caption('Pratinjau aturan dari data saat ini. Simpan analisis untuk membuat snapshot dan catatan verifikasi.')
    tabs=st.tabs(['Data input','Screening','Model XGBoost','Penjelasan SHAP','Rekomendasi & verifikasi'])
    with tabs[0]:
        st.write(f"**Tutupan:** {zone['landcover_type']} · **Status legal:** {zone['legal_status']}")
        show_table(pd.DataFrame(observation_rows(zone)),hide_index=True,width='stretch',height=490)
        st.caption('Kelengkapan menghitung ketersediaan 7 parameter inti; bukan keyakinan model atau mutu ekologis.')
        with st.expander('Provenance dataset & geometri'):
            st.json({'provenance':zone['provenance'],'geometry':zone['geometry']})
        if scope()=='local': st.page_link('pages/5_Data_Model.py',label='Edit data zona',icon=':material/edit:')
    with tabs[1]:
        st.subheader(STATUS_LABELS[r['screening']['status']])
        for reason in r['screening']['reasons']: st.write('• '+reason)
        for warning in r['warnings']: st.warning(warning)
        st.caption(f"Aturan {r['screening']['rules_version']} · Konsep awal yang memerlukan telaah ahli.")
    with tabs[2]:
        st.info('NO_MODEL_AVAILABLE — Model belum tersedia; mode penilaian berbasis aturan digunakan.')
        st.write('Model hanya diaktifkan setelah tersedia data berlabel yang sah, pemisahan uji spasial, metrik validasi, serta pemeriksaan domain penerapan. Paket ini belum menghubungkan inferensi model.')
    with tabs[3]:
        st.info('SHAP belum tersedia karena belum ada model XGBoost tervalidasi.')
        st.write('Alasan screening ada pada tab Screening. SHAP nantinya menjelaskan kontribusi fitur terhadap prediksi model; bukan bukti kausalitas dan bukan persen keberhasilan tanam.')
    with tabs[4]:
        st.subheader(r['recommendation']['action'])
        st.write(r['recommendation']['focus'])
        for i,s in enumerate(r['recommendation']['next_steps'],1): st.write(f'{i}. {s}')
        st.info('Hasil ini merupakan arahan pemeriksaan awal. Peninjauan ahli dan izin setempat tetap diperlukan.')
        if scope()=='demo': st.caption('Demo bersifat baca-saja. Gunakan Analis lokal untuk menyimpan data dan catatan.')
        else:
            if st.button('Simpan analisis saat ini',type='primary'):
                save_analysis(r);st.success('Snapshot analisis tersimpan.');st.rerun()
            if aid:
                with st.form('review_form'):
                    reviewer=st.text_input('Nama verifikator / ahli')
                    decision=st.selectbox('Hasil tinjauan',['Perlu survei tambahan','Tunda intervensi','Diteruskan untuk kajian ahli'])
                    notes=st.text_area('Catatan verifikasi',placeholder='Temuan lapangan, referensi dokumen izin, koreksi, dan tindak lanjut.')
                    if st.form_submit_button('Simpan catatan'):
                        try: save_review(aid,reviewer,notes,decision);st.success('Catatan tersimpan.');st.rerun()
                        except ValueError as e: st.error(str(e))
                st.caption('Catatan tidak mengganti status screening secara otomatis. Perbaiki input bila ada temuan baru, lalu simpan analisis ulang.')
            reviews=get_reviews(zone['zone_id'])
            if reviews: show_table(pd.DataFrame(reviews),hide_index=True,width='stretch')
    st.divider()
    st.subheader('Unduh hasil kajian')
    exports([r],'analysis_')

def comparison_page():
    header('PRIORITAS / 03','Bandingkan zona','Susun urutan survei dengan alasan yang dapat ditelusuri.')
    zones=list_zones(scope())
    if scope()=='local' and any(z['is_demo'] for z in zones): watermark()
    if not zones: empty_state();return
    ids=[z['zone_id'] for z in zones]
    selected=st.multiselect('Pilih 2–5 zona',ids,default=ids[:min(3,len(ids))],max_selections=5,format_func=lambda v:next(z['zone_name'] for z in zones if z['zone_id']==v))
    if not selected: st.info('Pilih zona untuk dibandingkan.');return
    a,b=st.columns(2)
    filt=a.selectbox('Filter status',['Semua']+list(STATUS_LABELS),format_func=lambda x:STATUS_LABELS.get(x,x))
    ordering=b.selectbox('Urutkan berdasarkan',['Urutan survei','Kelengkapan data terendah','Nama zona'])
    results=[result_for(z)[0] for z in zones if z['zone_id'] in selected]
    results=[r for r in results if filt=='Semua' or r['screening']['status']==filt]
    if ordering=='Urutan survei': results=survey_sort(results)
    elif ordering=='Kelengkapan data terendah': results=sorted(results,key=lambda r:r['completeness']['percent'])
    else: results=sorted(results,key=lambda r:r['feature_snapshot']['zone_name'])
    if not results: st.info('Tidak ada zona sesuai filter.');return
    st.info('Urutan survei: perlu verifikasi → bisa dikaji lanjut → dikecualikan; dalam kelompok, data paling tidak lengkap diperiksa lebih dahulu. Ini bukan skor prioritas program atau keberhasilan tanam.')
    rows=[]
    for i,r in enumerate(results,1):
        z=r['feature_snapshot'];v=values(z)
        rows.append({'Urutan survei':i,'ID':z['zone_id'],'Nama':z['zone_name'],'Luas (ha)':area_ha(z['geometry']),'Screening':STATUS_LABELS[r['screening']['status']],'Kelengkapan (%)':r['completeness']['percent'],'Kelas habitat ML':'Tidak tersedia','Sinyal degradasi':'Abrasi terindikasi' if v.get('shoreline_change_m_y') is not None and v['shoreline_change_m_y']<0 else 'Belum dinilai','Kualitas':r['data_quality'],'Tindakan awal':r['recommendation']['action'],'Alasan':' | '.join(r['screening']['reasons'])})
    show_table(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.subheader('Bandingkan parameter')
    nums=[k for k,m in PARAMETERS.items() if 'range' in m]
    param=st.selectbox('Parameter grafik',nums,format_func=lambda k:f"{PARAMETERS[k]['label']} ({PARAMETERS[k]['unit']})")
    chart=pd.DataFrame([{'Zona':r['feature_snapshot']['zone_id'],'Nilai':values(r['feature_snapshot']).get(param)} for r in results]).set_index('Zona')
    if chart['Nilai'].notna().any():
        st.bar_chart(chart.dropna(),color='#278267',height=250)
        if chart['Nilai'].isna().any(): st.caption('Zona tanpa nilai tidak digambar; kosong bukan nol.')
    else: st.info('Belum ada nilai untuk parameter ini.')
    st.caption('Lihat sumber, tanggal, dan kualitas setiap nilai pada Analisis lokasi → Data input.')
    exports(results,'comparison_')

def zone_form():
    zones=list_zones('local')
    selected=st.selectbox('Tambah atau edit',['__new__']+[z['zone_id'] for z in zones],format_func=lambda x:'＋ Buat zona baru' if x=='__new__' else next(z['zone_name'] for z in zones if z['zone_id']==x),key='edit_choice')
    existing=next((z for z in zones if z['zone_id']==selected),None)
    with st.form('zone_form_'+selected):
        a,b=st.columns(2)
        zid=a.text_input('ID zona',value=existing['zone_id'] if existing else '',disabled=bool(existing),placeholder='ZONA-001')
        name=b.text_input('Nama zona',value=existing['zone_name'] if existing else '',placeholder='Nama lokasi survei')
        land=a.selectbox('Jenis tutupan',LANDCOVERS,index=LANDCOVERS.index(existing['landcover_type']) if existing else len(LANDCOVERS)-1)
        legal=b.selectbox('Status legal',LEGAL,index=LEGAL.index(existing['legal_status']) if existing else 1)
        st.caption('Terverifikasi berarti Anda memiliki bukti status lahan/izin. Catat referensinya di bawah; pilihan ini bukan verifikasi otomatis aplikasi.')
        legal_ref=st.text_input('Referensi status lahan / izin',value=existing.get('provenance',{}).get('legal_reference','') if existing else '')
        geom=json.dumps(existing['geometry'],ensure_ascii=False) if existing else '{"type":"Point","coordinates":[112.5,-6.9]}'
        geometry=st.text_area('Geometri GeoJSON (EPSG:4326)',value=geom,height=100,help='Point: [bujur, lintang]. Polygon: ring tertutup. Koordinat contoh perlu diganti dengan hasil survei.')
        st.markdown('**Observasi per parameter**')
        st.caption('Isi nilai beserta sumber, tanggal YYYY-MM-DD, kualitas, dan metode per baris. Biarkan nilai kosong bila belum diukur. Satuan sudah ditetapkan; jangan diganti.')
        rows=[]
        for k,m in PARAMETERS.items():
            o=existing['observations'][k] if existing else {}
            rows.append({'parameter':k,'value':'' if o.get('value') is None else str(o['value']),'unit':m['unit'],'source':o.get('source') or '', 'date':o.get('date') or '', 'quality_flag':o.get('quality_flag') if o.get('quality_flag') not in (None,'missing') else 'measured','method':o.get('method') or '', 'datum':o.get('datum') or ''})
        edited=st.data_editor(pd.DataFrame(rows),hide_index=True,width='stretch',height=500,disabled=['parameter','unit'],column_config={'quality_flag':st.column_config.SelectboxColumn('Kualitas',options=QUALITIES,required=True),'value':st.column_config.TextColumn('Nilai'),'source':st.column_config.TextColumn('Sumber'),'date':st.column_config.TextColumn('Tanggal'),'method':st.column_config.TextColumn('Metode'),'datum':st.column_config.TextColumn('Datum elevasi')},key='observations_'+selected)
        submitted=st.form_submit_button('Simpan zona',type='primary')
    if submitted:
        try:
            observations={r['parameter']:{k:(None if pd.isna(v) else v) for k,v in r.items() if k!='parameter'} for r in edited.to_dict('records')}
            provenance=dict(existing['provenance']) if existing else {}
            provenance['legal_reference']=legal_ref
            p={'zone_id':zid,'zone_name':name,'landcover_type':land,'legal_status':legal,'observations':observations,'provenance':provenance}
            # Jangan mencuci penanda data sintetis saat diedit.
            if existing and existing['is_demo']: p['quality_flag']='demo'
            z=normalize_zone(p,json.loads(geometry))
            save_zones([z],replace=bool(existing))
            st.session_state['selected_zone']=z['zone_id']
            st.success('Zona tersimpan. Buka Analisis lokasi untuk melihat hasil terbaru.')
        except (ValueError,TypeError,KeyError) as e: st.error(str(e))
    with st.expander('Kategori yang diperbolehkan untuk nilai teks'):
        for k,m in PARAMETERS.items():
            if 'choices' in m: st.write(f"**{k}:** {', '.join(m['choices'])}")

def data_page():
    header('PENGELOLAAN / 04','Data & model','Kelola zona, jejak sumber observasi, dan kesiapan model.')
    tabs=st.tabs(['Impor & template','Tambah / edit zona','Dataset tersimpan','Status model'])
    with tabs[0]:
        st.subheader('Mulai dari data yang dapat ditelusuri')
        st.write('CSV untuk titik sampel; GeoJSON untuk polygon atau titik. Semua koordinat mengikuti EPSG:4326 [longitude, latitude].')
        a,b,c=st.columns(3)
        a.download_button('Template CSV kosong',(ROOT/'data/demo/template_kosong.csv').read_bytes(),'template_kosong.csv','text/csv')
        b.download_button('Contoh CSV sintetis',(ROOT/'data/demo/titik_simulasi.csv').read_bytes(),'titik_simulasi.csv','text/csv')
        c.download_button('Contoh GeoJSON sintetis',(ROOT/'data/demo/zona_simulasi.geojson').read_bytes(),'zona_simulasi.geojson','application/geo+json')
        st.caption('Contoh GeoJSON memakai ID demo yang dicadangkan. Ubah ID sebelum diimpor ke Analis lokal; penanda data demo tetap dipertahankan.')
        if scope()=='demo':
            st.info('Pilih Analis lokal pada sidebar untuk mengimpor atau mengedit. Dataset demo bersifat baca-saja.')
        else:
            uploaded=st.file_uploader('Unggah CSV / GeoJSON',type=['csv','geojson','json'],help='Maksimum sesuai konfigurasi, default 10 MB dan 1.000 zona.')
            if uploaded:
                try:
                    zones,meta=parse_upload(uploaded.getvalue(),uploaded.name)
                    st.success(f'Validasi lolos: {len(zones)} zona. Data belum disimpan sampai tombol impor ditekan.')
                    show_table(pd.DataFrame([{'ID':z['zone_id'],'Nama':z['zone_name'],'Geometri':z['geometry']['type'],'Data sintetis':z['is_demo']} for z in zones]),hide_index=True,width='stretch')
                    replace=st.checkbox('Perbarui zona lokal dengan ID yang sama',help='Riwayat analisis sebelumnya tetap tersimpan.')
                    if st.button('Impor dan simpan',type='primary'):
                        try: save_zones(zones,replace=replace,dataset=meta);st.success('Dataset tersimpan. Pilih Analisis lokasi untuk melanjutkan.')
                        except ValueError as e: st.error(str(e))
                except (ValidationError,TypeError,KeyError) as e: st.error(f'VALIDATION_ERROR — {e}')
    with tabs[1]:
        if scope()=='demo': st.info('Pilih Analis lokal untuk menambah atau mengedit zona.')
        else: zone_form()
    with tabs[2]:
        zs=list_zones(scope())
        if zs:
            show_table(pd.DataFrame([{'ID':z['zone_id'],'Nama':z['zone_name'],'Geometri':z['geometry']['type'],'Legal':z['legal_status'],'Sumber sintetis':z['is_demo']} for z in zs]),hide_index=True,width='stretch')
            if st.button('Cadangkan seluruh zona sebagai GeoJSON'):
                rs=[result_for(z)[0] for z in zs]
                st.download_button('Unduh cadangan',export_geojson(rs),'mangrove_fit_cadangan.geojson','application/geo+json')
        else: empty_state()
        datasets=list_datasets()
        if datasets and scope()=='local': show_table(pd.DataFrame(datasets),hide_index=True,width='stretch')
        st.caption('Cadangan penuh termasuk riwayat analisis dan tinjauan: tutup aplikasi, lalu salin berkas data/app.db. Ekspor GeoJSON menyimpan data zona dan tinjauan analisis yang dipilih.')
    with tabs[3]:
        st.code('NO_MODEL_AVAILABLE',language=None)
        st.write('Paket MVP ini belum berisi model XGBoost, data latih berlabel, hasil evaluasi, atau penjelasan SHAP. Menaruh berkas model saja tidak akan mengaktifkannya.')
        st.markdown('Syarat integrasi model berikutnya:\n\n- Dataset berlabel dan sumber label yang sah.\n- Pembagian train/validation/test berbasis lokasi atau waktu.\n- Skema fitur dan preprocessing yang sesuai.\n- Evaluasi independen, domain penerapan, dan persetujuan peninjau.\n- Implementasi inferensi serta pengujian konsistensi SHAP.')
        st.info('Tidak ada unggahan pickle/joblib. Dependensi AI sengaja belum dipasang untuk menghemat ruang tahap MVP.')

def methodology_page():
    header('REFERENSI / 05','Metodologi & batasan','Pahami apa yang disimpulkan aplikasi, dari mana asalnya, dan apa yang belum diketahui.')
    a,b,c=st.columns(3)
    for col,title,text in [(a,'01 · Screening','Validasi data, geometri, habitat, legal, dan ketersediaan parameter inti.'),(b,'02 · Kajian tindakan','Aturan terbuka memberi arah pemeriksaan; peninjauan ahli tetap diperlukan.'),(c,'03 · Model bersyarat','XGBoost dan SHAP belum terhubung. Tidak ada probabilitas atau akurasi yang dibuat-buat.')]:
        with col: st.markdown(f'<div class="card"><h3>{title}</h3><p>{text}</p></div>',unsafe_allow_html=True)
    st.subheader('Tiga hal yang berbeda')
    show_table(pd.DataFrame([{'Hasil':'Kesesuaian habitat','Makna':'Kondisi yang mendukung habitat mangrove','Status MVP':'Prediksi model belum tersedia'},{'Hasil':'Urgensi intervensi','Makna':'Ancaman/degradasi yang perlu diteliti','Status MVP':'Hanya sinyal dari observasi; tidak ada skor komposit'},{'Hasil':'Kesiapan tindakan','Makna':'Kecukupan data, izin, dan tinjauan ahli','Status MVP':'Penyaringan awal; bukan izin tanam'}]),hide_index=True,width='stretch')
    st.subheader('Aturan yang dapat diperiksa')
    st.code((ROOT/'config/rules.yaml').read_text(),language='yaml')
    st.write('Aturan ini merupakan konsep awal. Tidak ada ambang salinitas, elevasi, atau genangan universal yang diangkat menjadi klaim ilmiah. Perubahan rules.yaml mengubah checksum dan membatalkan penggunaan snapshot lama sebagai hasil terkini.')
    with st.expander('Parameter, satuan, dan sumber data',expanded=True):
        show_table(pd.DataFrame([{'Field':k,'Parameter':m['label'],'Satuan':m['unit']} for k,m in PARAMETERS.items()]),hide_index=True,width='stretch')
        st.write('Salinitas, hidroperiode, substrat, dan regenerasi perlu sumber lapangan/sekunder terverifikasi. NDVI dan NDMI bukan pengukuran langsung salinitas atau keberhasilan penanaman. Elevasi tanpa datum tidak ditafsirkan terhadap pasang surut.')
    st.subheader('Keterbatasan yang perlu diketahui')
    st.markdown('- Semua zona bawaan adalah sintetis. Koordinat dan luasan tidak menunjukkan lokasi rehabilitasi nyata.\n- Status legal dan sumber diisi pengguna; aplikasi tidak memverifikasinya secara independen.\n- Tidak ada login multiuser atau sinkronisasi; ruang kerja ini untuk laptop lokal.\n- Basemap memerlukan internet. Data, formulir, screening, dan peta skematis tetap dapat digunakan offline setelah dependensi terpasang.\n- Tinjauan ahli berupa catatan, tidak mengizinkan aktivitas secara otomatis.\n- SHAP, bila diintegrasikan kelak, menjelaskan model dan bukan hubungan sebab-akibat.')
    st.subheader('Rujukan teknis')
    st.markdown('[Streamlit](https://docs.streamlit.io/) · [SQLite / Python](https://docs.python.org/3/library/sqlite3.html) · [GeoJSON RFC 7946](https://www.rfc-editor.org/rfc/rfc7946) · [Folium](https://python-visualization.github.io/folium/latest/)')
    st.caption('Rujukan ilmiah pada dokumen spesifikasi disertakan dalam docs/spesifikasi_sumber.md untuk telaah ahli. Aplikasi tidak mengunduh atau mengklaim sudah memakai dataset tersebut.')
