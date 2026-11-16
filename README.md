# 🌿 MANGROVE-FIT

**MANGROVE-FIT: Aplikasi Prioritisasi Rehabilitasi Mangrove di Pesisir Pantai Berbasis XGBoost dan SHAP dengan Integrasi Data Hidrologi dan Geospasial**

> Wilayah studi: Pesisir Kabupaten Demak, Jawa Tengah, Indonesia  
> Versi: MVP 0.1 · Bahasa antarmuka: Indonesia  
> Status sistem: Rule-based screening · XGBoost & SHAP belum tersedia

---

## Deskripsi

MANGROVE-FIT adalah aplikasi web lokal berbasis Streamlit untuk membantu peneliti, pengelola pesisir, dan kelompok masyarakat menilai **kesesuaian ekologis habitat mangrove** dan menentukan **prioritas verifikasi dan strategi pemulihan**. Aplikasi ini **tidak** menggantikan survei lapangan, izin kawasan, atau konsultasi ahli.

**Apa yang bisa dilakukan:**
- Jelajahi peta kawasan pesisir dengan zona kandidat
- Impor data titik (CSV) atau polygon (GeoJSON)
- Jalankan screening ekologis & legal berbasis aturan transparan
- Bandingkan beberapa zona dan susun urutan survei
- Ekspor hasil ke CSV, GeoJSON, HTML, atau Markdown

**Apa yang belum tersedia (MVP):**
- Prediksi XGBoost (menunggu dataset berlabel terverifikasi)
- Penjelasan SHAP
- Integrasi Google Earth Engine / Sentinel-2 otomatis

---

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
cd e:\ITRUSH\mangrove-fit-bismillah

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

### 1. Mode Demo (bawaan)
- Buka aplikasi → sidebar menunjukkan **"Demo"**
- Tiga zona sintetis sudah tersedia dengan watermark **SIMULASI — BUKAN DATA LAPANGAN**
- Jelajahi peta, lihat analisis, dan ekspor contoh laporan

### 2. Mode Analis Lokal
- Di sidebar, pilih **"Analis lokal"**
- Pergi ke halaman **Data & model** → tab **Impor & template**
- Unduh template CSV kosong, isi data lapangan kamu, lalu upload kembali

### 3. Import Data

**Format CSV** (untuk titik/sampel):
```
zone_id, zone_name, longitude, latitude, landcover_type, legal_status, ...
```
Kolom kosong = `null` (bukan 0). Lihat [`data/demo/template_kosong.csv`](data/demo/template_kosong.csv) untuk template lengkap.

**Format GeoJSON** (untuk polygon):
- CRS: EPSG:4326 `[longitude, latitude]`
- Tipe geometri: Point atau Polygon
- Lihat [`data/demo/zona_simulasi.geojson`](data/demo/zona_simulasi.geojson) untuk contoh

### 4. Ekspor Hasil
Dari halaman **Analisis lokasi** atau **Perbandingan zona**, klik tombol ekspor:
- **CSV** — data tabular + metadata sumber
- **GeoJSON** — geometri + hasil screening
- **HTML** — laporan ringkas siap cetak
- **Markdown** — teks terformat

---

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
│   └── 6_Metodologi.py
├── mangrove_fit/             # Modul backend Python
├── config/
│   ├── rules.yaml            # Aturan screening ekologis (dapat diedit)
│   └── demo_mode.yaml
├── data/
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
| Database error | Hapus `data/app.db` lalu restart aplikasi |
| Data demo muncul di mode lokal | Normal — klik "Analis lokal" di sidebar, tambah zona baru |

---

## Menjalankan Tests

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

Hasil: 51 test lulus pada versi MVP 0.1.

---

## Keterbatasan Penting

- **Kesesuaian habitat ≠ keberhasilan rehabilitasi.** Hasil screening hanya arah kajian awal.
- Semua zona bawaan adalah **data sintetis** — koordinat dan nilai tidak mewakili lokasi nyata.
- XGBoost dan SHAP **belum aktif** — menunggu dataset berlabel terverifikasi.
- Basemap memerlukan internet. Data dan analisis tetap berjalan offline.
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

Dataset dan sumber data yang relevan didokumentasikan di [`docs/spesifikasi_sumber.md`](docs/spesifikasi_sumber.md) dan [`data/DATA_STATUS.md`](data/DATA_STATUS.md). Aplikasi **tidak mengklaim** telah mengunduh atau menggunakan dataset tersebut tanpa verifikasi tertulis.

---

## Lisensi & Atribusi

- Basemap: © OpenStreetMap contributors
- Aplikasi: dikembangkan sebagai proof of concept untuk IT RUSH 2026
- Data demo: sintetis — bukan data lapangan atau hasil penelitian nyata
