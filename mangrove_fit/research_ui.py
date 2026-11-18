"""Research dashboard and read-only interactive demonstration."""
import json

import pandas as pd
import streamlit as st

from .research_service import MODELS, ResearchError, available_models, load_research, predict_research

LABELS = {'species': 'Spesies', 'length': 'Ukuran bibit awal (satuan sumber)',
          'sediment_level_cm': 'Sedimen awal (cm; satuan perlu verifikasi)',
          'SiteCondition': 'Kondisi situs', 'PlantingTreatment': 'Perlakuan / spesies',
          'zone': 'Zona', 'zone_type': 'Tipe lokasi', 'day_sin': 'Siklus hari: sinus',
          'day_cos': 'Siklus hari: kosinus', '%t_submerged': 'Fraksi waktu tergenang (0–1)',
          'pH': 'pH tanah', 'redox': 'Redoks (satuan sumber)'}


def research_page():
    from .ui_components import header, show_table
    header('LABORATORIUM / RISET', 'XGBoost & SHAP',
           'Hasil eksperimen nyata dan demonstrasi prediksi. Terpisah dari penilaian operasional zona.', research=True)
    st.info('RESEARCH_ONLY · Data historis. Input manual adalah simulasi; tidak disimpan sebagai survei. '
            'Model operasional tetap memerlukan persetujuan dan validasi lapangan.')
    keys = available_models()
    if not keys:
        st.warning('Belum ada artefak riset. Jalankan scripts/train_all_data.py terlebih dahulu.')
        return
    key = st.selectbox('Pilih model riset', keys, format_func=MODELS.get, key='research_model')
    try:
        directory, card, encoder, frame = load_research(key)
    except ResearchError as exc:
        st.error(str(exc)); return
    st.write(card['description'])
    evaluation, demonstration = st.tabs(['Evaluasi & SHAP global', 'Coba prediksi & SHAP lokal'])
    with evaluation:
        metrics = card['metrics']['nested_oof_threshold_05']
        cols = st.columns(3)
        cols[0].metric('Observasi', card['rows'])
        cols[1].metric('Balanced accuracy · ambang 0,5', f"{metrics['balanced_accuracy']:.1%}")
        cols[2].metric('Average precision', f"{metrics['pr_auc']:.3f}")
        st.caption('Validasi silang bertingkat berbasis kelompok. Skor ini bukan persentase keberhasilan penanaman. '
                   'Data telah dianalisis sebelumnya; belum ada uji eksternal baru.')
        rows = []
        for name, metric in card['metrics'].items():
            title = {'nested_oof_threshold_05': 'Model · ambang 0,5', 'nested_oof_tuned_threshold': 'Model · ambang dipilih di validasi internal',
                     'baseline_prevalence': 'Baseline prevalensi', 'simple_features_same_outer_folds': 'Model fitur lama · fold sama'}[name]
            rows.append({'Evaluasi': title, 'Balanced accuracy': metric['balanced_accuracy'], 'F1': metric['f1'],
                         'AP': metric['pr_auc'], 'Brier': metric['brier']})
        show_table(pd.DataFrame(rows), hide_index=True)
        try:
            importance = pd.read_csv(directory / 'shap_importance.csv').rename(columns={'feature': 'Fitur', 'mean_abs_oof_shap_log_odds': 'Rata-rata |SHAP|'})
            importance['Fitur'] = importance['Fitur'].map(lambda f: LABELS.get(f, f))
            st.subheader('Kontribusi fitur pada data uji tiap fold')
            st.bar_chart(importance.set_index('Fitur'), horizontal=True)
            st.caption('Satuan log-odds. SHAP menjelaskan perilaku model, bukan hubungan sebab-akibat.')
        except (OSError, ValueError, KeyError):
            st.warning('Berkas SHAP global belum tersedia atau rusak.')
        with st.expander('Metode, sumber, dan unduhan'):
            st.write(card['validation'])
            st.write('Fitur: ' + ', '.join(LABELS.get(f, f) for f in card['features']))
            st.caption('Koordinat A–C dan tanggal 19 November 2026 adalah acuan skenario esai; tidak mengganti data training historis.')
            st.download_button('Unduh kartu model riset', json.dumps(card, ensure_ascii=False, indent=2),
                               f'RISET_{key}_model_card.json', mime='application/json')
    with demonstration:
        mode = st.radio('Sumber input', ['Observasi historis', 'Input simulasi manual'], key=f'research_mode_{key}')
        inputs, selected = {}, None
        if mode == 'Observasi historis':
            st.caption('Contoh berasal dari data training final. Prediksi ini demonstrasi, bukan pengujian independen baru.')
            selected = st.selectbox('ID observasi sumber', frame.row_id.astype(str).tolist(), key=f'research_row_{key}')
            row = frame.loc[frame.row_id.astype(str).eq(selected), card['features']]
            show_table(row, hide_index=True)
        else:
            st.caption('SIMULASI · Isi semua fitur. Rentang di bawah berasal dari data training; tidak ada nilai pengukuran yang diisi otomatis.')
            cols = st.columns(2)
            for i, feature in enumerate(encoder['numeric']):
                values = pd.to_numeric(frame[feature], errors='raise')
                inputs[feature] = cols[i % 2].number_input(LABELS.get(feature, feature), value=None,
                    min_value=float(values.min()), max_value=float(values.max()),
                    key=f'research_input_{key}_{feature}', help=f'Rentang sumber: {values.min():g} hingga {values.max():g}')
            for feature in encoder['categorical']:
                inputs[feature] = st.selectbox(LABELS.get(feature, feature), encoder['categories'][feature], index=None,
                                              key=f'research_input_{key}_{feature}', placeholder='Pilih kategori sumber')
        # Results exist only for the submitted current inputs; editing inputs clears output on rerun.
        if st.button('Jalankan prediksi riset', type='primary', key='research_predict'):
            try:
                result = predict_research(key, inputs=inputs, historical_id=selected)
            except ResearchError as exc:
                st.error(str(exc)); return
            st.warning(result['watermark'])
            st.metric('Skor model untuk kelas positif', f"{result['probability']:.3f}")
            st.write(f"Kelas prediksi: **{result['prediction']}** · ambang final: {result['threshold']:.2f}")
            st.caption('Kelas 1 = hidup pada horizon target (survival), semai ditemukan, atau propagul ditemukan, sesuai model yang dipilih. '
                       'Skor belum dikalibrasi dan tidak memberikan izin atau rekomendasi tanam.')
            contributions = pd.DataFrame([{'Fitur': LABELS.get(f, f), 'SHAP lokal': v} for f, v in result['contributions'].items()])
            st.bar_chart(contributions.set_index('Fitur'), horizontal=True)
            st.caption(f"Aditivitas SHAP lulus: bias {result['bias']:.4f} + kontribusi = margin {result['margin']:.4f}. "
                       'Kontribusi positif menaikkan skor kelas 1, negatif menurunkannya.')
            st.download_button('Unduh hasil riset berwatermark', json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False),
                               f'RISET_{key}_hasil.json', mime='application/json')
