# Batasan rilis 0.1

- Seluruh geometri/nilai demo sintetis. Sumber asli, legal, dan metode input pengguna belum diverifikasi independen.
- Screening ELIGIBLE berarti tersedia dasar untuk kajian lanjut, bukan bukti habitat cocok untuk semua spesies dan bukan izin tanam.
- Kesesuaian habitat tidak sama dengan persentase hidup bibit.
- XGBoost, inferensi model, SHAP, training, kalibrasi, dan evaluasi model belum tersedia.
- Aturan masih konsep awal yang memerlukan validasi ekologis setempat. Tidak ada pengukuran dampak restorasi.
- Tidak ada integrasi GEE/Sentinel/GMW, raster, riwayat garis pantai otomatis, login, API REST, multiuser, atau server produksi.
- Datum elevasi dapat disimpan. Bila tidak ada, muncul peringatan dan elevasi tidak dipakai untuk menafsirkan posisi intertidal.
- Luas titik tidak dihitung. Luas polygon menggunakan proyeksi metrik, tetapi akurasinya tetap bergantung pada akurasi batas sumber.
- Batas unggahan: default 10 MB/1.000 fitur; maksimum 50.000 vertex per geometri. Polygon melintasi antimeridian dan geometri 3D ditolak.
- Basemap dan aset komponen peta memerlukan internet. Jalur skematis offline tidak memanggil komponen peta, menampilkan koordinat lokal, dan menyediakan pilihan melalui dropdown. Pemutusan koneksi fisik laptop belum diuji.
- UI form menyunting koordinat GeoJSON; belum ada alat gambar polygon langsung.
- Penanda demo dipertahankan pada alur edit/ekspor. Pengguna tetap bertanggung jawab atas metadata file eksternal; ini bukan mekanisme anti-pemalsuan forensik.
- CSV ekspor mengawali teks formula dengan apostrof. Teks tersebut sengaja berubah saat roundtrip demi keamanan spreadsheet.
- Catatan verifikator tidak mengubah screening; temuan baru harus dimasukkan sebagai revisi input lalu dianalisis ulang.
- Ekspor ringkasan berisi catatan snapshot terkini. Backup SQLite diperlukan untuk riwayat lengkap.
- Telah diuji Linux/Python 3.12.14; launcher Windows/macOS belum dijalankan pada OS tersebut.
