# Hasil training datamangroveit — 19 November 2026 (WIB)

Status: **SELESAI** untuk training kandidat dan ekspor SHAP; **PARSIAL** untuk kelayakan penggunaan. Model tetap `PENDING_REVIEW`, tidak dipasang ke `models/active`.

## Data dan target

- Sumber: `datamangroveit/sea-site_dataset_withNAs.csv` (56 titik) dan `pond_dataset_withNAs_UTF8.csv` (55 titik).
- Target `seedling_presence`: semai alami ditemukan/tidak ditemukan. Label tambak `absent` menjadi 0, `present`/`multiple` menjadi 1. Ini bukan label keberhasilan rehabilitasi atau survival penanaman.
- Fitur: lama genangan, pH tanah, redoks. Fraksi genangan dikalikan 24; satuan redoks dan periode pengamatan tetap perlu konfirmasi metadata sumber.
- 111 observasi, 109 lengkap, 2 dibuang tanpa imputasi; 30 positif dan 79 negatif pada data lengkap.
- 21 transek dipisahkan utuh; nomor transek sea-site dan tambak tidak tumpang tindih. Pembagian tetap dengan seed 42: train 62, validation 22, test 25. Jarak geografis antartransek belum dijadikan buffer validasi.
- Kolom shear strength dan parameter baru lain tidak dipakai sebelum peninjauan skema/satuan. Berkas batimetri dan deret waktu tidak digabung tanpa kunci lokasi/waktu terverifikasi.
- Q4 survival tidak dipakai pada eksperimen ini: konversi yang tersedia mengambil sedimen akhir, berisiko leakage untuk prediksi sebelum tanam; `groupby.last()` juga dapat mengambil nilai nonkosong dari waktu sebelumnya. Training survival memerlukan penyusunan fitur awal dan horizon target yang konsisten.

## Evaluasi nyata

XGBoost 3.2.0; maksimum 100 boosting rounds, early stopping pada validation; threshold 0,5. Tidak ada pemilihan seed/threshold berdasarkan test. Validasi leave-one-transect-out memakai 100 rounds tetap, terpisah dari keputusan early stopping kandidat; hasilnya menilai prosedur dengan anggaran pohon berbeda.

| Metrik | Validation (22) | Test (25) | Leave-one-transect-out (109) |
|---|---:|---:|---:|
| Balanced accuracy | 0,4706 | 0,6140 | 0,5407 |
| F1 | 0,0000 | 0,4000 | 0,2857 |
| Average precision / PR-AUC | 0,3327 | 0,6012 | 0,4655 |
| Brier (lebih rendah lebih baik) | 0,1657 | 0,1552 | 0,1867 |

Baseline test: balanced accuracy 0,5; average precision 0,24; Brier 0,1868. Confusion test: TP=2, FP=2, TN=17, FN=4. Hanya 6 positif di test; hasil belum membuktikan generalisasi ke lokasi baru. Model melewati batas numerik minimum pemeriksa otomatis, tetapi validation lemah dan validasi silang hanya sedikit di atas 0,5. Belum ada peninjauan ahli atau kalibrasi probabilitas.

Perhitungan average precision diperbaiki agar prediksi dengan skor sama dihitung pada threshold yang sama; baseline konstan sekarang tepat sama dengan prevalensi. Metrik kandidat lama tidak dihitung ulang.

## SHAP

SHAP tidak dilatih sebagai model kedua. Exact TreeSHAP dihitung dari model XGBoost yang disimpan menggunakan `pred_contribs=True`, sesuai [dokumentasi XGBoost](https://xgboost.readthedocs.io/en/release_3.2.0/python/python_api.html). Paket `shap` terpisah tidak terpasang; pemeriksaan silang TreeExplainer belum dilakukan.

Uji aditivitas lulus untuk 109 observasi: bias + kontribusi fitur = margin log-odds, galat absolut maksimum 2,3842e-7. Mean absolute SHAP pada **test saja**:

| Fitur | Mean absolute SHAP (log-odds) |
|---|---:|
| Lama genangan | 0,8460981 |
| pH tanah | 0,24701174 |
| Redoks | 0,19481140 |

Urutan ini menjelaskan perilaku model, bukan hubungan sebab-akibat. Nilai kontribusi bukan persentase probabilitas.

## Artefak dan reproduksi

Folder: `models/experiments/datamangroveit_presence/`.

- `model.ubj`, `model_card.json`: model dan kartu lengkap beserta metrik, split, checksum, parameter.
- `training.csv`, `dataset_manifest.json`: tabel turunan dan provenance sumber; data mentah tetap utuh.
- `predictions_shap.csv`: prediksi, nilai fitur, identitas baris CSV, split, bias, kontribusi setiap fitur.
- `shap_importance_test.csv`, `shap_report.json`, `run_summary.json`: ringkasan interpretasi dan evaluasi.

```powershell
.venv\Scripts\python.exe scripts/train_datamangroveit.py --out models/experiments/datamangroveit_presence_run2
```

Folder keluaran harus baru untuk menghindari penimpaan eksperimen. Pada lingkungan sandbox Windows, pembukaan ulang model oleh native XGBoost membutuhkan eksekusi yang diizinkan di luar sandbox; ekspor run ini berhasil setelah izin tersebut diberikan.

Validasi kode: `python -m pytest tests -q` menghasilkan **73 passed**. Status model aplikasi diperiksa dan tetap `NO_MODEL_AVAILABLE`.
