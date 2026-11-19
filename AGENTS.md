# AGENTS.md — Aturan Workspace MANGROVE-FIT

> Dibaca oleh AI coding agent (Google Antigravity, Gemini, Copilot, dll.) sebelum mengerjakan tugas di repositori ini.

---

## Identitas Proyek

**Nama:** MANGROVE-FIT  
**Tujuan:** Prioritas survei rehabilitasi mangrove menggunakan indikator kondisi dan K-Means. Ruang survei memakai screening ekologis dan legal. XGBoost dan SHAP tersedia untuk eksperimen riset.
**Wilayah studi utama:** Kabupaten Sidoarjo dan Kota Surabaya, Jawa Timur. Demak berada di ruang arsip.
**Entry point:** `streamlit run app.py`  
**Database:** SQLite di `data/app.db`

---

## Aturan Wajib

### 1. Jangan Mengarang Data

- **DILARANG** membuat nilai salinitas, hidroperiode, koordinat survei, persentase survival, atau skor akurasi yang seolah-olah nyata
- Dataset sintetis HANYA di folder `data/demo/`, diberi nama `DEMO_SYNTHETIC_*`
- Kolom kosong = `null`; jangan isi dengan 0 atau rata-rata tanpa peringatan

### 2. Jangan Mengklaim AI Aktif

- Model XGBoost dan SHAP **belum tersedia** di MVP ini
- Tab Model XGBoost dan tab SHAP harus menampilkan `NO_MODEL_AVAILABLE`
- Jangan menambahkan skor, probabilitas, atau plot SHAP palsu

### 3. Pisahkan Data Demo dan Data Nyata

- Scope `demo` = baca saja; tidak bisa dimodifikasi pengguna
- Scope `local` = data pengguna di SQLite lokal
- Jangan mencampur keduanya tanpa watermark

### 4. Status Implementasi

- Setiap perubahan fitur besar → perbarui `docs/IMPLEMENTATION_STATUS.md`
- Gunakan status: **SELESAI / PARSIAL / TERHAMBAT / BELUM MULAI**
- Jangan mengklaim fitur berjalan sebelum diuji

---

## Struktur Penting

```
app.py                     # Entry point — jangan ubah page_config
pages/                     # Halaman Streamlit (1_Beranda hingga 6_Metodologi)
mangrove_fit/              # Semua logika backend (services, bukan halaman)
  ├── config.py            # Konstanta, path, load_rules()
  ├── schemas.py           # Validasi parameter, PARAMETERS dict
  ├── database.py          # SQLite CRUD
  ├── screening.py         # Aturan ekologis/legal
  ├── recommendations.py   # Mesin rekomendasi
  ├── services.py          # Fungsi analisis utama
  └── ui_components.py     # Fungsi halaman UI
config/rules.yaml          # Aturan screening — checksum direkam per analisis
data/demo/                 # Data sintetis saja
docs/                      # Dokumentasi teknis
tests/                     # Unit tests (jalankan: pytest tests -v)
```

---

## Konvensi Koding

- Bahasa UI: **Bahasa Indonesia**
- Bahasa kode: **Python 3.11**, type hints dianjurkan
- Format: ikuti pola yang ada (tidak ada black/isort dipaksakan)
- Error messages untuk pengguna: Bahasa Indonesia, jelas, dan actionable
- Log/komentar teknis: boleh Bahasa Inggris

### Skema observasi (jangan ubah tanpa migrasi DB)

Setiap parameter dalam `PARAMETERS` (di `schemas.py`) menyimpan:
```python
{
    "value": nilai_atau_None,
    "unit": "satuan",
    "source": "sumber_data_atau_None",
    "date": "YYYY-MM-DD_atau_None",
    "quality_flag": "measured|modelled|estimated|demo|missing",
    "method": "metode_pengukuran_atau_None",
    "datum": "datum_vertikal_atau_None"
}
```

---

## Yang Boleh Diubah Agent

| Komponen | Boleh diubah | Catatan |
|---|---|---|
| `pages/*.py` | ✅ | Ikuti pola `header()`, `watermark()`, `scope()` |
| `mangrove_fit/*.py` | ✅ | Jaga kompatibilitas skema DB |
| `config/rules.yaml` | ✅ | Checksum otomatis berubah; snapshot lama tidak terbatalkan |
| `tests/*.py` | ✅ | Tambah test, jangan hapus yang sudah ada |
| `docs/*.md` | ✅ | Perbarui `IMPLEMENTATION_STATUS.md` setelah perubahan besar |
| `data/demo/*.csv` | ⚠️ | Pertahankan watermark sintetis |
| `data/app.db` | ❌ | Jangan modifikasi langsung; gunakan `database.py` |
| `mangrove_fit/schemas.py` PARAMETERS | ⚠️ | Perubahan butuh migrasi DB |

---

## Menjalankan Tests

```powershell
# Aktifkan venv dulu
.venv\Scripts\Activate.ps1

# Jalankan semua test
python -m pytest tests -v

# Jalankan satu file
python -m pytest tests/test_screening.py -v
```

Target: semua test lulus sebelum commit.

---

## Menambahkan Fitur Baru

1. Tambah logika di `mangrove_fit/` (bukan di `pages/`)
2. Tambah unit test di `tests/`
3. Perbarui `docs/IMPLEMENTATION_STATUS.md`
4. Jika mengubah skema DB: buat migrasi dan dokumentasikan
5. Jika menambah parameter: perbarui `schemas.py`, `data_dictionary.md`

---

## Larangan Keras

- ❌ Jangan bypass validasi geometri atau skema
- ❌ Jangan eksekusi kode dari konten CSV/YAML pengguna
- ❌ Jangan aktifkan model XGBoost tanpa artefak dan manifest kelayakan
- ❌ Jangan hapus watermark dari ekspor data demo
- ❌ Jangan buat koordinat zona dari nama desa (tanpa data survei)
- ❌ Jangan iklankan akurasi atau probabilitas yang belum diuji
