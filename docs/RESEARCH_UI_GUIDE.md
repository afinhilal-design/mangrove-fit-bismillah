# Menggunakan XGBoost & SHAP di aplikasi

Integrasi lokal selesai pada 19 November 2026. Model operasional dan model riset terpisah. Tidak perlu menyalin model riset ke `models/active` atau menyetujui kartu secara manual.

1. Buka aplikasi yang sedang berjalan dan muat ulang halaman browser.
2. Pilih **XGBoost & SHAP · Riset** pada sidebar. Tautan juga tersedia di Data & model dan tab analisis yang belum memiliki model operasional.
3. Pilih model; pilihan awal **Survival Q4 · bulan 0 ke 16**.
4. Tab **Evaluasi & SHAP global** menampilkan metrik validasi silang, baseline, dan SHAP observasi yang ditahan pada setiap fold.
5. Buka **Coba prediksi & SHAP lokal**. Pilih **Observasi historis**, pilih ID, lalu klik **Jalankan prediksi riset**. Tidak diperlukan pengisian data atau zona SQLite.
6. Untuk perandaian sendiri, pilih **Input simulasi manual**. Isi semua fitur dan kategori. Kolom awal kosong; nilai di luar rentang atau kategori sumber ditolak. Manual Q4 memerlukan sedimen awal, ukuran bibit awal, dan spesies. Label satuan mengikuti sumber dan keterbatasannya ditampilkan.
7. Lihat skor kelas positif, keputusan pada ambang final, dan kontribusi SHAP lokal. Unduh JSON berwatermark bila diperlukan untuk esai.

**Makna kelas positif berbeda per model:** Q4 hidup bulan 16 pada bibit hidup bulan 0; Q3 hidup bulan 10 pada bibit hidup bulan 3; keberadaan semai/propagul berarti ditemukan pada pengamatan. Skor belum dikalibrasi; bukan persentase keberhasilan rehabilitasi atau izin tanam. Kontribusi SHAP bukan sebab-akibat.

Observasi historis merupakan data yang juga dipakai melatih model final: demonstrasi ini bukan evaluasi baru. Metrik evaluasi hanya diambil dari prediksi outer-fold, bukan dari contoh demonstrasi. Setelah input/model diubah, hasil lama tidak ditampilkan sampai prediksi dijalankan kembali.

Skenario 19 November 2026 dengan titik A–C tetap terpisah. Halaman tidak memindahkan pengamatan Q4 ke A–C atau membuat fitur yang belum tersedia. Tidak ada penulisan ke data mentah, dataset demo, ataupun SQLite. Ruang kerja Demo/Analis lokal sama-sama dapat membaca hasil riset.

Artefak yang dibaca: `models/experiments/all_data_v2/<model>/`. Backend memeriksa checksum model dan data training, urutan fitur, kategori encoder, batas nilai, serta aditivitas SHAP. Model dimuat dalam format native UBJ, bukan pickle. Data yang hilang pada contoh historis tetap NaN sesuai pipeline training; input simulasi manual wajib lengkap.

Jika halaman kosong, periksa artefak riset atau jalankan pipeline training. Jika XGBoost belum dipasang, gunakan `python -m pip install -r requirements-ml.txt`. Setelah instalasi restart Streamlit. `NO_MODEL_AVAILABLE` pada analisis zona tetap menunjukkan belum adanya model **operasional** yang disetujui, sementara halaman riset dapat digunakan.

Pengujian: **88 tes lulus** dengan Streamlit AppTest dan pengujian backend, termasuk navigasi halaman baru, semua empat model, formulir manual/historis, input kosong/tidak valid/di luar rentang, artefak rusak, aditivitas SHAP, dan status model operasional tetap terjaga. Tidak ada perubahan `page_config` atau skema DB.
