# Model belum tersedia

Rilis 0.1 tidak berisi model atau prediksi terlatih. Tidak ada dataset berlabel asli yang disertakan pengguna, sehingga menyalakan XGBoost/SHAP sekarang akan menyesatkan.

Tahap selanjutnya memerlukan:

1. Tentukan target tunggal: kesesuaian/kehadiran habitat, atau hasil rehabilitasi 12 bulan; jangan dicampur.
2. Audit asal label dan sampling negatif, serta hindari kebocoran label dari fitur tutupan tahun yang sama.
3. Bagi train/validation/test berbasis blok pesisir/waktu; fit preprocessing hanya pada train.
4. Buat baseline, latih XGBoost, evaluasi balanced accuracy/F1/PR-AUC dan kalibrasi; uji lokasi independen.
5. Simpan model native JSON/UBJ, checksum, schema fitur, domain, metrik, versi data dan persetujuan ahli.
6. Implementasikan adapter inferensi yang memeriksa screening, fitur lengkap, dan domain sebelum memprediksi.
7. Gunakan SHAP TreeExplainer pada model yang sama; uji aditivitas dan ruang output raw/log-odds/probability.
8. Tambahkan pengujian model nyata sebelum mengubah status UI.

`model_service.check_model_inputs` sudah menyediakan pemeriksaan kelengkapan fitur. Ini belum merupakan implementasi inferensi. Tidak ada pickle/joblib upload, notebook yang mengarang data latih, atau hasil akurasi fiktif. Dependensi AI baru dipilih dan dikunci setelah tahap tersebut diuji.
