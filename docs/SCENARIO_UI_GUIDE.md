# Peta dan analisis skenario Demak A–C

## Perbandingan yang terhubung ke hasil riset

Perbandingan skenario kini menampilkan kartu skor XGBoost historis tiap titik, tabel ringkas dengan jumlah parameter tersedia (9/23, 6/23, 7/23), kelengkapan parameter inti yang terpisah, dan kualitas **Data historis · skenario**. Alasan screening dan kebutuhan verifikasi ada dalam panel detail. Tidak dibuat kelas kesesuaian habitat, nilai degradasi, atau luas polygon dari titik.

Grafik otomatis membuka parameter yang mempunyai data, dimulai dengan lama genangan. Pilihan tanpa data pada semua titik tidak ditawarkan; jika hanya sebagian titik memiliki nilai, titik yang kosong tidak digambar dan diberi keterangan. Unduhan perbandingan skor riset terpisah dari ekspor screening dan mempertahankan watermark. Skor riset tidak mengubah urutan survei. Pengujian perubahan tampilan: 15 tes skenario/UI lulus.

Pembaruan kelengkapan: seluruh parameter numerik yang tersedia pada baris sumber kini dipetakan: **A 9 parameter, B 6 parameter, C 7 parameter**. Tambahan mencakup kemiringan dasar, kuat geser, kadar air, karbon organik, densitas curah dan lebar perlindungan sesuai ketersediaan masing-masing titik. Tidak ada imputasi. Satuan mengikuti konverter proyek dan tetap memerlukan konfirmasi metadata sebelum penggunaan operasional.

Analisis lokasi menampilkan parameter tersedia terlebih dahulu; daftar parameter kosong ada dalam bagian **Parameter belum tersedia**. Kelengkapan parameter inti tetap dihitung terpisah dan tidak dinaikkan oleh fitur tambahan noninti. Pengujian perubahan ini: **14 tes integrasi skenario/UI lulus**.

Pilih **Skenario Demak A–C** pada sidebar. Sesi baru membuka ruang kerja ini secara default. Sesi browser yang masih berada di Analis lokal dapat memilihnya langsung atau menekan **Tampilkan skenario Demak A–C** pada halaman kosong.

- **Peta kawasan:** tiga titik SKENARIO-A, SKENARIO-B, SKENARIO-C menggunakan koordinat historis terverifikasi terhadap tabel sumber. Pilih titik lalu buka Analisis zona ini. Jika latar peta tidak termuat, gunakan Skematis offline.
- **Analisis lokasi:** menampilkan genangan, pH, redoks dan metadata sumber; pilihan titik diteruskan dari peta. Tanggal pada tabel diberi label **Tanggal skenario**. Status habitat/legal dan parameter lain tetap tidak diketahui/kosong.
- **Perbandingan zona:** ketiga titik dapat dibandingkan dan diekspor. Titik tidak mempunyai luas poligon yang diketahui.
- **Data & model:** daftar skenario dapat dilihat dan diekspor; impor dan edit hanya tersedia untuk Analis lokal.

Skenario adalah overlay baca-saja. Tiga titik tidak disimpan sebagai survei baru di SQLite dan tidak dicampur dengan SIM-A/SIM-B/SIM-C bawaan. Checksum sumber serta kesesuaian nilai dan koordinat diperiksa pada pemuatan. Kesalahan sumber menampilkan pesan, bukan koordinat/nilai pengganti.

Tanggal skenario **19 November 2026** dipakai sebagai tanggal asumsi pada observasi dengan kualitas `demo`, bukan tanggal survei. Tanggal survei sebenarnya tetap `null` pada provenance. Metode setiap nilai menjelaskan penggunaan data historis sebagai perandaian. Koordinat tidak dibuat-buat; klaim nama desa, habitat, status legal, salinitas, dan kondisi terkini tidak ditambahkan.

Ketiga titik menghasilkan **Perlu verifikasi / NEEDS_REVIEW** karena informasi inti dan legal belum cukup. Ini hasil screening yang benar, bukan kegagalan integrasi. Kartu **Skor XGBoost riset · semai alami** kini menampilkan skor model final untuk baris historis sumber yang sesuai. Tab Model XGBoost menyediakan fitur lengkap model serta unduhan hasil berwatermark; tab Penjelasan SHAP menampilkan kontribusi lokal dan uji aditivitas. Skor ini bukan model operasional dan bukan prediksi kondisi terkini. Screening, rekomendasi, dan ekspor kajian aturan tidak diganti oleh hasil riset.

Model riset keberadaan semai memakai 17 fitur numerik dan tipe zona dari tabel historis lengkap, termasuk fitur yang tidak menjadi parameter aplikasi. Nilai kosong historis ditangani secara native oleh XGBoost, tanpa angka random. Kemampuan validasi model ini masih lemah (balanced accuracy 48,8%); prediksi baris sumber adalah demonstrasi, bukan evaluasi independen. Prediksi survival Q4 tidak dipindahkan ke titik A–C.

Kolom tampilan kualitas menggunakan **Data historis · skenario**. Flag internal `demo` dan watermark ekspor tetap dipertahankan agar skenario tidak disalahartikan sebagai survei baru. Metode dijelaskan sebagai pengolahan data: konversi fraksi genangan × 24, atau penyalinan kolom sumber tanpa imputasi. Metode/instrumen lapangan yang belum terdokumentasi tidak dibuat-buat. Pembulatan empat desimal hanya untuk tampilan, bukan perubahan nilai sumber.

Ekspor mempertahankan watermark simulasi, geometri, tanggal skenario, nilai kosong dan provenance sumber. Jangan menghapus penanda tersebut ketika menggunakan hasil pada esai.

Verifikasi: 90 tes lulus pada suite penuh; satu assertion tipe koordinat diperbaiki dari list menjadi tuple sesuai validator geometri, lalu ketiga tes integrasi skenario lulus saat dijalankan ulang. Seluruh 91 kasus tes telah lulus pada pemeriksaan akhir masing-masing. Streamlit AppTest memeriksa peta online/offline, pemilihan B/C, analisis, perbandingan, halaman data, perpindahan dari Analis lokal kosong, serta tidak adanya kontrol penyimpanan skenario.
