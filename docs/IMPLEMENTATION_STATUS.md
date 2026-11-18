# Status Implementasi — MANGROVE-FIT

> **Diperbarui:** 19 November 2026 (WIB)  
> **Versi:** MVP 0.1  
> **Lingkungan uji:** Windows 11, Python 3.11.9, Streamlit 1.50.0

---

## Integrasi skenario Demak A–C — 19 November 2026

**SELESAI — Perbandingan skenario:** kartu skor historis untuk A–C, tabel ringkas dan kualitas “Data historis · skenario”, detail alasan screening terpisah, grafik hanya menawarkan parameter tersedia, serta unduhan skor berwatermark. Tidak ada parameter random, kelas habitat atau status legal buatan. 15 tes skenario/UI lulus.

**SELESAI — Skor dan SHAP riset per titik:** Analisis lokasi menampilkan prediksi `presence_expanded` untuk baris historis `sea_1_1`, `sea_14_2`, dan `pond_12_1` yang sesuai dengan A–C. Tidak menggunakan model survival Q4 atau mengganti status operasional. Label tampilan kualitas menjadi “Data historis · skenario”, metode pengolahan spesifik per kolom sumber, angka dibulatkan empat desimal tanpa mengubah data. Nilai tidak tersedia tetap null. **93 tes lulus**, termasuk kecocokan ID historis, validasi zona, skor, SHAP, dan metadata ekspor.

**SELESAI — Pemetaan seluruh nilai sumber tersedia:** A 9 parameter, B 6, C 7. Parameter yang kosong pada sumber tetap null; tampilan mengutamakan nilai tersedia dan menyediakan daftar kekurangan terpisah. Satuan mengikuti pemetaan proyek dengan catatan perlu konfirmasi metadata. 14 tes skenario dan UI lulus untuk pembaruan ini.

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Ruang kerja Skenario Demak A–C | **SELESAI** | Pilihan bawaan sesi baru; overlay baca-saja, terpisah dari Demo sintetis dan Analis lokal |
| Peta, Analisis lokasi, Perbandingan | **SELESAI** | Membaca tiga titik dari konfigurasi skenario dan memvalidasi checksum, koordinat, nilai sumber serta skema/geometri |
| Provenance dan ekspor | **SELESAI** | Tanggal 19 November sebagai tanggal skenario; tanggal survei asli tetap null; watermark dan metadata tersertakan dalam ekspor |
| Isolasi data | **SELESAI** | Tidak ada penambahan zona ke SQLite; tidak ada formulir simpan/edit pada skenario; nilai inti yang tidak tersedia tetap null |

Panduan penggunaan dan verifikasi: [SCENARIO_UI_GUIDE.md](SCENARIO_UI_GUIDE.md).

## Integrasi aplikasi riset — 19 November 2026

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Menu XGBoost & SHAP · Riset | **SELESAI** | Empat model, metrik validasi, baseline dan SHAP global terhubung ke artefak lokal |
| Demonstrasi prediksi & SHAP lokal | **SELESAI** | Pilih observasi historis atau isi simulasi manual; skor, kontribusi, uji aditivitas dan unduhan JSON berwatermark |
| Validasi integrasi | **SELESAI** | Checksum model/data, skema encoder, kategori dan domain input; 88 tes lulus termasuk Streamlit AppTest |
| Model operasional zona | **PARSIAL** | Tetap NO_MODEL_AVAILABLE sampai persetujuan; mode riset tidak mengubah DB atau melewati screening |

Panduan: [RESEARCH_UI_GUIDE.md](RESEARCH_UI_GUIDE.md).

## Pembaruan audit seluruh data dan eksperimen diperluas — 19 November 2026

Bagian ini menggantikan status eksperimen terbatas sebelumnya, tanpa mengubah hasil historisnya.

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Audit semua sumber | **SELESAI** | 97 berkas, 178 tabel/sheet; checksum, duplikasi, missing values, masalah koordinat dan peran setiap sumber tercatat |
| Pemanfaatan seluruh sumber untuk training langsung | **PARSIAL** | 5 berkas masuk 4 tugas berlabel; sisanya untuk konteks/audit atau menunggu pemetaan/definisi target, tidak digabung paksa |
| XGBoost riset diperluas | **SELESAI** | Fitur numerik/kategori, NaN native, nested GroupKFold; Q4 BA 0,6364 pada threshold 0,5 dibanding 0,4914 model satu fitur pada fold sama |
| Validasi koordinat keberadaan semai | **SELESAI** | Transek yang berbagi koordinat menjadi 4 komponen; BA 0,4883, model masih lemah |
| SHAP out-of-fold | **SELESAI** | Kontribusi pada test setiap outer fold, agregasi kategori ke fitur asal, aditivitas teruji |
| Aktivasi aplikasi | **PARSIAL** | Empat model `RESEARCH_ONLY`, belum tervalidasi eksternal; aplikasi tetap `NO_MODEL_AVAILABLE` |
| Tes | **SELESAI** | 82 passed |

Rincian: [TRAINING_ALL_DATA.md](TRAINING_ALL_DATA.md). Artefak: `models/experiments/all_data_v2/`.

## Pembaruan training survival Q4 — 19 November 2026

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Kohort survival bulan 0 ke 16 | **SELESAI** | 397 bibit/20 blok; ID ambigu J4 dan bibit sudah mati P0 dikeluarkan; tanpa imputasi |
| Training XGBoost dan SHAP Q4 | **SELESAI** | Satu fitur sedimen awal; artefak `models/experiments/q4_survival_baseline/`; aditivitas SHAP lulus |
| Kelayakan model Q4 | **TERHAMBAT** | Test BA 0,5; CV BA 0,4914; tidak melampaui baseline; kandidat tidak diaktifkan |
| Pengujian | **SELESAI** | 76 passed, mencakup fitur baseline, horizon tetap, ID ambigu, NA dan label |

Rincian: [TRAINING_Q4_SURVIVAL.md](TRAINING_Q4_SURVIVAL.md). Data historis dipertahankan; asumsi kondisi saat ini hanya skenario esai. Pembaruan ini menggantikan status Q4 BELUM MULAI dalam catatan sebelumnya di bawah.

## Pembaruan training datamangroveit — 19 November 2026

Bagian ini memperbarui catatan historis di bawah mengenai ketersediaan data/model.

| Komponen | Status | Bukti / Catatan |
|---|---|---|
| Training XGBoost data nyata | **SELESAI** | Kandidat `cand-20261118-bcc114bb`, target keberadaan semai alami; 109 observasi lengkap dari sea-site + tambak, 21 transek. Artefak di `models/experiments/datamangroveit_presence/` |
| Evaluasi kandidat | **SELESAI** | Test BA 0,6140, F1 0,4000, AP 0,6012; leave-one-transect-out BA 0,5407. AP diperbaiki untuk skor seri; CV memakai 100 rounds tetap |
| Ekspor SHAP kandidat | **SELESAI** | Exact TreeSHAP native XGBoost, CSV per observasi dan importance test; aditivitas lulus, galat maksimum 2,3842e-7 |
| Kelayakan operasional | **PARSIAL** | `PENDING_REVIEW`; validation BA 0,4706 dan CV lemah. Belum ada peninjauan ahli/kalibrasi. Status aplikasi terverifikasi `NO_MODEL_AVAILABLE` |
| Training survival Q4 | **BELUM MULAI** | Memerlukan fitur awal, horizon target konsisten, dan koreksi agregasi NA; tidak digabung dengan target keberadaan semai |
| Pengujian kode | **SELESAI** | `python -m pytest tests -q`: 73 passed; mencakup AP dengan ties, ekspor SHAP, checksum, dan gerbang model |

Rincian data, keterbatasan, metrik dan reproduksi: [TRAINING_DATAMANGROVEIT.md](TRAINING_DATAMANGROVEIT.md).

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
| Audit ketersediaan dataset berlabel | ⚠️ PARSIAL | D01 sea-site diaudit & dikonversi (`dataset_d01.py`, `scripts/import_sea_site.py`, manifest SHA-256). D02 belum diunduh |
| Model kandidat D01 | ⚠️ PARSIAL | `cand-20261117-ef0e4a75` PENDING_REVIEW; CV antar-transek BA 0.5, PR-AUC 0.4367 vs 0.2222. Ditolak gerbang persetujuan (tidak melampaui baseline) → UI tetap NO_MODEL_AVAILABLE |
| Parameter baru pH, redoks, kemiringan | ✅ SELESAI | `schemas.py` + migrasi baca `upgrade_observations`; diuji `tests/test_dataset_d01.py` |
| Pipeline training XGBoost | ✅ SELESAI (kode) | `training.py` + `scripts/train_model.py`: split blok spasial, tanpa imputasi, early stopping, metrik BA/F1/PR-AUC/Brier vs baseline; diuji `tests/test_training.py` dengan data acak sementara |
| Inferensi model di UI | ⚠️ PARSIAL | Tab Model XGBoost & Analisis terhubung ke `predict_zone`; tampil hanya bila model APPROVED ada. Belum ada model nyata → tetap NO_MODEL_AVAILABLE |
| Interpretasi SHAP | ⚠️ PARSIAL | TreeSHAP XGBoost + uji aditivitas + cek silang `shap.TreeExplainer` (opsional); grafik di tab Penjelasan SHAP. Menunggu model nyata |
| Notebook training | 🔲 BELUM MULAI | Direncanakan di `notebooks/train_xgboost.ipynb` |
| Model registry | ⚠️ PARSIAL | Berbasis berkas: `models/candidate` → `scripts/approve_model.py` → `models/active`, arsip di `models/archive`. Tabel DB `model_registry` belum dipakai |
| Validasi out-of-domain | ✅ SELESAI (kode) | Domain = min/maks fitur data latih, ditulis ke kartu model; prediksi ditolak (OUT_OF_DOMAIN) di luar rentang |

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
3. Latih kandidat: `python scripts/train_model.py <csv> --target ... --features ... --block-col ...`
4. Peninjau ahli memeriksa `models/candidate/model_card.json`, lalu `python scripts/approve_model.py --reviewer ...`
5. Uji UI dengan model nyata (AT-10, AT-11) sebelum mengubah status menjadi SELESAI

---

> Dokumen ini hanya mencatat status perangkat lunak, bukan validasi ekologis, akurasi model, atau keberhasilan rehabilitasi lapangan.
