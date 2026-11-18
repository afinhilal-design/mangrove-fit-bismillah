import streamlit as st
import mangrove_fit.database as _db
from scripts.seed_demo import seed
from mangrove_fit.ui_components import apply_style

st.set_page_config(page_title='MANGROVE-FIT · Kajian Pesisir',page_icon='🌿',layout='wide',initial_sidebar_state='expanded')
@st.cache_resource
def _seed_once(db_path):
    # Sekali per proses/berkas DB, bukan di setiap interaksi pengguna.
    seed()
_seed_once(str(_db.DB_PATH))
apply_style()
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark"></div><div><div class="brand-name">MANGROVE<span>FIT</span></div><div class="brand-sub">KAJI HABITAT. PULIHKAN PESISIR.</div></div></div>',unsafe_allow_html=True)
    st.write('')
    st.radio('Ruang kerja',['Demo','Analis lokal','Skenario Demak A–C'],index=2,key='workspace_mode',help='Skenario Demak A–C dan Demo bersifat baca-saja. Analis lokal menyimpan survei pengguna dalam SQLite.')
    st.divider()
page=st.navigation({'EKSPLORASI':[
    st.Page('pages/1_Beranda.py',title='Beranda',icon=':material/dashboard:',default=True),
    st.Page('pages/2_Peta.py',title='Peta kawasan',icon=':material/map:'),
    st.Page('pages/3_Analisis.py',title='Analisis lokasi',icon=':material/eco:'),
    st.Page('pages/4_Perbandingan.py',title='Perbandingan zona',icon=':material/compare_arrows:')],
    'PENGELOLAAN':[
    st.Page('pages/7_Riset.py',title='XGBoost & SHAP · Riset',icon=':material/science:'),
    st.Page('pages/5_Data_Model.py',title='Data & model',icon=':material/database:'),
    st.Page('pages/6_Metodologi.py',title='Metodologi',icon=':material/menu_book:')]
})
with st.sidebar:
    st.divider()
    st.markdown('**● Sistem aktif**  \nPenilaian berbasis aturan')
    from mangrove_fit.research_service import available_models
    st.caption(('XGBoost & SHAP tersedia di menu Riset; model operasional terpisah.' if available_models()
                else 'Artefak XGBoost & SHAP riset belum tersedia.') + '\n\nPenyimpanan lokal')
page.run()
