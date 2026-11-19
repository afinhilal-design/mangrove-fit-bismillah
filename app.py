import streamlit as st

import mangrove_fit.database as db
from mangrove_fit.coastal_ui import coastal_style
from mangrove_fit.ui_components import apply_style
from scripts.seed_demo import seed

st.set_page_config(page_title='MANGROVE-FIT · Kajian Pesisir',page_icon='🌿',layout='wide',initial_sidebar_state='expanded')


@st.cache_resource
def seed_once(db_path):
    seed()


seed_once(str(db.DB_PATH))
regional = [
    st.Page('pages/8_Pesisir.py', title='Prioritas wilayah', icon=':material/map:', default=True),
    st.Page('pages/9_Datasheet.py', title='Kelola datasheet', icon=':material/table_chart:'),
]
archive = [
    st.Page('pages/1_Beranda.py', title='Beranda survei', icon=':material/dashboard:'),
    st.Page('pages/2_Peta.py', title='Peta kawasan', icon=':material/map:'),
    st.Page('pages/3_Analisis.py', title='Analisis lokasi', icon=':material/eco:'),
    st.Page('pages/4_Perbandingan.py', title='Perbandingan zona', icon=':material/compare_arrows:'),
    st.Page('pages/5_Data_Model.py', title='Data survei', icon=':material/database:'),
    st.Page('pages/6_Metodologi.py', title='Metodologi survei', icon=':material/menu_book:'),
    st.Page('pages/7_Riset.py', title='XGBoost & SHAP', icon=':material/science:'),
]
page = st.navigation(regional + archive, position='hidden')
on_archive = page.url_path in {p.url_path for p in archive}
if on_archive:
    apply_style()
coastal_style(archive=on_archive)
with st.sidebar:
    st.markdown('<div class="mf-wordmark">Mangrove<span>Fit</span></div><div class="mf-brandnote">Kajian pesisir</div>', unsafe_allow_html=True)
    for p in regional:
        st.page_link(p)
    with st.expander('Survei dan riset', expanded=on_archive):
        st.radio('Ruang kerja', ['Demo', 'Analis lokal', 'Skenario Demak A–C'], index=2, key='workspace_mode',
                 help='Pilihan ini berlaku untuk halaman survei dan riset di bawah.')
        for p in archive:
            st.page_link(p)
page.run()
