# Deployment — MANGROVE-FIT

> Target: laptop lokal Windows 10/11 · Python 3.11/3.12 · Satu pengguna

---

## Cara Menjalankan (Windows)

### Metode 1 — Batch File (Disarankan)

```
1. Klik dua kali: 01_INSTALL_WINDOWS.bat    (sekali saja, saat pertama)
2. Klik dua kali: 02_JALANKAN_WINDOWS.bat   (setiap kali ingin membuka)
```

Browser akan terbuka otomatis di `http://localhost:8501`.

### Metode 2 — PowerShell Manual

```powershell
# Masuk ke folder proyek
cd e:\ITRUSH\mangrove-fit-bismillah

# Aktifkan virtual environment
.venv\Scripts\Activate.ps1

# (Pertama kali) Install dependensi
pip install -r requirements.txt

# Jalankan aplikasi
streamlit run app.py
```

### Menghentikan Aplikasi

Tekan `Ctrl+C` di jendela PowerShell/Command Prompt, atau tutup jendela terminal.

---

## Port dan Akses

- Server terikat ke `localhost:8501` secara default
- Hanya bisa diakses dari laptop yang sama
- Jika port 8501 sudah dipakai: `streamlit run app.py --server.port 8502`

> ⚠️ Jangan mengekspos server ini ke internet (tidak ada autentikasi, HTTPS, atau keamanan produksi).

---

## Variabel Lingkungan (.env)

Salin `.env.example` menjadi `.env` dan sesuaikan jika perlu:

```dotenv
APP_MODE=demo              # demo atau local
DATABASE_URL=sqlite:///data/app.db
MAX_UPLOAD_MB=10
MAX_FEATURES=1000
# Opsional (fase lanjutan):
GEE_PROJECT_ID=
MODEL_ARTIFACT_PATH=
```

File `.env` dibaca otomatis oleh `mangrove_fit/config.py`. Jangan commit file `.env` ke repositori.

---

## Struktur Data Lokal

```
data/
├── app.db          ← Database SQLite (dibuat otomatis saat startup)
├── demo/           ← Data sintetis bawaan (jangan hapus)
│   ├── template_kosong.csv
│   ├── titik_simulasi.csv
│   └── zona_simulasi.geojson
├── raw/            ← Dataset mentah yang diunduh manual (gitignored)
└── processed/      ← Data yang sudah diolah (gitignored)
```

---

## Backup Data Pengguna

Data pengguna tersimpan di `data/app.db`. Cara backup:

1. **Tutup aplikasi** (Ctrl+C)
2. Salin `data/app.db` ke lokasi lain
3. Atau gunakan fitur "Cadangkan seluruh zona sebagai GeoJSON" di halaman Data & model

Jangan memindahkan atau membuka `app.db` dengan editor lain saat aplikasi berjalan.

---

## Distribusi ke Komputer Lain

1. Compress seluruh folder proyek menjadi ZIP
2. Pindahkan ke komputer tujuan
3. Pastikan Python 3.11/3.12 sudah terinstall
4. Jalankan `01_INSTALL_WINDOWS.bat` untuk install ulang dependensi
5. Data pengguna (`app.db`) ikut terbawa jika folder di-copy utuh

> Berbagi folder bukan berarti aplikasi multiuser — satu instance untuk satu pengguna.

---

## Troubleshooting

| Masalah | Kemungkinan Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: streamlit` | Virtual env tidak aktif / belum install | Jalankan `01_INSTALL_WINDOWS.bat` lagi |
| `OSError: [Errno 10048]` | Port 8501 sudah dipakai | `streamlit run app.py --server.port 8502` |
| Peta tidak muncul | Tidak ada koneksi internet | Aktifkan "Peta skematis offline" di halaman Peta |
| `sqlite3.OperationalError` | File DB rusak atau terkunci | Hapus `data/app.db` → restart (data hilang) |
| PowerShell: `cannot be loaded` | Eksekusi script diblokir | Jalankan: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Browser tidak terbuka | Browser default tidak dikonfigurasi | Buka manual: `http://localhost:8501` |
| Import CSV gagal semua baris | Encoding bukan UTF-8 | Simpan CSV dengan encoding UTF-8 di Excel: Save As → CSV UTF-8 |

---

## Deployment Produksi (Rencana Masa Depan)

Jika kelak ingin deploy ke server:

| Komponen | Rekomendasi |
|---|---|
| Web server | Nginx + Streamlit behind reverse proxy |
| Autentikasi | OAuth2 / SSO institusi |
| Database | Migrasi ke PostgreSQL + PostGIS |
| HTTPS | Sertifikat SSL (Let's Encrypt) |
| Backup | Automated backup DB harian |
| Model registry | MLflow atau sistem registry terpisah |
| Logging | Structured logging ke file/ELK |

> MVP ini **tidak** dirancang untuk produksi. Jangan ekspos `streamlit run` langsung ke internet.

---

## Catatan Teknis

- Server terikat ke `localhost` melalui launcher — aman dari akses jaringan eksternal
- SQLite tidak mendukung concurrent write dari banyak proses
- Jangan jalankan dua instance aplikasi pada waktu bersamaan dengan DB yang sama
- Mode Demo dan Analis lokal **bukan** mekanisme autentikasi atau kontrol akses keamanan

