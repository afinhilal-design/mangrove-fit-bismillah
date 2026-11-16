# Status Implementasi — MANGROVE-FIT

> **Diperbarui:** 16 November 2026  
> **Versi:** MVP 0.1  
> **Lingkungan uji:** Windows 11, Python 3.11.9, Streamlit 1.50.0

---

## Legenda Status

| Status | Arti |
|---|---|
| ✅ SELESAI | Diimplementasikan dan lulus pengujian otomatis |
| ⚠️ PARSIAL | Tersedia sebagian; ada bagian yang belum lengkap |
| ❌ TERHAMBAT | Belum bisa dilanjutkan karena ketergantungan eksternal |
| 🔲 BELUM MULAI | Direncanakan tetapi belum dikerjakan |

---

## Sprint 1 — Kerangka dan Peta

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Inisialisasi repositori & environment | ✅ SELESAI | `requirements.txt` terkunci, `.gitignore`, `.env.example` tersedia |
| Streamlit multipage + tema | ✅ SELESAI | 6 halaman berjalan; CSS kustom di `apply_style()` |
| Peta interaktif Folium | ✅ SELESAI | `streamlit-folium` + klik polygon memperbarui panel kanan |
| Peta skematis offline (fallback) | ✅ SELESAI | SVG inline tanpa dependensi internet; toggle di halaman Peta |
| Import CSV titik | ✅ SELESAI | Validasi skema, geometri, satuan, rentang; test `test_import.py` |
| Import GeoJSON polygon | ✅ SELESAI | Validasi geometri Shapely; test `test_geospatial.py` |
| Tiga zona demo sintetis | ✅ SELESAI | `scripts/seed_demo.py`; watermark SIMULASI |
| Penyimpanan SQLite | ✅ SELESAI | `mangrove_fit/database.py`; impor atomik |

---

## Sprint 2 — Screening dan Keputusan

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Screening ekologis & legal | ✅ SELESAI | `screening.py`; aturan dari `config/rules.yaml`; checksum aturan |
| Form input data per parameter | ✅ SELESAI | `ui_components.py::zone_form()`; null ≠ 0 dipertahankan |
| Metadata per observasi (sumber, tanggal, kualitas) | ✅ SELESAI | Skema di `schemas.py`; `quality_flag`, `method`, `datum` |
| Rule-based recommendation engine | ✅ SELESAI | `recommendations.py`; alasan transparan; test `test_recommendations.py` |
| Halaman Analisis lokasi (5 tab) | ✅ SELESAI | Tab: Data input, Screening, XGBoost*, SHAP*, Rekomendasi |
| Halaman Perbandingan zona | ✅ SELESAI | Tabel, grafik bar, filter status, urutan survei |
| Ekspor CSV, GeoJSON, HTML, Markdown | ✅ SELESAI | `report_service.py`; metadata mode/versi/timestamp terbawa |
| Watermark demo pada ekspor | ✅ SELESAI | SIMULASI tercantum pada semua ekspor demo |
| Unit tests screening | ✅ SELESAI | `tests/test_screening.py` — lulus |
| Unit tests database | ✅ SELESAI | `tests/test_database.py` — lulus |
| Unit tests ekspor | ✅ SELESAI | `tests/test_export.py` — lulus |
| Unit tests UI (AppTest) | ✅ SELESAI | `tests/test_ui.py` — lulus |

---

## Sprint 3 — Model XGBoost dan SHAP

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Audit ketersediaan dataset berlabel | ❌ TERHAMBAT | Dataset D01, D02 (4TU) belum diunduh; akses manual diperlukan |
| Pipeline training XGBoost | ⚠️ PARSIAL | `model_service.py` berisi validator & status; inferensi belum terhubung |
| Inferensi model di UI | ❌ TERHAMBAT | Menunggu artefak model terverifikasi |
| Interpretasi SHAP | ❌ TERHAMBAT | `explain_service.py` berisi placeholder; menunggu model valid |
| Notebook training | 🔲 BELUM MULAI | Direncanakan di `notebooks/train_xgboost.ipynb` |
| Model registry | ⚠️ PARSIAL | Tabel `model_registry` ada di DB; belum ada artefak model |
| Validasi out-of-domain | 🔲 BELUM MULAI | Menunggu data latih dan domain pelatihan terdefinisi |

---

## Sprint 4 — Perapian dan Handoff

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Responsif laptop | ✅ SELESAI | CSS `max-width: 1500px`; layout kolom adaptif |
| Error state & empty state | ✅ SELESAI | `empty_state()`, pesan validasi, fallback offline |
| Halaman Metodologi & sumber | ✅ SELESAI | `6_Metodologi.py`; aturan YAML dapat diperiksa |
| README.md lengkap | ✅ SELESAI | Instalasi Windows, cara run, import, troubleshooting |
| Screenshot halaman utama | ✅ SELESAI | `docs/screenshots/` (7 gambar) |
| Dokumentasi teknis | ⚠️ PARSIAL | `architecture.md`, `data_dictionary.md`, `limitations.md` ada; beberapa baru dilengkapi |
| `IMPLEMENTATION_STATUS.md` | ✅ SELESAI | Dokumen ini |
| `TARGET_DEFINITION.md` | ✅ SELESAI | `docs/TARGET_DEFINITION.md` |
| `USER_GUIDE.md` | ✅ SELESAI | `docs/USER_GUIDE.md` |
| `MODEL_CARD.md` | ⚠️ PARSIAL | Placeholder; akan diisi setelah model dilatih |
| `DATA_STATUS.md` | ✅ SELESAI | `data/DATA_STATUS.md` |
| `DATA_AUDIT.md` | ⚠️ PARSIAL | Status akses tercatat; audit file mentah belum bisa dilakukan |

---

## Acceptance Test — Ringkasan MVP 0.1

| ID | Skenario | Status |
|---|---|---|
| AT-01 | Jalankan dari README pada laptop baru | ✅ Lulus (Windows 11 + Python 3.11) |
| AT-02 | Pilih zona demo → metadata tampil | ✅ Lulus |
| AT-03 | Zona dengan data kurang → NEEDS_REVIEW | ✅ Lulus |
| AT-04 | Upload CSV template sah | ✅ Lulus |
| AT-05 | CSV dengan latitude 120 → ditolak | ✅ Lulus |
| AT-06 | GeoJSON self-intersecting → ditolak | ✅ Lulus |
| AT-07 | Salinitas kosong → null tersimpan | ✅ Lulus |
| AT-08 | Nonhabitat/larangan legal → tidak ada "tanam" | ✅ Lulus |
| AT-09 | Model tidak ada → NO_MODEL_AVAILABLE | ✅ Lulus |
| AT-10 | Fitur model salah → MISSING_REQUIRED_FEATURES | ⚠️ Sebagian (validator diuji; model nyata belum ada) |
| AT-11 | SHAP model nyata | ❌ Belum berlaku (menunggu model) |
| AT-12 | Bandingkan 3 zona | ✅ Lulus |
| AT-13 | Ekspor CSV/GeoJSON dengan metadata | ✅ Lulus |
| AT-14 | Hitung luas polygon (hektare) | ✅ Lulus |
| AT-15 | Ganti zona → state tidak tertukar | ✅ Lulus |
| AT-16 | Internet mati → data lokal tetap tampil | ⚠️ Sebagian (jalur offline diuji; pemutusan fisik belum) |
| AT-17 | File terlalu besar/format salah → ditolak | ✅ Lulus |
| AT-18 | Ekspor demo → ada watermark SIMULASI | ✅ Lulus |

**Hasil: 14 dari 18 kriteria LULUS penuh · 3 PARSIAL · 1 menunggu data**

---

## Pekerjaan Berikutnya

1. **Prioritas:** Unduh dataset D02 (`To Plant or Not to Plant`, 4TU) secara manual → audit kolom → tentukan target AI
2. Buat `data/manifests/D02.json` setelah berhasil akses
3. Susun pipeline training di `notebooks/train_xgboost.ipynb`
4. Aktifkan inferensi model di `model_service.py` setelah artefak terverifikasi
5. Hubungkan SHAP ke tab Penjelasan SHAP di halaman Analisis

---

> Dokumen ini hanya mencatat status perangkat lunak, bukan validasi ekologis, akurasi model, atau keberhasilan rehabilitasi lapangan.
