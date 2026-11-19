"""Streamlit pages for the regional atlas and imported sheets."""
import hashlib
import html
import json
from pathlib import Path
from shapely import orient_polygons
from shapely.geometry import mapping, shape

import altair as alt
import pandas as pd
import streamlit as st

from .coastal_analysis import CANDIDATE, COLOURS, analyse_sheet, fmt
from .coastal_sheets import (DOCUMENTS, EXCEL, FIELDS, FORMATS, active_edition, auto_columns, clean_table,
                            delete_sheet, load_sheet, read_table, saved_sheets, sheet_names, store_sheet)
from .config import ROOT, WATERMARK
from .report_service import safe_cell

BUILTIN = 'regional'
DEFAULT_TITLE = 'Sidoarjo dan Surabaya'
CSS = (ROOT / 'assets' / 'pesisir.css').read_text(encoding='utf-8')


def coastal_style(archive=False):
    style = CSS.split('.block-container')[0] if archive else CSS
    st.markdown(f'<style>{style}</style>', unsafe_allow_html=True)


def heading(kicker, title, text):
    st.markdown(f'<div class="mf-supra">{html.escape(kicker)}</div>'
                f'<div role="heading" aria-level="1" class="mf-display">{html.escape(title)}</div>'
                f'<p class="mf-deck">{html.escape(text)}</p>', unsafe_allow_html=True)


def section(text):
    st.markdown(f'<div class="mf-section" role="heading" aria-level="2">{html.escape(text)}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def bundled(version):
    raw = pd.read_csv(version / 'lokasi.csv', dtype={'kode_kecamatan': str})
    source = json.loads((version/'sumber.json').read_text(encoding='utf-8'))
    outline = json.loads((version/'kecamatan.geojson').read_text(encoding='utf-8'))['features']
    # D3 spherical polygons use clockwise exterior rings, unlike RFC 7946 GeoJSON.
    for feature in outline:
        feature['geometry'] = mapping(orient_polygons(shape(feature['geometry']), exterior_cw=True))
    frame = raw.rename(columns={'akhir_pengamatan': 'tanggal'})
    return frame, source, outline


def regional_data():
    return bundled(active_edition())


@st.cache_data(show_spinner=False, max_entries=12)
def computed(frame):
    return analyse_sheet(frame)


def csv_bytes(frame):
    return frame.map(safe_cell).to_csv(index=False).encode('utf-8-sig')


@st.cache_data(show_spinner=False, max_entries=8, ttl=600)
def upload_names(raw, name):
    return sheet_names(raw, name)


@st.cache_data(show_spinner=False, max_entries=8, ttl=600)
def uploaded_table(raw, name, sheet, header):
    return read_table(raw, name, sheet, header)


@st.cache_data(show_spinner=False)
def map_labels(outline):
    from shapely.ops import unary_union
    records = []
    for key in ('Sidoarjo', 'Kota Surabaya'):
        districts = [shape(f['geometry']) for f in outline if f['properties']['wilayah'] == key]
        point = unary_union(districts).representative_point()
        records.append({'label': key.removeprefix('Kota '), 'lon': point.x, 'lat': point.y})
    return pd.DataFrame(records)


def atlas_map(rows, outline, builtin):
    if not {'latitude', 'longitude'}.issubset(rows):
        st.info('Tambahkan kolom lintang dan bujur untuk menempatkan lokasi di peta.')
        return
    coords = rows.dropna(subset=['latitude', 'longitude'])
    if coords.empty:
        st.info('Lokasi pada datasheet ini belum memiliki pasangan koordinat.')
        return
    if len(coords) < len(rows):
        st.caption(f'{len(coords)} dari {len(rows)} lokasi memiliki koordinat.')
    if not builtin and not (coords.latitude.between(-7.65, -7.10) & coords.longitude.between(112.45, 112.95)).all():
        from folium import CircleMarker, Map, TileLayer
        from streamlit_folium import st_folium
        m = Map(location=[coords.latitude.mean(), coords.longitude.mean()], tiles=None, zoom_start=10)
        TileLayer('OpenStreetMap').add_to(m)
        for loc in coords.itertuples():
            CircleMarker([loc.latitude, loc.longitude], radius=6, color=COLOURS[loc.status], fill=True,
                         fill_opacity=.85, tooltip=html.escape(str(loc.lokasi)+' · '+loc.status)).add_to(m)
        if len(coords[['latitude','longitude']].drop_duplicates()) > 1:
            m.fit_bounds([[coords.latitude.min(), coords.longitude.min()], [coords.latitude.max(), coords.longitude.max()]])
        st_folium(m, height=345, use_container_width=True, returned_objects=[], key='import_coast_map')
        return
    land = alt.Chart(alt.Data(values=outline)).mark_geoshape(fill='#e7e8d9', stroke='#b8bcac', strokeWidth=.65)
    # Administrative outlines are drawn locally so the regional map also works offline.
    place_names = alt.Chart(map_labels(outline)).mark_text(font='Georgia', fontSize=15, fontStyle='italic',
        color='#4a6558', align='right', dx=-4).encode(longitude='lon:Q', latitude='lat:Q', text='label:N')
    display = coords[['lokasi','kabupaten_kota','status','latitude','longitude','alasan']]
    points = alt.Chart(display).mark_circle(
        opacity=.94, size=95, stroke='#fffcf4', strokeWidth=1.5).encode(
        longitude='longitude:Q', latitude='latitude:Q',
        color=alt.Color('status:N', scale=alt.Scale(domain=list(COLOURS), range=list(COLOURS.values())), legend=None),
        tooltip=[alt.Tooltip('lokasi:N', title='Lokasi'), alt.Tooltip('kabupaten_kota:N', title='Wilayah'),
                 alt.Tooltip('status:N', title='Tindak lanjut'), alt.Tooltip('alasan:N', title='Indikator')])
    chart = alt.layer(land, place_names, points).project(type='mercator').properties(height=320, background='#eaf1ee').configure_view(stroke=None)
    st.altair_chart(chart, use_container_width=True, theme=None)
    legend = ''.join(f'<span><i style="background:{colour}"></i>{text}</span>' for text, colour in COLOURS.items() if text in set(rows.status))
    st.markdown(f'<div class="mf-legend">{legend}</div>', unsafe_allow_html=True)


def method_details():
    st.write('Aplikasi membandingkan lokasi yang memiliki jenis indikator yang sama. Untuk kunjungan berulang, aplikasi memakai tanggal terbaru dan median ulangan pada tanggal tersebut. Kunjungan sebelumnya bisa menjadi pembanding NDVI atau luas.')
    st.write('K-Means membagi sedikitnya tiga lokasi yang sebanding menjadi dua atau tiga kelompok menurut kondisi vegetasinya. Tinggi atau rendah berlaku dalam datasheet dan kelompok indikator yang dipilih. Jika variasi atau jumlah lokasi kurang, hasil hanya memuat indikator deskriptif.')
    st.write('Label kandidat digunakan jika ada salah satu sinyal penurunan: NDVI median turun sedikitnya 0,10, setidaknya 25% piksel turun sebesar 0,10, atau luas mangrove turun sedikitnya 10%. Ini ambang penapisan aplikasi. Tinjau penyebab perubahan, pasang surut, hidrologi dan status lahan sebelum menentukan tindakan.')
    st.caption('Urutan dalam satu profil mempertimbangkan tindak lanjut, kelompok K-Means, lalu indeks tekanan relatif. Angka indeks adalah ringkasan indikator, bukan peluang keberhasilan rehabilitasi.')


def regional_page():
    base, meta, outlines = regional_data()
    library = {s['id']: s for s in saved_sheets()}
    if 'coast_next' in st.session_state:
        st.session_state['coast_source'] = st.session_state.pop('coast_next')
    if 'coast_source' not in st.session_state:
        st.session_state['coast_source'] = st.session_state.get('coast_last_source', BUILTIN)
    if st.session_state['coast_source'] not in {BUILTIN, *library}:
        st.session_state['coast_source'] = BUILTIN
    heading('Atlas pesisir · Jawa Timur', 'Prioritas rehabilitasi', 'Temukan lokasi yang perlu disurvei lebih dulu dan periksa perubahan kondisi mangrovenya.')
    a, b = st.columns([1.35, 1])
    with a:
        identity = st.selectbox('Datasheet aktif', [BUILTIN, *library], key='coast_source',
                                format_func=lambda v: DEFAULT_TITLE+' · data bawaan' if v==BUILTIN else library[v]['name'])
    st.session_state['coast_last_source'] = identity
    builtin = identity == BUILTIN
    frame = base if builtin else load_sheet(identity)
    rows = computed(frame)
    if builtin:
        quality = base.set_index(['kabupaten_kota', 'lokasi'])
        for i, r in rows[rows.urutan.isna()].iterrows():
            q = quality.loc[(r.kabupaten_kota, r.lokasi)]
            rows.at[i, 'alasan'] = (f'Hanya {int(q.piksel_valid)} dari {int(q.piksel_acuan)} piksel dapat dibandingkan '
                                    f'({fmt(q.cakupan_valid_pct, 1)}%). Diperlukan minimal 20 piksel dan cakupan 50%.')
    if 'is_demo' in frame and frame.is_demo.any():
        st.warning(WATERMARK)
    with b:
        regions = sorted(s for s in rows.kabupaten_kota.unique() if s)
        region = st.selectbox('Kabupaten / kota', ['Semua wilayah', *regions], key='coast_region_'+identity)
    profiles = sorted(rows.profil.unique(), key=lambda p:(p=='Tanpa indikator', p))
    comparable = [p for p in profiles if p not in ('Tanpa indikator', 'Pembatas lahan')]
    if len(comparable) > 1:
        profile = st.selectbox('Indikator yang dibandingkan', profiles, key='coast_profile_'+identity,
                               help='Setiap pilihan memiliki urutan sendiri agar lokasi dibandingkan dengan ukuran yang sama.')
        rows = rows[rows.profil==profile]
    if region != 'Semua wilayah':
        rows = rows[rows.kabupaten_kota == region]
    label = DEFAULT_TITLE if builtin else library[identity]['name']
    if builtin:
        period = meta['periods'][1]
        st.caption(f'Periode pengamatan {period[0]} s.d. {period[1]} · dibandingkan dengan periode yang sama tahun sebelumnya. Sumber dan tanggal citra tersedia di bawah.')
    if rows.empty:
        st.info('Tidak ada lokasi yang sesuai dengan filter ini.')
        return
    rows = rows.copy()
    valid_mask = rows.urutan.notna()
    rows['urutan_tampilan'] = pd.Series(pd.NA, index=rows.index, dtype='Int64')
    rows.loc[valid_mask, 'urutan_tampilan'] = range(1, int(valid_mask.sum())+1)
    view_key = identity+'_'+region+'_'+str(rows.profil.iloc[0])
    detail_key = 'coast_detail_'+view_key
    c, d = st.columns([1.45, 1], gap='large')
    with c:
        section('Peta lokasi')
        atlas_map(rows, outlines, builtin)
        if builtin:
            st.caption('Titik menandai bagian mangrove yang dipetakan dalam setiap kecamatan. Arahkan kursor ke titik untuk melihat indikator.')
    with d:
        section('Urutan survei')
        shortlist = rows[valid_mask]
        n_candidates = int((shortlist.status == CANDIDATE).sum())
        st.markdown(f'<div class="mf-callout"><strong>{n_candidates} kandidat rehabilitasi</strong><small>{len(shortlist)} lokasi dapat dibandingkan dari {len(rows)} lokasi yang ditampilkan</small></div>', unsafe_allow_html=True)
        for r in shortlist.head(3).itertuples():
            st.markdown(f'<div class="mf-site"><span class="mf-rank">{int(r.urutan_tampilan):02d}</span><div>'
                        f'<b>{html.escape(str(r.lokasi))}</b><small>{html.escape(str(r.kabupaten_kota))}</small>'
                        f'<em style="color:{COLOURS[r.status]}">{r.status}</em><p>{html.escape(r.alasan)}</p></div></div>', unsafe_allow_html=True)
        if shortlist.empty:
            st.caption('Datasheet perlu setidaknya satu indikator kondisi untuk menghasilkan prioritas.')
        elif n_candidates:
            st.caption('Kandidat menunjukkan sinyal penurunan vegetasi. Periksa penyebabnya di lapangan sebelum memilih tindakan.')
    section('Hasil per lokasi')
    table = rows[['urutan_tampilan','lokasi','kabupaten_kota','status','kelompok','alasan']].rename(columns={
        'urutan_tampilan':'Urutan','lokasi':'Lokasi','kabupaten_kota':'Kabupaten / kota','status':'Tindak lanjut',
        'kelompok':'Kelompok tekanan','alasan':'Indikator pengamatan'})
    event = st.dataframe(table.map(safe_cell), hide_index=True, width='stretch',
                         key='coast_table_'+view_key, on_select='rerun', selection_mode='single-row',
                         column_config={'Urutan':st.column_config.NumberColumn(format='%d')})
    indices = event.selection.rows
    if indices:
        row_index = rows.index[indices[0]]
        if st.session_state.get('coast_table_choice_'+view_key) != row_index:
            st.session_state['coast_table_choice_'+view_key] = row_index
            st.session_state[detail_key] = row_index
    else:
        st.session_state.pop('coast_table_choice_'+view_key, None)
    focus = st.selectbox('Rincian lokasi', list(rows.index), format_func=lambda i: f"{rows.at[i,'lokasi']} · {rows.at[i,'kabupaten_kota']}".strip(' ·'),
                         key=detail_key)
    item = rows.loc[focus]
    st.write(f"**{item['status']}** · {item['alasan']}")
    st.caption(f"Metode pengelompokan: {item['metode']}. Profil: {item['profil']}.")
    if builtin:
        src = base[(base.lokasi==item.lokasi) & (base.kabupaten_kota==item.kabupaten_kota)].iloc[0]
        st.caption(f"Piksel yang dapat dibandingkan: {int(src.piksel_valid):,} dari {int(src.piksel_acuan):,} ({fmt(src.cakupan_valid_pct,1)}%).")
    elif item['tanggal']:
        st.caption(f"Pengamatan terakhir {item['tanggal']} · {item['jumlah_baris']} baris sumber untuk lokasi ini.")
    export = rows.copy()
    export['datasheet'] = label
    if 'is_demo' in frame and frame.is_demo.any():
        export['watermark'] = WATERMARK
    if builtin:
        meta_cols = ['lokasi','kabupaten_kota','piksel_valid','piksel_acuan','cakupan_valid_pct','awal_pengamatan','awal_pembanding','akhir_pembanding']
        export = export.merge(base[meta_cols], on=['lokasi','kabupaten_kota'], validate='one_to_one')
        export['sumber'] = meta['mask_url']+' | '+meta['stac']
    else:
        export['file_sumber'] = library[identity]['filename']
    st.download_button('Unduh hasil CSV', csv_bytes(export), 'hasil_prioritas_mangrove.csv', 'text/csv', icon=':material/download:')
    with st.expander('Cara membaca hasil dan sumber data'):
        method_details()
        if builtin:
            st.markdown(f"**Data bawaan diperbarui hingga {meta['cutoff']}.** Area pengamatan mengikuti poligon mangrove KLHK pada peta BIG tahun {', '.join(meta['mask_years'])}, dipotong batas kecamatan. Indeks NDVI berasal dari pita merah dan inframerah dekat Sentinel-2 L2A.")
            st.write('Satu piksel 20 m harus memiliki sedikitnya dua observasi jernih pada masing-masing periode. Piksel yang sama dibandingkan antartahun. Hasil disajikan untuk kecamatan dengan sedikitnya 20 piksel berpasangan dan cakupan 50%. Perubahan pasang, musim dan kekeruhan ikut memengaruhi NDVI.')
            st.markdown(f"[Peta mangrove BIG]({meta['mask_url']}) · [Batas kecamatan BIG]({meta['admin_url']}) · [Katalog Sentinel-2]({meta['stac']}/collections/{meta['collection']})")
            scenes = [s for group in meta['scenes'].values() for s in group]
            latest = max(s.split('_')[2][:8] for s in scenes)
            st.caption(f"{len(scenes)} granula citra. Perekaman terakhir dalam komposit: {latest[:4]}-{latest[4:6]}-{latest[6:]}.")
            st.download_button('Unduh daftar citra dan sumber', json.dumps(meta, ensure_ascii=False, indent=2),
                               'sumber_mangrove.json', 'application/json')
            st.download_button('Unduh datasheet bawaan', csv_bytes(base.rename(columns={'tanggal':'akhir_pengamatan'})), 'datasheet_sidoarjo_surabaya.csv', 'text/csv')


def import_panel():
    file = st.file_uploader('Pilih datasheet', type=list(FORMATS), key='coast_file',
                            help='CSV, TSV, TXT, Excel, ODS, JSON/JSONL, GeoJSON, Parquet, serta tabel Word dan PDF teks. Maksimum 10 MB.')
    if file is None:
        st.caption('Sertakan nama lokasi dan indikator kondisi, misalnya NDVI, tutupan tajuk (%), atau luas mangrove pada dua periode. Koordinat dipakai untuk peta.')
        st.download_button('Unduh contoh format CSV', 'lokasi,kabupaten_kota,tanggal,ndvi,ndvi_sebelumnya,tutupan_pct,latitude,longitude\n'.encode('utf-8-sig'),
                           'format_survei_mangrove.csv','text/csv', icon=':material/download:')
        return
    raw = file.getvalue()
    sig = hashlib.sha256(raw).hexdigest()[:16]
    ext = Path(file.name).suffix.lower().lstrip('.')
    try:
        names = upload_names(raw, file.name) if ext in EXCEL | DOCUMENTS else []
        sheet = st.selectbox('Lembar atau tabel', names, key='coast_tab_'+sig) if names else None
        header = 1
        if ext in EXCEL | DOCUMENTS or ext in ('csv','tsv','txt'):
            with st.expander('Posisi judul kolom'):
                header = int(st.number_input('Nomor baris judul', 1, 100, 1, key=f'coast_head_{sig}_{sheet}'))
        frame = uploaded_table(raw, file.name, sheet, header)
        token = f'{sig}_{sheet}_{header}'
        match = auto_columns(frame.columns)
        with st.expander('Cocokkan nama kolom', expanded='lokasi' not in match):
            st.caption('Pilih kolom sesuai satuannya. Kolom yang tidak dibutuhkan dapat dikosongkan.')
            cols = st.columns(2)
            for i, (key, (label, _)) in enumerate(FIELDS.items()):
                choices = [None, *frame.columns]
                match[key] = cols[i % 2].selectbox(label, choices, index=choices.index(match.get(key)),
                                                   format_func=lambda v:'— Lewati —' if v is None else v,
                                                   key=f'coast_col_{token}_{key}')
        with st.expander('Pratinjau tabel asli'):
            st.dataframe(frame.head(50).map(safe_cell), hide_index=True, width='stretch')
        cleaned, issues = clean_table(frame, match)
        if not issues.empty:
            with st.expander(f'{len(issues)} catatan pembacaan data', expanded=True):
                st.dataframe(issues.head(100), hide_index=True, width='stretch')
        results = computed(cleaned)
        if 'is_demo' in cleaned and cleaned.is_demo.any():
            st.warning(WATERMARK)
        n = int(results.urutan.notna().sum())
        st.write(f'**{len(results)} lokasi** terbaca dari {len(frame)} baris. Sebanyak **{n} lokasi** memiliki indikator yang dapat dinilai.')
        st.dataframe(results[['lokasi','kabupaten_kota','status','kelompok','alasan']].rename(columns={
            'lokasi':'Lokasi','kabupaten_kota':'Kabupaten / kota','status':'Tindak lanjut','kelompok':'Kelompok tekanan','alasan':'Indikator'}).map(safe_cell),
            hide_index=True, width='stretch')
        title = st.text_input('Nama datasheet', value=Path(file.name).stem, key='coast_title_'+token, max_chars=120)
        if st.button('Simpan dan buka hasil', type='primary', icon=':material/save:'):
            selected = store_sheet(title, raw, file.name, sheet, match, header, cleaned)
            st.session_state['coast_next'] = selected
            st.switch_page('pages/8_Pesisir.py')
    except ValueError as exc:
        st.warning(str(exc))


def datasheet_page():
    heading('Ruang data', 'Kelola datasheet', 'Unggah tabel lapangan, cocokkan kolomnya, lalu baca hasil analisis per lokasi.')
    import_tab, files_tab = st.tabs(['Impor file', 'Datasheet tersimpan'])
    with import_tab:
        import_panel()
    with files_tab:
        section('Koleksi lokal')
        st.write('**Sidoarjo dan Surabaya** · Data bawaan')
        st.download_button('Unduh datasheet regional', (active_edition()/'lokasi.csv').read_bytes(), 'datasheet_sidoarjo_surabaya.csv', 'text/csv')
        items = saved_sheets()
        if not items:
            st.caption('Datasheet yang kamu simpan akan muncul di sini.')
        for s in items:
            with st.expander(s['name']):
                st.caption(f"{s['filename']} · {s['sheet'] or 'tabel'} · disimpan {s['created_at'][:10]}")
                a,b = st.columns(2)
                if a.button('Buka hasil', key='coast_open_'+s['id']):
                    st.session_state['coast_next'] = s['id']
                    st.switch_page('pages/8_Pesisir.py')
                with b.popover('Hapus datasheet'):
                    st.write('Hapus salinan tersimpan ini dari aplikasi?')
                    if st.button('Ya, hapus', key='coast_delete_'+s['id']):
                        delete_sheet(s['id'])
                        st.rerun()
