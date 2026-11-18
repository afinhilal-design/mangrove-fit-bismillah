# Skenario esai: tiga titik Demak

**Label wajib: SKENARIO HIPOTETIS — DATA HISTORIS, BUKAN SURVEI TERBARU.**

Tanggal skenario ditetapkan: **19 November 2026**. Tanggal ini dipilih sebagai konteks perandaian, bukan tanggal pengukuran. Tanggal pengamatan asli belum terverifikasi pada tabel yang digunakan; jangan diisi dengan tanggal skenario atau tahun publikasi sumber.

Tiga titik dipilih dari tabel sumber `models/experiments/datamangroveit_presence/training.csv`: transek berbeda, koordinat berbeda, fitur genangan/pH/redoks lengkap, dan mencakup sea-site serta tambak. Pemilihan bukan berdasarkan hasil prediksi atau label keberhasilan.

| Label skenario | ID sumber | Transek | Konteks sumber | Latitude | Longitude |
|---|---|---|---|---:|---:|
| Titik A | ss_1-1 | sea_T01 | Sea-site/pesisir | -6.893683 | 110.504174 |
| Titik B | ss_14-2 | sea_T14 | Sea-site/pesisir | -6.912354 | 110.486396 |
| Titik C | pd_12-1 | pond_T12 | Tambak | -6.914048 | 110.495973 |

Koordinat tabel ditampilkan dengan enam angka desimal dari sumber, bukan koordinat baru hasil perkiraan. Nama desa tidak ditetapkan karena belum diverifikasi. Titik adalah lokasi pengamatan, bukan batas atau luas zona rehabilitasi.

Narasi yang dapat digunakan:

> Pada skenario perencanaan bertanggal 19 November 2026, tiga titik pengamatan historis di pesisir Demak digunakan untuk memperagakan penilaian awal rehabilitasi mangrove. Karakteristik lingkungan historis diasumsikan mewakili kondisi skenario. Asumsi ini belum diverifikasi melalui survei terkini.

Ketiga titik berasal dari data keberadaan semai; tidak boleh langsung diberi label survival dari Q4 tanpa hubungan lokasi yang terverifikasi. Belum ada skor atau rekomendasi per titik yang dihitung dalam penetapan skenario ini. Karena sumber titik telah digunakan dalam eksperimen keberadaan semai, demonstrasi pada titik ini bukan evaluasi independen baru.

## Ketetapan penyesuaian data lain

- Semua penyajian skenario menggunakan tanggal acuan 19 November 2026 dan titik A–C di atas.
- `scenario_date` dan `scenario_location` merupakan asumsi presentasi; tidak mengganti waktu dan lokasi pengukuran pada sumber.
- Nilai lingkungan ketiga titik disalin dari baris sumber yang sesuai, tanpa mengisi nilai kosong. Nilai itu adalah pengamatan historis yang digunakan kembali dalam skenario, bukan pengukuran tanggal 19 November 2026.
- Baris dari lokasi lain tidak otomatis dipindahkan ke A–C. Statusnya data pendukung historis sampai ada pemetaan yang dapat dijelaskan. Menyamakan tanggal saja tidak membuktikan kesesuaian lokasi.
- Waktu relatif eksperimen, seperti bulan 0 dan bulan 16 pada Q4, tetap berurutan; tidak diratakan menjadi satu tanggal.
- Training dan evaluasi memakai identitas serta waktu asli. Penyesuaian skenario tidak dipakai untuk menciptakan label survival, lokasi validasi baru, atau skor evaluasi baru.
- Konfigurasi skenario dan inventaris berkas pendukung tersimpan di `data/demo/DEMO_SYNTHETIC_skenario_tiga_titik.json`. Berkas diberi scope demo/read-only dan watermark simulasi; tidak diimpor ke SQLite sebagai survei lokal.
