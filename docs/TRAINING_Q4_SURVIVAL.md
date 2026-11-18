# Training survival Q4 — 19 November 2026

**SELESAI:** training kandidat XGBoost dan exact TreeSHAP. **TERHAMBAT:** kelayakan operasional, karena evaluasi tidak melampaui baseline. Status artefak `PENDING_REVIEW`; aplikasi tidak diaktifkan.

## Skenario esai

Data historis diasumsikan mewakili kondisi saat ini sebagai pembuktian konsep. Ini bukan survei baru. Bulan relatif asli dipertahankan; tidak ada tanggal kalender, hasil lapangan, atau akurasi yang dibuat-buat.

## Data dan metode

Sumber: `datamangroveit/Q4_EMR-and-planting.csv`, checksum dan audit disimpan dalam manifest. Ada 2.800 baris longitudinal dan 399 ID unik. ID J4 memiliki dua catatan per bulan dengan ukuran bibit berbeda; semua 14 baris ID ini dikeluarkan, bukan digabung atau ditebak identitasnya. ID P0 sudah tercatat mati pada bulan 0 dan dikeluarkan dari kohort bibit hidup awal.

Hasil: 397 bibit, 20 blok, 129 hidup dan 268 mati pada bulan 16. Tidak ada nilai fitur/target kosong pada kohort ini; tidak ada imputasi. Unit analisis satu bibit, target hidup/mati pada bulan 16. Satu fitur yang digunakan adalah `sediment_raw` **bulan 0**, dipetakan ke `sediment_level_cm` mengikuti konverter proyek. Satuan masih perlu konfirmasi metadata eksternal.

Spesies dan ukuran bibit awal belum menjadi fitur model ini; keduanya memerlukan pipeline fitur eksperimen tersendiri tanpa mengubah skema observasi aplikasi. Ini model pembanding dengan fitur terbatas, bukan pemanfaatan penuh Q4 atau seluruh folder. Tidak ada penggabungan otomatis dengan data batimetri dan seri pengamatan lain.

Pembagian blok utuh, seed 42: train 218, validation 79, test 100 bibit. XGBoost maksimum 100 rounds dengan early stopping pada validation. Leave-one-block-out memakai 100 rounds tetap; berbeda dari jumlah pohon kandidat hasil early stopping. Test tidak digunakan untuk memilih seed, fitur, atau threshold. Threshold tetap 0,5. Tidak ada klaim independensi geografis antarlokasi di luar blok eksperimen.

## Hasil nyata

| Metrik | Validation | Test | Leave-one-block-out |
|---|---:|---:|---:|
| Balanced accuracy | 0,5000 | 0,5000 | 0,4914 |
| F1 | 0,0000 | 0,0000 | 0,0671 |
| Average precision | 0,3305 | 0,3394 | 0,3541 |
| Brier | 0,2063 | 0,2497 | 0,2380 |

Baseline prevalensi pada test: BA 0,5; AP 0,37; Brier 0,2360. Jadi model tidak lebih baik dari baseline pada metrik test tersebut. Confusion test: TP=0, FP=0, TN=63, FN=37. Seluruh test diprediksi mati pada threshold 0,5. Accuracy biasa 63% hanya mencerminkan proporsi kelas mati dan tidak menunjukkan model berhasil mengenali bibit hidup.

Hasil tidak membuktikan bahwa seluruh data Q4 gagal memprediksi survival: hanya konfigurasi satu fitur awal ini yang diuji. Penambahan fitur relevan dan validasi pada data baru diperlukan sebelum klaim yang lebih luas.

## SHAP dan verifikasi

Exact TreeSHAP bawaan XGBoost dihitung untuk 397 bibit. Uji bias + kontribusi = margin log-odds lulus; galat maksimum 5,9605e-8. Mean absolute SHAP test untuk sedimen awal = 0,32016632 log-odds. Karena hanya satu fitur, tidak ada perbandingan kepentingan antarfitur. SHAP menjelaskan model yang lemah ini; bukan bukti pengaruh kausal sedimen.

Seluruh **76 tes lulus**, termasuk kesesuaian fitur dengan bulan 0, target bulan 16, pengecualian ID ambigu, tidak mengisi NA awal dengan pengamatan masa depan, dan penolakan label survival tidak valid.

## Artefak

Folder `models/experiments/q4_survival_baseline/` berisi:

- `model.ubj`, `model_card.json`: kandidat dan kartu model.
- `training.csv`, `dataset_manifest.json`: kohort dan audit sumber/pengecualian.
- `predictions_shap.csv`: prediksi dan kontribusi per baris, dengan penanda split.
- `shap_importance_test.csv`, `shap_report.json`, `run_summary.json`: hasil interpretasi dan evaluasi.

Reproduksi (folder keluaran harus baru):

```powershell
.venv\Scripts\python.exe scripts/train_survival_q4.py --out models/experiments/q4_survival_run2
.venv\Scripts\python.exe -m pytest tests -q
```

Training keberadaan semai sebelumnya tetap terpisah dan tidak ditimpa. Tidak ada perubahan DB, skema observasi, data mentah, atau aktivasi model aplikasi.
