# Arsitektur Sistem — MANGROVE-FIT

> Versi MVP 0.1 · Deployment: lokal satu pengguna di laptop Windows

---

## Diagram Alur Data

```
Pengguna
   |
   v
[Streamlit UI — app.py + pages/]
   |
   +--→ [ui_components.py]  ← tampilan, form, peta, interaksi
   |
   +--→ [data_io.py]        ← parsing & validasi CSV/GeoJSON upload
   |
   +--→ [services.py]       ← orchestrator analisis utama
         |
         +--→ [schemas.py]           ← validasi skema, rentang fisik, null
         +--→ [screening.py]         ← aturan ekologis & legal (rules.yaml)
         +--→ [recommendations.py]   ← mesin rekomendasi berbasis aturan
         +--→ [preprocessing.py]     ← kelengkapan 7 parameter inti
         +--→ [geospatial.py]        ← validasi Shapely, luas UTM/LAEA
         +--→ [prioritization.py]    ← urutan survei
         +--→ [model_service.py]     ← status model (NO_MODEL_AVAILABLE)
         +--→ [explain_service.py]   ← SHAP placeholder
         +--→ [report_service.py]    ← ekspor CSV/GeoJSON/HTML/Markdown
         |
         v
   [database.py ← SQLite: data/app.db]
         |
         +-- tabel zones
         +-- tabel observations
         +-- tabel datasets
         +-- tabel analyses (snapshot)
         +-- tabel reviews
         +-- tabel model_registry (placeholder)
```

---

## Komponen UI (pages/)

| Halaman | File | Fungsi utama |
|---|---|---|
| Beranda | `1_Beranda.py` → `home()` | Ringkasan zona, status sistem, navigasi cepat |
| Peta kawasan | `2_Peta.py` → `map_page()` | Folium interaktif, klik polygon, peta skematis offline |
| Analisis lokasi | `3_Analisis.py` → `analysis_page()` | 5 tab: data, screening, XGBoost*, SHAP*, rekomendasi |
| Perbandingan zona | `4_Perbandingan.py` → `comparison_page()` | Tabel, grafik, urutan survei, ekspor |
| Data & model | `5_Data_Model.py` → `data_page()` | Import, form zona, dataset tersimpan, status model |
| Metodologi | `6_Metodologi.py` → `methodology_page()` | Aturan YAML, parameter, keterbatasan |

---

## Modul Backend (mangrove_fit/)

| Modul | Tanggung Jawab |
|---|---|
| `config.py` | Konstanta global, path, `load_rules()` dengan checksum |
| `schemas.py` | `PARAMETERS` dict, `normalize_zone()`, `ValidationError` |
| `database.py` | CRUD SQLite: `save_zones()`, `list_zones()`, `save_analysis()`, `get_reviews()` |
| `data_io.py` | `parse_upload()` — CSV dan GeoJSON; batas ukuran/geometri |
| `geospatial.py` | `area_ha()` via UTM/LAEA, `center()`, validasi Shapely |
| `preprocessing.py` | Hitung kelengkapan 7 parameter inti (bukan imputasi) |
| `screening.py` | `screen_zone()` → status ELIGIBLE/NEEDS_REVIEW/EXCLUDED + alasan |
| `recommendations.py` | `recommend()` → tindakan awal, langkah berikutnya |
| `services.py` | `analyse_zone()` — orchestrator: screening + kelengkapan + rekomendasi + snapshot |
| `prioritization.py` | `survey_sort()` — urutan survei tanpa skor program |
| `model_service.py` | Status `NO_MODEL_AVAILABLE`; validator fitur untuk model kelak |
| `explain_service.py` | SHAP placeholder; aktif setelah model tervalidasi tersedia |
| `report_service.py` | `export_csv()`, `export_geojson()`, `export_markdown()`, `export_html()` |
| `ui_components.py` | Semua fungsi halaman UI; `apply_style()`, `watermark()`, `scope()` |

---

## Skema Database SQLite

### Tabel `zones`
Menyimpan zona sebagai JSON blob (`payload JSON`) + flag `is_demo` + scope (demo/local).

### Tabel `observations`
Observasi ternormalisasi per parameter per zona: value, unit, source, date, quality_flag, method, datum.

### Tabel `datasets`
Metadata dataset yang diimpor: nama, versi, URL, lisensi, tanggal impor, checksum.

### Tabel `analyses`
Snapshot hasil analisis: `zone_id`, `timestamp`, `result_json` (berisi feature_snapshot + screening + completeness + recommendations + rules_checksum).

### Tabel `reviews`
Catatan verifikator: `analysis_id`, `reviewer`, `notes`, `decision`, `reviewed_at`.

### Tabel `model_registry`
Placeholder model: belum ada entri aktif di MVP 0.1.

---

## Alur Penyimpanan Data

```
Upload CSV/GeoJSON
      |
      v
parse_upload() → validasi skema, geometri, satuan, rentang
      |
      +-- Error → tampilkan pesan → STOP (tidak ada data tersimpan)
      |
      v
save_zones(zones, replace=False) ← transaksi atomik SQLite
      |
      +-- Berhasil → konfirmasi pengguna
      +-- Gagal → rollback → tidak ada zona parsial tersimpan
```

---

## Alur Analisis

```
zone = list_zones(scope)[selected]
      |
      v
result_for(zone):
  1. Cek cache: snapshot masih cocok + checksum rules.yaml sama?
     → Ya: pakai hasil tersimpan
     → Tidak: hitung ulang
  2. analyse_zone(zone):
     - preprocessing: hitung kelengkapan 7 parameter
     - screening: cek tutupan, legal, parameter
     - recommendations: pilih tindakan awal
     - buat result dict dengan timestamp UTC
      |
      v
Tampilkan di UI → bisa disimpan (save_analysis) → bisa ekspor
```

---

## Mekanisme Mode Demo vs Lokal

```python
def scope():
    return 'demo' if st.session_state.get('workspace_mode') == 'Demo' else 'local'
```

- Scope `demo`: data baca saja dari seed; tidak bisa dimodifikasi
- Scope `local`: data pengguna di SQLite; bisa tambah/edit/simpan analisis

Watermark tampil otomatis jika scope `demo` atau ada zona dengan `is_demo=True` di mode lokal.

---

## Keamanan Dasar (MVP Lokal)

- Upload dibatasi: 10 MB, 1.000 zona, 50.000 vertex per polygon
- Konten CSV/YAML tidak dieksekusi sebagai kode
- Formula spreadsheet dicegah dengan awalan apostrof di ekspor CSV
- Path traversal dicegah di nama file upload
- Pickle/joblib tidak diterima dari pengguna (model hanya dari admin)
- Tidak ada autentikasi — hanya untuk laptop lokal, bound ke `localhost`

---

## Batas Deployment

- **Satu pengguna** — tidak ada multiuser atau sinkronisasi
- **Localhost saja** — jangan ekspos ke internet sebagai aplikasi produksi
- **SQLite** — tidak untuk produksi berskala besar; migrasi ke PostGIS untuk penggunaan luas
- Basemap memerlukan internet — data dan analisis tetap berjalan offline

