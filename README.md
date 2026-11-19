# MANGROVE-FIT

Aplikasi Streamlit untuk menentukan lokasi survei rehabilitasi mangrove di pesisir Kabupaten Sidoarjo dan Kota Surabaya. Halaman pertama menampilkan peta, urutan lokasi, kondisi vegetasi dan sumber pengamatan.

## Data bawaan

Edisi 18 November 2026 mencakup 7 kecamatan di Sidoarjo dan 10 di Surabaya. Komposit Sentinel-2 L2A Collection 1 membandingkan periode 10 Oktober–18 November 2025 dengan 10 Oktober–18 November 2026. Citra paling baru yang lolos pemilihan direkam 15 November 2026. Poligon mangrove acuan berasal dari peta KLHK tahun 2021 yang disajikan BIG. Pengamatan mencakup area di dalam poligon lama tersebut.

Setiap piksel pada grid 20 m memerlukan dua tanggal pengamatan valid pada masing-masing periode. Analisis hanya membandingkan piksel yang tersedia pada kedua periode. Sebanyak 16 kecamatan memenuhi batas minimum 20 piksel dan 50% cakupan. Asem Rowo memiliki cakupan 17,1% dan tetap terlihat di peta tanpa peringkat.

Di **Kelola datasheet → Datasheet tersimpan**, klik **Unduh datasheet regional** untuk memperoleh CSV. Daftar citra, tautan sumber dan tanggalnya tersedia di **Prioritas wilayah → Cara membaca hasil dan sumber data**.

## Prasyarat

- Windows 10/11 (atau Linux/macOS)
- Python 3.11 atau 3.12
- Koneksi internet untuk basemap (data lokal tetap berjalan offline)

---

## Instalasi (Windows)

### Cara 1 — Otomatis (klik dua kali)

1. Pastikan Python 3.11/3.12 sudah terinstall: [python.org/downloads](https://www.python.org/downloads/)
2. Klik dua kali **`01_INSTALL_WINDOWS.bat`** — tunggu hingga selesai
3. Klik dua kali **`02_JALANKAN_WINDOWS.bat`** — browser akan terbuka otomatis

### Cara 2 — Manual (PowerShell)

```powershell
# 1. Masuk ke folder proyek
cd path\ke\mangrove-fit-bismillah

# 2. Buat virtual environment
python -m venv .venv

# 3. Aktifkan virtual environment
.venv\Scripts\Activate.ps1

# 4. Install dependensi
pip install -r requirements.txt

# 5. Jalankan aplikasi
streamlit run app.py
```

Aplikasi akan terbuka di: **http://localhost:8501**

---

## Cara Menggunakan

### Data sendiri

1. Buka **Kelola datasheet** dan pilih file. Aplikasi mendukung CSV, TSV, TXT, XLS, XLSX, XLSB, ODS, JSON, JSONL, GeoJSON, Parquet, tabel Word DOCX dan tabel pada PDF teks bergaris.
2. Untuk buku kerja atau dokumen, pilih lembar atau tabel. Bila judulnya berada di bawah baris pertama, atur **Posisi judul kolom**. Nama berbahasa Indonesia dan Inggris yang dikenal dipetakan otomatis. Periksa satuan dan sesuaikan melalui **Cocokkan nama kolom**.
3. Sertakan nama lokasi dan sedikitnya satu indikator vegetasi. Misalnya NDVI, tutupan tajuk dalam persen, kehilangan luas, atau kerapatan pohon per hektare. Dua luas pada periode yang sebanding juga dapat menghasilkan persentase kehilangan. Koordinat bersifat opsional. Satu nilai luas saja tercatat sebagai inventaris.
4. Hasil awal muncul saat file dibaca. Pilih **Simpan dan buka hasil** untuk menyimpan tabel di SQLite lokal. Gunakan **Datasheet aktif** untuk berpindah antara tabel sendiri dan data bawaan.
5. Gunakan filter wilayah, pilih baris atau rincian lokasi, lalu unduh hasil CSV. File yang sama dengan pilihan lembar, judul dan pemetaan sama akan memperbarui nama salinan yang sudah ada.

Batas satu file adalah 10 MB, 20.000 baris dan 250 kolom. File PDF berupa pindai, foto, tabel tanpa struktur yang terbaca, atau file tanpa indikator memerlukan penyiapan data. Nilai yang gagal dibaca ditandai. Data kosong tidak diganti dengan nol.

### Membaca urutan survei

K-Means berjalan lokal tanpa API key. Lokasi dibandingkan jika profil indikatornya sama. Tiga lokasi atau lebih dengan variasi indikator dapat dibagi menjadi dua atau tiga kelompok. Dengan data sedikit atau seragam, aplikasi menampilkan indikator deskriptif. Urutan mencantumkan status tindak lanjut, kelompok tekanan, serta ringkasan indikator yang arahnya diseragamkan.

Ambang penapisan dalam aplikasi menandai kandidat jika NDVI median turun ≥0,10, minimal 25% piksel turun ≥0,10 NDVI, atau kehilangan luas mangrove mencapai 10%. Ini pilihan desain untuk menyeleksi kunjungan. Pasang surut, kondisi citra dan perubahan musiman dapat memengaruhi hasil. Survei hidrologi, pemeriksaan penyebab degradasi dan status lahan diperlukan sebelum menetapkan bentuk rehabilitasi.

**Survei dan riset** memuat ruang kerja lokal, demo sintetis dan skenario historis Demak. Model XGBoost / SHAP riset memiliki target semai dan survival tersendiri. Hasilnya tersedia pada arsip riset jika dependensi opsional terpasang.

### Memperbarui data bawaan

Pembacaan, pengelompokan dan peta regional berjalan dari berkas lokal. Untuk membangun edisi berikutnya dari BIG dan katalog publik Earth Search, jalankan perintah berikut dari lingkungan Python proyek dengan akses internet. Ganti tanggal dengan akhir periode yang sudah selesai.

```bash
python -m pip install "rasterio>=1.4,<2"
python scripts/update_pesisir.py --tanggal 2026-11-18
```

Pembaruan mengunduh band citra untuk pemrosesan dan memeriksa integritasnya. Setiap edisi memuat `lokasi.csv`, `kecamatan.geojson`, dan `sumber.json` di `data/pesisir/`. Penanda aktif berubah setelah edisi baru lengkap. Impor pengguna tetap tersimpan saat data bawaan diperbarui.

## Struktur Folder

```
mangrove-fit-bismillah/
├── app.py                    # Entry point Streamlit
├── pages/                    # Halaman-halaman UI
│   ├── 1_Beranda.py
│   ├── 2_Peta.py
│   ├── 3_Analisis.py
│   ├── 4_Perbandingan.py
│   ├── 5_Data_Model.py
│   ├── 6_Metodologi.py
│   ├── 7_Riset.py
│   ├── 8_Pesisir.py
│   └── 9_Datasheet.py
├── mangrove_fit/             # Modul backend Python
├── config/
│   ├── rules.yaml            # Aturan screening ekologis (dapat diedit)
│   └── demo_mode.yaml
├── data/
│   ├── pesisir/              # Snapshot regional dan manifest sumber
│   ├── demo/                 # Data sintetis (SIMULASI)
│   └── app.db                # Database SQLite lokal (dibuat otomatis)
├── docs/                     # Dokumentasi teknis
├── tests/                    # Unit tests
└── requirements.txt
```

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: streamlit` | Jalankan `pip install -r requirements.txt` |
| Peta tidak muncul | Aktifkan **"Peta skematis offline"** di halaman Peta |
| `Error: cannot import name ...` | Pastikan virtual environment aktif (`.venv\Scripts\Activate.ps1`) |
| Port 8501 sudah terpakai | Jalankan `streamlit run app.py --server.port 8502` |
| Gagal membuka database | Pastikan folder proyek dapat ditulis dan tersedia ruang disk. Salin `data/app.db` sebelum melakukan pemulihan. |
| Data demo muncul di mode lokal | Normal — klik "Analis lokal" di sidebar, tambah zona baru |

---

## Menjalankan Tests

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

Tes mencakup impor datasheet, peringkat, integritas model arsip, dan navigasi Streamlit.

---

## Keterbatasan Penting

- **Kesesuaian habitat ≠ keberhasilan rehabilitasi.** Hasil screening hanya arah kajian awal.
- Data regional memakai citra dan geometri publik. Skenario Demak dan demo memiliki penanda tersendiri.
- Pengelompokan regional menggunakan K-Means. Model XGBoost di ruang riset memakai data historis.
- Peta bawaan Sidoarjo–Surabaya tersedia offline. Peta jalan untuk unggahan dari luar wilayah membutuhkan koneksi internet.
- Tidak ada multiuser, login, atau keamanan produksi.

Lihat [`docs/limitations.md`](docs/limitations.md) untuk daftar lengkap.

---

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Arsitektur sistem dan alur data |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Kamus field dan parameter |
| [`docs/limitations.md`](docs/limitations.md) | Keterbatasan rilis 0.1 |
| [`docs/deployment.md`](docs/deployment.md) | Cara deploy lokal |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Panduan pengguna lengkap |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | Metodologi screening dan ML |
| [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) | Status implementasi tiap fitur |
| [`data/DATA_STATUS.md`](data/DATA_STATUS.md) | Status akses dataset ilmiah |

---

## Referensi Ilmiah

Dataset dan sumber data yang relevan didokumentasikan di [`docs/spesifikasi_sumber.md`](docs/spesifikasi_sumber.md) dan [`data/DATA_STATUS.md`](data/DATA_STATUS.md). Sumber snapshot regional dan metode pengolahannya tercatat di setiap edisi.

---

## Lisensi & Atribusi

- Basemap: © OpenStreetMap contributors
- Aplikasi: dikembangkan sebagai proof of concept untuk IT RUSH 2026
- Data demo: sintetis — bukan data lapangan atau hasil penelitian nyata
