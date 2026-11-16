# MANGROVE-FIT — MASTER IMPLEMENTATION SPECIFICATION FOR GOOGLE ANTIGRAVITY

> **STATUS:** Instruksi kerja untuk membangun aplikasi (developer handoff), **bukan** bukti bahwa dataset telah terunduh atau model telah dilatih.  
> **Versi:** 2.0 — 14 November 2026  
> **Bahasa UI/dokumentasi:** Bahasa Indonesia  
> **Wilayah studi awal:** kawasan pesisir **Kabupaten Demak, Jawa Tengah, Indonesia**  
> **Strategi utama:** **DATA FIRST → AUDIT → APLIKASI PETA → MODEL TERVERIFIKASI → SHAP → REKOMENDASI**  
> **Target lingkungan:** Windows 10/11, Python 3.11/3.12, Google Antigravity sebagai coding agent.

## 0. PERINTAH UTAMA KEPADA ANTIGRAVITY — BACA DULU

Anda adalah **senior Python developer, geospatial data engineer, ML engineer, dan UX engineer**. Bangun aplikasi yang **berfungsi dan dapat dijalankan secara lokal**, bukan hanya mockup atau proposal. Kerjakan dalam workspace baru `mangrove-fit/`, buat dan modifikasi source code sesuai spesifikasi ini, jalankan pengujian, lalu laporkan status sebenarnya. Jangan berhenti setelah membuat sketsa arsitektur.

**Judul resmi proyek—HARUS sama persis pada halaman Beranda, README, dan laporan:**

**MANGROVE-FIT: Aplikasi Prioritisasi Rehabilitasi Mangrove di Pesisir Pantai Berbasis XGBoost dan SHAP dengan Integrasi Data Hidrologi dan Geospasial**

**Masalah yang diselesaikan:** Pengelola pesisir perlu menilai **kesesuaian ekologis habitat mangrove**, meninjau faktor pembatas seperti hidrologi, substrat, dinamika pantai dan tutupan vegetasi, lalu menentukan **prioritas verifikasi dan strategi pemulihan**. Tidak semua wilayah pantai cocok ditanami mangrove.

**Outcome/luaran:** Aplikasi peta interaktif dan dashboard analitis yang menampilkan data terverifikasi; jika memungkinkan, model XGBoost yang dilatih pada label biologis nyata; interpretasi SHAP; rekomendasi restorasi bersyarat; ekspor laporan. Untuk tahap awal, fokus seluruh pesisir Demak sebagai **area pencarian data**. Bedono, Timbulsloko, Surodadi dan desa lain hanya dijadikan unit analisis **setelah koordinat data asli dan cakupan wilayah diverifikasi**.

### Instruksi eksekusi yang wajib ditaati

1. **Mulai dengan audit berkas dan data nyata**, baru membangun model. Unduh atau minta pengguna memasukkan dataset dari sumber resmi di §3. Jangan menyatakan data telah diunduh apabila belum.
2. Buat aplikasi **tetap dapat berjalan tanpa internet, kredensial Earth Engine, atau data lapangan**, dengan mode penjelajahan peta dan demo yang diberi label jelas. Fitur yang belum memiliki data nyata harus menampilkan **BELUM TERSEDIA**, bukan angka palsu.
3. **JANGAN mengarang** nilai salinitas, hidroperiode, koordinat survei, persentase survival, area rehabilitasi, skor akurasi, atau dataset CSV berlabel nyata.
4. Data sintetis hanya boleh di folder `data/demo/`, diberi nama `DEMO_SYNTHETIC_*`, dan memiliki watermark UI **“SIMULASI — BUKAN DATA LAPANGAN”**; tidak boleh masuk training default.
5. Pisahkan dengan jelas **(a) observasi**, **(b) hasil turunan dari satelit**, **(c) model**, dan **(d) penilaian/aturan ekologi**. **XGBoost hanya aktif jika target valid dan evaluasi memadai. SHAP hanya tampil untuk model XGBoost yang benar-benar dilatih.**
6. Kode harus modular, memiliki pengujian otomatis, dokumentasi, kesalahan yang dapat dipahami pengguna, *logging*, serta ekspor data dengan sumber dan tanggal.
7. Bila server dataset meminta login atau memblokir pengunduhan otomatis, **jangan mencoba bypass**. Buat pengunduh dengan status, instruksi unduh manual, dan pengunggah dataset ke aplikasi.
8. Setiap langkah menulis progres aktual ke `docs/IMPLEMENTATION_STATUS.md`, terdiri dari **SELESAI / PARSIAL / TERHAMBAT**, bukti pengujian, dan pekerjaan berikutnya. Jangan mengklaim fungsi beroperasi sebelum dites.
9. Pengembangan harus mendukung pemeriksaan ilmiah untuk esai IT RUSH 2026: pemanfaatan AI, dampak lingkungan dan masyarakat, sumber yang terlacak, kelayakan implementasi. Prototipe tidak diwajibkan oleh guidebook tetapi aplikasi ini dibangun sebagai **proof of concept** tambahan, bukan klaim implementasi lapangan.
10. **Prioritas keputusan:** jika ruang lingkup besar, selesaikan fase MVP benar-benar berjalan terlebih dahulu, kemudian tambah modul ilmiah; hindari aplikasi tampak lengkap tetapi fungsi inti tidak bekerja.

**Definition of Done paling utama:** pengguna menjalankan `streamlit run app.py`, melihat peta Demak, membuka katalog data, mengimpor CSV/GeoJSON valid, memeriksa mutu data, membandingkan zona, menerima rekomendasi bersyarat yang transparan, mengekspor hasil, dan melihat status model yang jujur. Jika label terverifikasi ada dan validasi lolos, model XGBoost–SHAP bisa diaktifkan. Jika tidak, sistem tetap berguna dalam mode observasi/screening tanpa prediksi AI palsu.

---

## 1. KEBIJAKAN PRODUK DAN CAKUPAN WILAYAH

### 1.1 Tujuan pengguna

- **Peneliti/analis:** menggabungkan pengamatan lapangan dan data geospasial pada satu peta serta mengaudit kecocokan antar-data.
- **Dinas/pengelola rehabilitasi:** memfilter zona prioritas survei, menilai kesiapan restorasi, dan menyimpan rekomendasi yang perlu diverifikasi.
- **Kelompok masyarakat pesisir:** memperoleh ringkasan faktor pembatas dan rencana verifikasi dengan bahasa sederhana.
- **Juri/pembaca esai:** melihat alur yang transparan dari sumber data ke hasil, termasuk keterbatasan penelitian.

### 1.2 Batas geografis

- AOI awal adalah polygon administrasi **Kabupaten Demak** dari data batas berizin/resmi (misalnya BIG/BPS/administrasi pemerintah) dan *coastal mask* yang relevan. **Jangan membuat polygon administratif karangan**.
- Peta boleh diawali tampilan terpusat pada Demak menggunakan koordinat *map view* umum; titik penelitian **tidak boleh dibuat hanya dari nama desa**.
- Pengguna dapat mengimpor polygon AOI, titik stasiun penelitian, zona kandidat, dan batas desa dalam GeoJSON/GeoPackage/CSV yang telah diaudit.
- CRS penyimpanan/peta publik: `EPSG:4326`; untuk luas, jarak dan buffer Demak gunakan CRS metrik yang sesuai, contoh `EPSG:32749` (UTM zona 49S), dengan pencatatan konversi. Elevasi pasang-surut memerlukan pengecekan **datum vertikal** yang tidak diselesaikan hanya dengan reproyeksi horizontal.
- Jika hanya subset wilayah memiliki data, tampilkan **“Cakupan penelitian: n zona, bukan seluruh Kabupaten Demak”**.

### 1.3 Tiga mode produk

| Mode | Kapan dipakai | Output yang diperbolehkan | Larangan |
|---|---|---|---|
| `DEMO` | Data ilustrasi untuk memeriksa UI | Tampilan demo, peta contoh, alur dummy yang diberi watermark | Klaim hasil ilmiah/real-world |
| `DATA_EXPLORER` | Sumber nyata berhasil diimpor, label training belum memadai | Peta pengamatan, indeks turunan, mutu sumber, *ecological screening*, prioritas survei | Menyebut skor sebagai akurasi atau prediksi survival |
| `VALIDATED_MODEL` | Dataset berlabel asli, pipeline dan evaluasi memenuhi syarat | Inferensi XGBoost sesuai target asli, evaluasi dan SHAP berdasarkan artefak model | Menganggap SHAP kausal/menentukan tindakan sipil otomatis |

Mode default `DATA_EXPLORER` ketika data tersedia; jika belum tersedia, `DEMO` eksplisit. Pengguna tidak dapat memilih `VALIDATED_MODEL` secara manual tanpa manifest kelayakan model.

### 1.4 Yang TIDAK boleh diklaim

- Keberadaan mangrove atau NDVI tinggi **bukan** label “bibit hidup 90%”.
- JRC Surface Water occurrence **bukan** pengukuran jam genangan pasang surut.
- Salinitas permukaan laut regional **bukan** salinitas pori sedimen di lokasi penanaman.
- DEMNAS **tidak otomatis** cukup presisi untuk mikro-elevasi habitat intertidal.
- SHAP menjelaskan kontribusi fitur terhadap **prediksi model**, bukan hubungan sebab-akibat.
- Sistem tidak menggantikan izin kawasan, analisis biodiversitas, penilaian spesies, konsultasi warga, atau survei lapangan.

---

## 2. PRIORITAS PENGEMBANGAN BERDASARKAN KELENGKAPAN DATA

**Prioritas 1:** Data primer sekunder terbuka tentang **kelangsungan hidup / rekrutmen semai**.  
**Prioritas 2:** Lingkungan tempat sampel berasal (hidrologi, substrat, gelombang, koordinat).  
**Prioritas 3:** Fitur satelit yang **waktunya sesuai** dengan pengamatan lapangan.  
**Prioritas 4:** Tampilan dashboard dan opsi rekomendasi.  
**Prioritas 5:** XGBoost–SHAP jika target dan ukuran sampel masuk akal.

Jangan mendahulukan fitur desain dibanding data dan uji kualitas.

### 2.1 Pilih satu target AI yang defensibel

**Urutan calon target:**

1. `seedling_survival_pct`: bila per kelompok percobaan terdapat **jumlah bibit awal, jumlah hidup, periode tindak lanjut, dan kondisi lingkungan** yang dapat ditautkan.
2. `seedling_density_m2` atau status rekrutmen semai: bila pengamatan kepadatan memiliki unit area jelas dan konteks waktu/lokasi.
3. `mangrove_border_shift_m`: bila data perubahan batas punya waktu pengamatan jelas; ini adalah respons dinamika tepi mangrove, bukan survival bibit.
4. `habitat_suitability_class`: **hanya** bila label kesesuaian dibuat dari survei/otoritas yang independen dan metodenya terdokumentasi; bukan label fiktif dari aturan yang sama dengan input model.

**PENTING:** Jangan menyatukan target-target ini menjadi satu label atau menyebut semuanya “keberhasilan rehabilitasi”. Buat `target_definition.md` yang menjelaskan target terpilih dan alasan pilihan, unit analisis, penyebab missing data, serta batas generalisasi.

---

## 3. KATALOG DATA NYATA DAN STATUS AKSES

**Status pada penyusunan dokumen:** Tautan/materi metadata sumber di bawah telah diidentifikasi; **berkas mentah tidak diasumsikan sudah terunduh dan tidak diasumsikan berisi nama kolom tertentu**. Antigravity harus membuktikan sendiri dengan audit *file-by-file*.

| ID | Sumber resmi | Isi yang perlu diperiksa | Peran | Catatan verifikasi |
|---|---|---|---|---|
| `D01` | van Bijsterveldt dkk. (2020), 4TU: https://doi.org/10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23 | 11 tambak terbengkalai dan 10 lokasi sisi laut di pesisir Demak; parameter kedalaman air, pH, redoks, sedimen, kepadatan semai, paparan gelombang, perubahan tepi mangrove | Fitur ekologis + target respons tertentu | Metadata publik teridentifikasi; belum audit berkas mentah |
| `D02` | van Bijsterveldt dkk. (2022), 4TU: https://doi.org/10.4121/17927198 | Dataset *To Plant or Not to Plant*: survei propagul, pembentukan semai, kelangsungan hidup, pertumbuhan, eksperimen penanaman dan struktur perlindungan; cakupan Demak 2005–2020 | **PRIORITAS TARGET AI** | Perlu cek file tabel, ID eksperimen, tanggal, ukuran unit sampel |
| `D03` | Gijón Mancheño dkk. (2025), 4TU: https://doi.org/10.4121/72bb1736-28be-4c10-8f13-c7e57f8a7803 | Batimetri/sedimentasi/struktur permeabel Timbulsloko, studi 2021–2022 | Konteks sedimentasi untuk lokasi yang cocok | Bukan label survival dan tak boleh otomatis di-*join* dengan D01/D02 |
| `D04` | Muhammad dkk. (2025), artikel BMC Ecology and Evolution: https://doi.org/10.1186/s12862-025-02406-7 | Salinitas, tekstur, durasi genangan, vegetasi Bedono | Pembanding ilmiah | Data mentah mungkin perlu diminta ke penulis; jangan fabrikasi dari ringkasan |
| `G01` | JAXA Global Mangrove Watch v4.1: https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm | Tutupan mangrove tahunan 1985–2025, GeoTIFF multiband 30 m, 0/1 | Perubahan tutupan | **Bukan target survival**; lihat atribusi/lisensi JAXA |
| `G02` | Sentinel-2 SR Harmonized: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED | Band B2,B3,B4,B8,B11,B12; NDVI, NDMI, MNDWI (sesuai formula), periode sejak 2017 | Fitur vegetasi/air | Masking awan; jangan pasangan 2015 dengan citra modern |
| `G03` | DEMNAS BIG: https://www.big.go.id/content/produk/demnas | Elevasi raster | Fitur topografi indikatif | Periksa datum dan ketelitian vertikal |
| `G04` | JRC GSW v1.4: https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater | occurrence/seasonality air Landsat 1984–2021 | Proxy air historis | **Bukan hidroperiode pasang surut** |
| `G05` | Stasiun pasang surut BIG Semarang: https://srgi.big.go.id/tides/smrg | Ketinggian air regional (jika akses sesuai) | Konteks pasang surut | Tidak mewakili elevasi air/genangan setiap titik Demak |
| `G06` | ESA WorldCover: https://esa-worldcover.org/en/data-access | Tutupan lahan 2020/2021 | Masker tutupan lahan | Tidak menghasilkan label sukses penanaman |
| `G07` | BIG/BPS/instansi daerah | Batas resmi Kabupaten/Kecamatan/Desa Demak, tata ruang dan status kawasan jika tersedia | Batas AOI, saringan legal | Atribusi dan tanggal versi wajib dicatat |

### 3.1 Urutan akuisisi dataset (jangan dibalik)

**D02 → D01 → D03 → G01 → G02 → G03 → G04 → G05/G06/G07**.

- Untuk setiap DOI, buka landing page, temukan file/unduhan asli jika diizinkan, simpan nama dan format file **apa adanya**, tanggal akses, ukuran, hash SHA256, lisensi, DOI/URL, dan nama studi.
- Jika pengunduhan gagal/akses dibatasi, buat entri status `MANUAL_DOWNLOAD_REQUIRED` dan tampilkan petunjuk unduh manual melalui halaman sumber. Jangan mengarang endpoint API atau melakukan scraping yang melanggar ketentuan.
- Jika file berupa XLSX/CSV/MAT/ZIP/GeoTIFF, buat pembaca sesuai format dan **inventaris isi ZIP sebelum ekstraksi**. Blok ZIP path traversal dan bom arsip; ekstraksi hanya lokasi aman. Pengunggahan tidak boleh mengeksekusi kode.
- Jangan menamai data input sebagai `demak_master_real.csv` sebelum asal dan baris asli diverifikasi.
- Jangan menganggap satu *geospatial point* pada metadata artikel sebagai posisi semua stasiun penelitian.
- Untuk G01, pahami bahwa raster memiliki 41 band 1985–2025; tahun yang dituju harus memilih band sesuai keterangan sumber, tidak selalu `band=1`.

### 3.2 Masalah temporal yang wajib diselesaikan

- **D01 merekam lapangan 2015**. Sentinel-2 SR Harmonized yang tersedia pada GEE mulai **2017**. Jangan mengekstrak Sentinel-2 tahun 2022/2025 lalu menyebutnya fitur tahun 2015. Gunakan Landsat dengan tahun cocok jika layak, atau tandai variabel satelit `missing_for_period`.
- D02 melintasi 2005–2020, tetapi tabel eksperimennya mungkin hanya mencakup subperiode tertentu. Gunakan tanggal asli **per baris**, bukan tahun metadata untuk semua baris.
- D03 2021–2022 hanya dapat menambah karakteristik jika lokasi/waktu/unit penelitiannya kompatibel. Jika tidak, tampilkan sebagai **layer independen**, bukan fitur training yang di-*join* otomatis.
- GMW tahunan ≠ ketersediaan citra satelit bebas awan pada semua tanggal. Catat *temporal offset* untuk setiap ekstraksi.

### 3.3 Struktur provenance wajib

Buat `data/catalog.csv` dan satu manifest per sumber `data/manifests/<SOURCE_ID>.json` dengan minimal:

```json
{
  "source_id": "D02",
  "title": "To Plant or Not to Plant dataset",
  "doi_or_url": "https://doi.org/10.4121/17927198",
  "provider": "4TU.ResearchData",
  "retrieved_at_utc": null,
  "download_status": "NOT_DOWNLOADED",
  "license": null,
  "local_files": [],
  "sha256": {},
  "geographic_extent": "Demak (metadata only)",
  "temporal_extent": "2005-2020 (metadata only)",
  "variable_inventory_verified": false,
  "notes": "Populate fields only after accessing original records"
}
```

Setiap baris yang masuk ke tabel master harus menyimpan `source_id`, `source_file`, `source_row_id` (bila ada), `observed_at`, `data_status`, dan `processing_version`. Jangan menghilangkan sumber saat transformasi.

---

## 4. ARSITEKTUR SISTEM YANG HARUS DIBUAT

### 4.1 Teknologi yang dipilih (MVP paling realistis)

| Layer | Teknologi | Fungsi |
|---|---|---|
| UI dan navigasi | **Streamlit** | Dashboard multipage Bahasa Indonesia |
| Peta | **Folium + streamlit-folium** | Marker/polygon, layer, pemilihan zona |
| Data tabular | **pandas, numpy, pyarrow** | ETL, tabel, Parquet |
| Geospasial | **geopandas, shapely, pyproj** | Overlay, validasi geometri, perubahan CRS |
| Raster (opsional setelah MVP) | **rasterio, rioxarray** | Sampling raster, statistik zonal |
| Visualisasi | **Plotly** | Tren, scatter, kelengkapan data, faktor SHAP |
| ML | **xgboost, scikit-learn** | Baseline, validasi, prediksi bersyarat |
| Interpretasi | **shap** | Kontribusi fitur model valid |
| Validasi data | **pydantic / pandera** | Skema, rentang dan kualitas data |
| Metadata lokal | **SQLite** | Dataset, zona, verifikasi, run model |
| Tests | **pytest** | Unit test/integration/smoke test |

**Hindari** memulai dengan Next.js, FastAPI, PostgreSQL, Kubernetes atau arsitektur kompleks jika belum diperlukan. Versi awal harus mudah dijalankan pada laptop Windows. Stack dapat dimodularisasi untuk migrasi ke PostGIS di masa depan.

### 4.2 Struktur direktori yang diwajibkan

```text
mangrove-fit/
├── app.py
├── README.md
├── AGENTS.md                         # aturan ringkas workspace, dibuat otomatis oleh agent
├── requirements.txt
├── requirements-optional.txt
├── .gitignore
├── .env.example
├── config/
│   ├── settings.yaml
│   ├── ecological_rules.yaml         # aturan bersyarat, placeholder harus jelas
│   └── target_definitions.yaml
├── pages/
│   ├── 01_Beranda.py
│   ├── 02_Peta_Pesisir_Demak.py
│   ├── 03_Katalog_dan_Audit_Data.py
│   ├── 04_Analisis_Zona.py
│   ├── 05_Prioritas_Rehabilitasi.py
│   ├── 06_Model_XGBoost_SHAP.py
│   ├── 07_Validasi_Lapangan.py
│   └── 08_Tentang_dan_Sumber.py
├── src/mangrovefit/
│   ├── __init__.py
│   ├── ui/components.py
│   ├── ui/styles.py
│   ├── data/catalog.py
│   ├── data/ingest.py
│   ├── data/validate.py
│   ├── data/provenance.py
│   ├── data/joins.py
│   ├── geo/geometry.py
│   ├── geo/sampling.py
│   ├── geo/indices.py
│   ├── geo/shoreline.py
│   ├── models/train.py
│   ├── models/predict.py
│   ├── models/evaluate.py
│   ├── models/explain.py
│   ├── decisions/screening.py
│   ├── decisions/prioritize.py
│   ├── decisions/recommend.py
│   ├── storage/db.py
│   └── reports/export.py
├── scripts/
│   ├── 01_catalog_sources.py
│   ├── 02_inventory_raw.py
│   ├── 03_build_observations.py
│   ├── 04_extract_geospatial.py
│   ├── 05_build_training_table.py
│   ├── 06_train_validate.py
│   └── 07_smoke_test.py
├── data/
│   ├── raw/                       # gitignored; asli tidak diubah
│   ├── staging/                   # gitignored
│   ├── processed/
│   ├── demo/                      # jelas sintetis
│   ├── manifests/
│   ├── catalog.csv
│   └── DATA_STATUS.md
├── artifacts/models/               # artefak lokal, registrasi dan versi
├── reports/
├── tests/
│   ├── test_import.py
│   ├── test_geo.py
│   ├── test_temporal_join.py
│   ├── test_leakage.py
│   ├── test_model_gating.py
│   ├── test_screening.py
│   ├── test_recommendations.py
│   └── test_export.py
└── docs/
    ├── DATA_DICTIONARY.md
    ├── DATA_AUDIT.md
    ├── TARGET_DEFINITION.md
    ├── MODEL_CARD.md
    ├── METHODOLOGY.md
    ├── IMPLEMENTATION_STATUS.md
    └── USER_GUIDE.md
```

Buat semua berkas yang diperlukan untuk MVP; modul tambahan dapat diberi status implementasi di `IMPLEMENTATION_STATUS.md` tetapi **jangan membuat tombol tidak berfungsi**.

### 4.3 Konfigurasi aplikasi

- `STUDY_AREA_NAME = "Pesisir Kabupaten Demak, Jawa Tengah"`.
- `ACTIVE_MODEL_STATUS` berasal dari model registry; default `UNAVAILABLE`.
- `DEMO_MODE_ENABLED = true`, **tetapi tidak boleh otomatis tercampur dengan data nyata**.
- Kriteria ambang ekologi (genangan, salinitas, gelombang, status lahan, dll.) harus disimpan dalam YAML dengan `source_reference`, `applies_to`, `reviewed_by`, `review_date`, `is_provisional`. Jika belum ada rujukan yang tepat, **jangan menetapkan ambang numerik seolah standar ilmiah**.
- Tanggal dan versi semua dataset tampil pada bagian footer/kartu sumber.

---

## 5. SKEMA DATA DAN PENGOLAHAN

### 5.1 Tabel inti

**A. `sources`**: `source_id, title, doi_or_url, license, retrieval_date, file_hash, status, notes`.

**B. `sites`**: `site_id, site_name, village, district, regency, lat, lon, geometry_wkt, geometry_crs, location_precision_m, location_verified, source_id`.

**C. `field_observations`**: satu baris per **observasi nyata / tanggal / unit sampel**.

```csv
record_id,source_id,source_file,source_row_id,site_id,plot_id,observed_at,latitude,longitude,water_depth_cm,inundation_hours_day,salinity_ppt,soil_ph,redox_mv,sulfide_mg_l,median_grain_um,sediment_water_content_pct,soil_organic_carbon_pct,bulk_density_g_cm3,wind_fetch_m,wave_exposure_index,seedling_density_m2,seedlings_initial,seedlings_alive,followup_days,mangrove_border_shift_m,measurement_method,measurement_status,quality_flag
```

Kolom boleh `null` jika tidak ada. Jangan memaksa 100% kolom terisi; pertahankan unit, missingness, dan tipe data.

**D. `geospatial_features`**: `site_id, feature_date_start, feature_date_end, source_id, raster_year, ndvi, ndmi, mndwi, gmw_cover, gsw_occurrence_pct, elevation_m, valid_pixel_pct, cloud_mask_method, temporal_offset_days, spatial_resolution_m, extraction_method, quality_flag`.

**E. `labels`**: `record_id, target_name, target_value, target_unit, target_observed_at, observation_window_days, target_source_id, label_quality`.

**F. `zone_decisions`**: `zone_id, run_id, analysis_date, mode, screening_status, priority_category, evidence_quality, limiting_factors_json, recommendation, review_status, reviewer, source_ids_json`.

**G. `model_registry`**: `model_id, target_name, source_ids_json, features_json, train_period, test_period, grouping_key, metrics_json, validated, approval_status, model_path, created_at, software_versions_json, data_hash`.

### 5.2 Aturan normalisasi data

- Pisahkan `study_id`, `site_id`, `plot_id`, `experiment_id`, `replicate_id`, `date`. Jangan menganggap koordinat berulang berarti sampel independen.
- Ubah `lat/lon` hanya jika sumber menyatakan format asli; log transformasi DMS/UTM.
- Simpan **nilai mentah** dan **nilai yang dinormalisasi**. Dokumentasikan konversi satuan, termasuk redoks, salinitas (ppt/PSU), ukuran butir (µm/mm), tinggi genangan (cm/m), dan survival (%/rasio).
- `seedling_survival_pct = 100 * seedlings_alive / seedlings_initial` **hanya jika** kedua jumlah berasal dari kohort dan titik waktu yang tepat serta `seedlings_initial > 0`. Jangan membuat survival dari selisih dua kepadatan yang tidak kompatibel.
- Rentang yang tidak masuk akal (mis. NDVI < -1 atau > 1; `alive > initial`) → `invalid`, bukan dipotong diam-diam.
- `salinity_ppt` hasil sensor lokal dan salinitas model oseanografi regional **bukan variabel setara**; beri field/sumber berbeda.
- Jangan meng-*join* data yang hanya sama `desa`. Temporal match gunakan jendela yang **dinyatakan dan diuji**, bukan asumsi.
- Berikan peringatan pada *duplicate coordinates*, campuran CRS, proyeksi salah, missing target, tanggal tidak valid, data tipe string, sampel kecil, dan *spatial leakage*.
- Simpan hasil ETL di Parquet dengan `schema_version`, checksum, dan *audit log*.

### 5.3 Indeks Sentinel-2 yang boleh dihitung

Gunakan band *surface reflectance* yang benar; lakukan cloud/shadow masking, kontrol musim dan tanggal, skala reflektansi yang sesuai. Sediakan minimal:

- `NDVI = (B8 - B4) / (B8 + B4)`.
- `NDMI = (B8 - B11) / (B8 + B11)`.
- `MNDWI = (B3 - B11) / (B3 + B11)`.

Denominator nol → `NaN` dan flag. Resolusi dan resampling harus terdokumentasi (B11 20 m vs B8/B3/B4 10 m). Jangan menilai pixel 10 m seolah seluruh variabel berasal dari pengukuran 10 m. Gunakan masker awan yang tersedia seperti Sentinel-2 Cloud Probability/Cloud Score+ bila sesuai; simpan persentase pixel valid.

### 5.4 Join spasial-temporal secara aman

```
RAW DATASET + FILE/ROW SOURCE ID
    → parse → validate → harmonize units / CRS
    → preserve observed_at + location accuracy
    → match study/site/plot identifiers
    → optionally extract raster within justified date window
    → record spatial_distance_m, temporal_offset_days
    → reject ambiguous join / record missing
    → audited observations + optional features
```

Aturan: jangan memakai data setelah kejadian (misalnya citra pasca-survival) untuk memprediksi survival sebelumnya. Pisahkan fitur pra-intervensi dari fitur pasca-intervensi. Hasil pengukuran 2021–2022 D03 tidak boleh otomatis dipakai memprediksi eksperimen 2015 D01.

### 5.5 Data quality score

Jangan membuat skor kualitas data yang disalahartikan sebagai akurasi ilmiah. Buat profil kualitas **deskriptif**: ketersediaan, sumber, akurasi koordinat, selisih tanggal, kecocokan skala, flag validitas, serta catatan reviewer. Jika skor agregat dibutuhkan untuk penyortiran UX, harus disebut **“Indeks kelengkapan metadata (administratif)”**, bukan *confidence model* atau validitas ekologis.

---

## 6. TRAINING XGBOOST DAN INFERENSI (AKTIF BERSYARAT)

### 6.1 Pemeriksaan sebelum training

Pipeline `scripts/06_train_validate.py` harus otomatis menghasilkan `docs/TARGET_DEFINITION.md` dan `docs/MODEL_CARD.md`:

- Apakah label target **asli dan punya definisi operasional**? Berapa baris berlabel, berapa lokasi independen, berapa replikasi per lokasi, per kelas bila klasifikasi?
- Apakah fitur diketahui sebelum target tercatat (*no temporal leakage*)?
- Apakah data dari studi dan unit eksperimen kompatibel?
- Apakah fitur salinitas, substrat, atau pasang surut punya missingness besar/berbeda antar-studi?
- Apakah ada potensi data latih dan uji berasal dari lokasi yang sama? Jika iya, gunakan `GroupKFold`, `GroupShuffleSplit`, atau *leave-one-site-out* sesuai jumlah grup; tidak boleh pakai *random pixel split* untuk klaim generalisasi geografis.
- Apakah preprocessing (imputasi, standardisasi bila dipakai, encoding) hanya di-*fit* pada training folds? Wajib pipeline scikit-learn atau prosedur setara.
- Apakah sampel cukup untuk evaluasi yang bermakna? Tidak ada satu ambang universal. **Jika lokasi independen dan target terlalu sedikit, latihan hanya boleh bertanda `EXPLORATORY`, tidak boleh `VALIDATED`.**

### 6.2 Baseline dan model utama

- Regresi survival/densitas: baseline `DummyRegressor` dan `RandomForestRegressor` atau estimator sederhana relevan; kandidat `XGBRegressor`.
- Klasifikasi label valid: baseline `DummyClassifier`/logistic regression dan `RandomForestClassifier`; kandidat `XGBClassifier`.
- Pilih hanya target yang benar-benar tersedia; jangan mengubah survival berkelanjutan menjadi tinggi/sedang/rendah dengan threshold arbitrer tanpa alasan ilmiah.
- Hiperparameter dituning dalam evaluasi grup, misalnya randomized search terbatas; gunakan seed reproduksibel, batas kompleksitas, early stopping jika sesuai; larang *test set* untuk tuning.
- Metrik regresi: MAE, RMSE, R² (dengan kewaspadaan sampel kecil), median error dan galat per lokasi jika memungkinkan.
- Metrik klasifikasi: confusion matrix, macro F1, recall, precision, ROC-AUC/PR-AUC hanya ketika sesuai, dan kalibrasi probabilitas jika menampilkan probabilitas.
- Laporkan **interval/variabilitas antar-fold**, ukuran sampel uji, jumlah grup, dan baseline; jangan hanya satu angka “akurasi 95%”.
- Data sintetis/demo **tidak pernah** menjadi evidence performa dunia nyata.

### 6.3 Artefak model

Simpan `artifacts/models/<model_id>/`:

```text
model.json atau model.joblib   # hanya dari build lokal tepercaya
preprocessor.joblib
metadata.json                 # daftar fitur, urutan, satuan, waktu, data hash
metrics.json
splits.json                   # site_id/train/test jika diizinkan
model_card.md
shap_summary.csv              # hanya bila dihitung dari model asli
```

**Security:** jangan membuka artefak pickle/joblib dari sumber tidak tepercaya. Dataset/model yang dikirim pengguna perlu diverifikasi sebelum dimuat. UI tidak boleh menawarkan upload `.pkl` acak yang otomatis dieksekusi.

`VALIDATED_MODEL` hanya tersedia jika model registry menyatakan `validated=true` **berdasarkan review tertulis pada model card**, pipeline pengujian lulus dan provenance lengkap. Jika tidak, tombol prediksi nonaktif disertai alasan (mis. “belum ada label survival terverifikasi”).

### 6.4 SHAP

- Gunakan SHAP kompatibel dengan XGBoost yang aktif dan fitur dalam urutan training.
- Tampilkan `SHAP summary`, top 5 fitur pada zona terpilih, arah kontribusi, feature value + satuan, base value, serta model/target yang sedang dijelaskan.
- SHAP tidak boleh muncul ketika model tidak tersedia atau data pengguna melewati validasi skema.
- Label UI: **“Penjelasan kontribusi fitur terhadap prediksi model; bukan bukti kausalitas ekologis.”**
- Jika fitur di luar *training distribution* atau kualitas koordinat buruk, tampilkan peringatan *out-of-distribution* / keterbatasan.

---

## 7. ECOLOGICAL SCREENING DAN MESIN REKOMENDASI

### 7.1 Pisahkan dari model ML

Rekomendasi restorasi berasal dari **aturan ekologis yang dapat ditelusuri**, *constraints* lapangan, status hukum, dan pendapat ahli; bukan sekadar memilih kategori dari skor XGBoost. Buat modul `decisions/` terpisah.

### 7.2 Keadaan zona dan contoh logika

| Kondisi terverifikasi | Status / arahan awal | Tindak lanjut |
|---|---|---|
| Mangrove eksisting relatif baik | `PROTECT` | Lindungi; lakukan monitoring, bukan target tanam otomatis |
| Habitat intertidal sesuai, propagul alami tersedia, gangguan rendah | `NATURAL_REGENERATION_REVIEW` | Uji opsi regenerasi alami |
| Aliran pasang surut/kanal terganggu, data memadai | `HYDROLOGY_REVIEW` | Survei teknis/izin untuk pemulihan konektivitas, **tanpa** perintah membuka tanggul otomatis |
| Kesesuaian terverifikasi, sumber propagul kurang, paparan gelombang dapat diterima | `PLANTING_FEASIBILITY_REVIEW` | Kajian spesies lokal dan rencana tanam oleh ahli |
| Paparan gelombang tinggi, area non-habitat, status kawasan tidak jelas, data inti hilang | `DEFER_AND_VERIFY` | Tunda rekomendasi intervensi dan kumpulkan data |

Jika salinitas, hidroperiode, substrat, atau status lahan belum tersedia, aplikasi harus mengatakan **“belum dapat diputuskan”**, bukan “cocok ditanami”. Tidak boleh menormalisasi setiap pantai menjadi habitat mangrove.

### 7.3 Prioritisasi yang transparan

Jangan menggunakan satu skor kesesuaian sebagai “prioritas tertinggi”; contoh lokasi yang sangat sesuai tetapi sudah berhutan utuh justru memerlukan **perlindungan**, bukan rehabilitasi.

Tampilkan **matriks dua sumbu**:

1. `restoration_need` = tingkat kebutuhan/persoalan yang didukung data; dan
2. `intervention_readiness` = kesiapan ekologis/hukum/data untuk tindakan tertentu.

Tambahkan `evidence_quality` sebagai kategori terpisah. Bila membuat angka bobot, bobot awal disimpan di file konfigurasi, berstatus **PROVISIONAL / expert review required**, dan pengguna dapat memeriksa *rationale*. Laporan harus menunjukkan indikator dan nilai yang benar-benar dipakai.

Urutan prioritas default untuk MVP adalah **prioritas survei/verifikasi**, bukan ranking definitif lokasi tanam. Algoritma hanya memeringkat zona yang memiliki data dan jenis tindakan sebanding; zona tak lengkap ditempatkan di kategori `DATA_GAP`.

---

## 8. SPESIFIKASI HALAMAN DAN INTERAKSI UI

**Gaya visual:** profesional, *coastal ecological analytics*, dominan putih dan hijau mangrove dengan aksen biru air; informasi singkat, peta besar, tidak padat ikon dekoratif. Responsif laptop dan tablet. Bahasa antarmuka Indonesia baku. **Semua angka besar harus menampilkan sumber, tanggal, unit, dan status.**

### Halaman 1 — Beranda

- Tampilkan judul lengkap, ringkasan konsep dan wilayah **Demak**, label status `DEMO / DATA EXPLORER / MODEL VALIDATED`.
- Ringkasan status dataset: `tercatat`, `berhasil diunduh`, `lulus audit`, `perlu unduh manual`, `tidak tersedia`.
- KPI deskriptif seperti jumlah sumber, jumlah zona berkoordinat valid, jumlah observasi terverifikasi, jumlah parameter belum tersedia. **Jangan tampilkan “luas lahan layak 4.321 ha” jika belum dihitung dari data nyata.**
- Tombol menuju peta, audit data, dan analisis.

### Halaman 2 — Peta Pesisir Demak

- Basemap OSM atau tiles berlisensi, attribution jelas, zona dan stasiun berkoordinat aktual saja.
- Layer yang dapat dinyalakan: polygon AOI, studi D01–D03 (hanya jika koordinat tersedia), tutupan mangrove GMW, indikator air, vegetasi, garis pantai (jika diimpor), zona prioritas hasil analisis.
- Filter sumber, tahun, desa, tingkat kelengkapan, status rekomendasi, model.
- Klik polygon/marker membuka panel: koordinat, waktu pengamatan, data sumber, fitur tersedia, missing, hasil screening, dan link sumber.
- Upload GeoJSON dan CSV point (kolom lat/lon) dengan validasi CRS, ukuran file, geometri; tampilkan error ramah pengguna.
- Jika data belum ada, peta tetap hidup dengan cakupan konteks Demak dan overlay kosong berlabel "Belum ada titik pengamatan terverifikasi".

### Halaman 3 — Katalog dan Audit Data

- Tabel sumber D01–D04, G01–G07; status download, doi, lisensi, jumlah file, periode, cakupan, variabel terdeteksi, jumlah baris/kolom setelah audit.
- Aksi `Buka halaman sumber`, `Impor file lokal`, `Audit`, `Lihat data dictionary`, `Unduh laporan audit`.
- Unggah CSV, XLSX, GeoJSON, ZIP tepercaya; preview sheet; pilih sheet; pemetaan nama kolom manual; validasi.
- Visualisasi missingness per parameter, catatan tipe/satuan yang ambigu, konflik koordinat, dan ringkasan *join readiness*.
- Tombol unduh tidak boleh mengaku berhasil bila server eksternal tidak memberi berkas. Tampilkan cara unduh manual.

### Halaman 4 — Analisis Zona

- Pilih zona + periode + sumber. Tampilkan chart perubahan vegetasi jika memiliki seri data, parameter teramati, indikasi genangan, kondisi substrat, dinamika pantai, dan gap.
- Panel kiri `Data yang diketahui`; panel kanan `Data yang belum diketahui`.
- Tab `Skema data`, `Hasil screening`, `Sumber & metode`, `Riwayat pengamatan`.
- Pilihan inspeksi manual kualitas data serta catatan verifikator.

### Halaman 5 — Prioritas Rehabilitasi

- Tabel zona dengan kategori: `PERLINDUNGAN`, `VERIFIKASI REGENERASI`, `VERIFIKASI HIDROLOGI`, `KAJIAN PENANAMAN`, `TUNDA—DATA KURANG`.
- Matriks kebutuhan restorasi vs kesiapan tindakan (bukan klaim probabilitas sukses).
- Detail penjelasan setiap keputusan: input, aturan terpicu, referensi aturan, *missing values*, rekomendasi survei, reviewer.
- Perbandingan maksimal tiga zona berdampingan.
- Ekspor CSV/GeoJSON dan laporan ringkas HTML/Markdown dengan disclaimer dan seluruh sumber.

### Halaman 6 — Model XGBoost dan SHAP

- Secara default tampil **“Model belum dilatih/tervalidasi”** dan checklist prasyarat jika data belum siap.
- Jika siap, tampil nama target, fitur, jumlah sampel & lokasi independen, metode split, baseline vs XGBoost, hasil evaluasi, tanggal training, SHA dataset.
- Tampilkan SHAP summary dan local feature contributions **hanya saat model valid**.
- Tombol `Jalankan prediksi` harus disabled ketika tidak memenuhi gating dan menjelaskan alasannya.

### Halaman 7 — Validasi Lapangan

- Form input observasi dengan tanggal, koordinat, unit, instrumen/metode, sumber petugas, kualitas data, foto opsional dengan persetujuan (jangan tampilkan data personal publik).
- Ekspor formulir CSV kosong dan impor isian.
- Status verifikasi: `draft`, `verified`, `rejected` beserta catatan.
- Input manual tidak secara otomatis dianggap "verified".

### Halaman 8 — Tentang dan Sumber

- Tujuan, peta alur teknologi, definisi target AI, sumber dataset resmi, keterbatasan, atribusi data (terutama GMW), etika dan privasi, cara penggunaan.
- Perbedaan habitat suitability vs seedling survival vs restoration priority.
- Bagian *research disclaimer*: prototipe konsep pendukung keputusan, hasil belum menjadi keputusan resmi pemerintahan.

---

## 9. PENGALAMAN PENGGUNA UTAMA (USER STORIES)

1. Sebagai analis, saya dapat mengimpor dataset lapangan D02, melihat jumlah sheet dan kolomnya, menandai kolom target kelangsungan hidup, dan mengetahui apakah baris memiliki koordinat/tanggal.
2. Sebagai analis, saya dapat memetakan stasiun D01 dari koordinat asli, membuka detail sumber dan parameter yang benar-benar tersedia.
3. Sebagai peneliti, saya dapat meninjau apakah data 2015 cocok dengan satelit tahun yang sama; jika tidak, sistem memberi `TEMPORAL_MISMATCH` dan tidak memaksa join.
4. Sebagai pengelola, saya bisa melihat bahwa satu zona perlu pemeriksaan kondisi hidrologi dan bahwa rekomendasi belum final sampai ada survei.
5. Sebagai juri, saya bisa membuka `MODEL_CARD` dan membedakan bukti data nyata, angka simulasi, dan rencana validasi.
6. Sebagai developer, saya bisa menjalankan aplikasi tanpa akun Google Earth Engine, lalu menambah data asli tanpa mengubah UI inti.
7. Sebagai penguji, saya bisa menelusuri setiap angka sampai file, baris, tanggal, dan transformasi yang menghasilkan angka tersebut.

---

## 10. IMPLEMENTASI PAKET ETL DAN DATA DOWNLOAD

### 10.1 CLI wajib

Buat antarmuka perintah berikut (boleh memakai `python -m ...` atau skrip `.py` konsisten):

```powershell
python scripts/01_catalog_sources.py
python scripts/02_inventory_raw.py --source D02 --path "data/raw/D02"
python scripts/03_build_observations.py --source D02
python scripts/05_build_training_table.py --target seedling_survival_pct
python scripts/06_train_validate.py --target seedling_survival_pct
python scripts/07_smoke_test.py
```

Jika dataset belum ada, perintah harus **gagal secara informatif / berstatus SKIPPED**, tidak diam-diam menciptakan observasi. Jika format asli sulit, implementasikan dukungan impor manual melalui UI dan dokumentasikan peta kolom. `04_extract_geospatial.py` harus bisa dijalankan dengan GeoTIFF lokal; autentikasi Google Earth Engine menjadi opsi lanjutan, bukan prasyarat MVP.

### 10.2 Laporan audit otomatis

`docs/DATA_AUDIT.md` minimal memuat:

- waktu pemeriksaan dan versi perangkat lunak;
- file sumber, hash, lisensi;
- sheet/table, dimensi, nama kolom asli;
- unit, rentang nilai, missingness, nilai ekstrem, duplikasi;
- cakupan spasial dan temporal yang **benar-benar teramati**;
- ada/tidaknya kolom lokasi, tanggal, unit percobaan, label target;
- apakah target ML dan data per lokasi memenuhi syarat;
- keputusan `READY_FOR_DESCRIPTIVE_ANALYSIS`, `READY_FOR_EXPLORATORY_ML`, `NEEDS_MORE_DATA` dengan alasan.

### 10.3 Proses ekspor peta

- Peta menggunakan sumber sah yang benar-benar sudah dimuat; jangan gunakan peta dekoratif generik sebagai hasil penelitian.
- Simpan GeoJSON pengamatan asli dengan field sumber dan waktu; *clip* berdasarkan AOI jika polygon tersedia dan sistem mencatatnya.
- Raster jika terlalu besar: proses *tiling*, *raster window*, *chunking* atau sampling relevan; hindari membaca seluruh raster global GMW ke memori.
- Cache hasil per `source_id + version + year + AOI_hash` untuk mengurangi proses ulang dan hindari request API tanpa batas.

---

## 11. BASIS DATA DAN PENYIMPANAN

- SQLite untuk `sources`, `sites`, `uploaded_files`, `observations_metadata`, `model_registry`, `zone_decisions`, `review_log`.
- GeoParquet/Parquet untuk tabel besar, GeoJSON untuk ekspor peta, raster pada berkas lokal.
- Simpan unggahan raw di direktori terproteksi dari akses publik, jangan mengekspos jalur filesystem Windows ke browser.
- Backup data dan audit; jangan mengubah file raw. Jika data lapangan sensitif atau koordinat lokasi konservasi yang rawan eksploitasi, gunakan pengaburan/pembatasan akses sesuai kebutuhan.
- Nilai null tetap null. Tidak boleh otomatis menulis hasil prediksi pada kolom observed.

---

## 12. KUALITAS, PENGUJIAN DAN ERROR HANDLING

### 12.1 Tests minimum

Buat pytest untuk skenario berikut:

1. CSV valid dengan lat/lon masuk ke peta dan sumber tercatat.
2. CSV dengan koordinat di luar domain atau string invalid ditolak dengan pesan jelas.
3. GeoJSON tanpa CRS eksplisit ditangani dengan aman; tidak menganggap CRS nonstandar adalah WGS84 tanpa pemeriksaan.
4. Koordinat, tanggal, dan unit eksperimen berbeda tidak boleh di-*join* hanya karena nama desa sama.
5. Data D01 2015 + Sentinel-2 2025 memunculkan `TEMPORAL_MISMATCH`.
6. Survival `alive > initial`, `initial=0`, atau `followup_days` tidak kompatibel ditolak/tidak dihitung.
7. Demo synthetic tidak masuk pipeline pelatihan default.
8. Model `UNAVAILABLE` menyebabkan SHAP dan tombol prediksi tidak aktif; status disajikan.
9. Jika artefak model memang tersedia, fitur missing atau urutan kolom salah tidak menghasilkan prediksi diam-diam.
10. Rekomendasi `PLANTING_FEASIBILITY_REVIEW` tidak dihasilkan bila data hidrologi/status lahan kritis belum ada.
11. Ekspor mencakup source_id, tanggal, quality flag, status mode, dan disclaimer.
12. Impor ZIP yang mengandung path traversal ditolak.
13. Perhitungan NDVI/NDMI/MNDWI menghasilkan nilai benar untuk contoh numerik yang diketahui dan NaN untuk pembagi nol.
14. Peta, seluruh halaman, dan alur utama lolos smoke test dengan dataset kecil yang **jelas sintetis**.

### 12.2 UX error dan fallback

- GEE meminta kredensial → tampil `Opsional: autentikasi Earth Engine belum dilakukan`, gunakan file lokal.
- Data sumber belum diunduh → tombol `Buka sumber resmi` dan instruksi impor file.
- Koneksi internet tidak ada → aplikasi lokal dan daftar sumber masih berjalan.
- Kolom tidak ditemukan → wizard pemetaan kolom, bukan aplikasi crash.
- Raster terlalu besar → notifikasi ukuran dan opsi AOI lebih kecil.
- Nilai kritis belum terukur → status `BELUM CUKUP DATA`, bukan default 0.
- Model kecil/overfit → tampil `EKSPLORATIF — TIDAK UNTUK KEPUTUSAN LAPANGAN`.

### 12.3 Logging dan reproduksibilitas

- Catat run_id, git commit (jika tersedia), Python/package versions, konfigurasi, seed, fingerprint dataset, parameter ML, lokasi hasil, dan hasil tests.
- Simpan input dan output evaluasi untuk memeriksa kesalahan; jangan membocorkan data personal.
- Beri *timestamp* dan sumber pada grafik dan peta.

---

## 13. TAHAPAN KERJA ANTIGRAVITY (EKSEKUSI BERURUTAN)

### FASE 0 — Workspace dan pemeriksaan kebutuhan [WAJIB]

- [ ] Buat folder proyek dan virtual environment.
- [ ] Buat `AGENTS.md` yang berisi ringkasan aturan nonfabrikasi, data-first, mode AI, testing (jaga ringkas; dokumentasi panjang tetap dokumen ini).
- [ ] Buat README, dependensi, `.gitignore`, `.env.example`, konfigurasi.
- [ ] Buat UI kerangka dan verifikasi `streamlit run app.py` berjalan.
- **Bukti selesai:** screenshot/hasil smoke test halaman Beranda, perintah start tidak error.

### FASE 1 — Akuisisi dan audit data [PRIORITAS TERTINGGI]

- [ ] Buat katalog D01–D04 + G01–G07 dengan metadata/tautan resmi.
- [ ] Coba dapatkan D02 dan D01 dari repositori resmi bila internet/kebijakan mengizinkan.
- [ ] Jika berhasil: audit raw (bukan sekadar metadata), dokumentasi sheet, tipe, jumlah baris dan target.
- [ ] Jika gagal: tampilkan hambatan yang persis dan dukungan upload manual.
- [ ] Tidak menyebut dataset sebagai siap ML jika kolom target belum diaudit.
- **Bukti selesai:** `docs/DATA_AUDIT.md`, `data/catalog.csv`, manifest per sumber.

### FASE 2 — ETL dan eksplorasi geospasial

- [ ] Terapkan ingest CSV/XLSX/GeoJSON, validasi koordinat/CRS dan metadata.
- [ ] Peta Demak dan layer titik aktual yang diimpor.
- [ ] Ekspor CSV dan GeoJSON dengan sumber.
- [ ] Buat profiling missingness dan mismatch data.
- **Bukti selesai:** demonstrasi peta dari berkas input nyata jika ada, dan test join temporal.

### FASE 3 — Screening dan rekomendasi

- [ ] Implementasikan aturan transparan tanpa threshold ekologis fiktif.
- [ ] Perbandingan zona dan prioritas **verifikasi lapangan**.
- [ ] Laporan sumber/ketidakpastian.
- **Bukti selesai:** kasus *data-lengkap*, *data-tidak-lengkap*, *non-habitat*, *mangrove-eksisting* lolos tests.

### FASE 4 — Model XGBoost dan SHAP [BERSYARAT]

- [ ] Tentukan target berdasarkan file asli dari fase 1.
- [ ] Buat *dataset card*, audit leakage dan pembagian berdasarkan lokasi.
- [ ] Training baseline vs XGBoost (hanya data label nyata).
- [ ] Evaluasi grup dan model card, lalu SHAP model aktual.
- [ ] Jika data tidak cukup, selesaikan UI `MODEL UNAVAILABLE` dan tulis alasan/pekerjaan ilmiah yang diperlukan.
- **Bukti selesai:** `MODEL_CARD.md` jujur, metrik hanya jika test sungguhan, gating test lulus.

### FASE 5 — Penyelesaian, dokumentasi dan review

- [ ] Semua menu aktif dan fungsi diuji, bukan stub atau placeholder menyesatkan.
- [ ] `pytest -q` lulus; buat laporan smoke test.
- [ ] Dokumentasi *Windows setup* dan cara mengimpor data asli.
- [ ] Pastikan atribusi JAXA/GMW, OSM, Sentinel-2/Copernicus, dan dataset riset ditampilkan ketika digunakan.
- [ ] Buat daftar fitur SELESAI/PARSIAL/TERHAMBAT dan keterbatasan ilmiah.
- **Bukti selesai:** perintah start, folder source, test, contoh input demo, README, status ilmiah.

**Jangan menyatakan “100% selesai” jika Fase 4 belum terlatih. Katakan MVP aplikasi selesai dengan model ML belum tervalidasi, bila itu kondisi yang benar.**

---

## 14. PERINTAH INSTALASI DAN CARA MENJALANKAN (WINDOWS)

Antigravity wajib memastikan instruksi ini cocok dengan versi dependensi aktual pada repo:

```powershell
# Dari root project mangrove-fit
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Jika kebijakan PowerShell melarang `Activate.ps1`, berikan opsi `cmd.exe`:

```bat
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
streamlit run app.py
```

Jalankan pengujian:

```powershell
pytest -q
python scripts/07_smoke_test.py
```

Jika memakai pustaka GeoPandas/Rasterio yang sulit diinstal di Windows, jelaskan solusi dependensi/wheels/conda yang sah, **jangan melewati modul krusial tanpa melaporkan**. Hindari meminta API key berbayar untuk fitur dasar.

---

## 15. KRITERIA KEBERHASILAN YANG BISA DIAUDIT

### Must-have acceptance criteria

- [ ] Project lokal start tanpa kesalahan dan dapat dibuka di browser.
- [ ] UI menampilkan judul resmi lengkap dan daerah studi Demak.
- [ ] Peta interaktif bekerja, termasuk marker atau polygon **hasil impor**, bukan koordinat riset rekaan.
- [ ] Halaman katalog dataset memiliki tautan resmi dan status akses yang jujur.
- [ ] Data asli ketika diunggah mempertahankan provenance dan units.
- [ ] Audit data memunculkan jumlah baris, kolom, missingness, dan mismatches sesuai file.
- [ ] Sistem tidak mencampur observasi 2015 dengan citra 2025 tanpa flag.
- [ ] Tidak ada data dummy yang bisa tampil sebagai data nyata.
- [ ] Screening dan rekomendasi menjelaskan alasan, keterbatasan dan tindak lanjut verifikasi.
- [ ] Fitur XGBoost/SHAP nonaktif ketika tidak ada dataset berlabel terverifikasi.
- [ ] Bila model tersedia, metrik dan SHAP berasal dari model yang sama, bukan contoh statis.
- [ ] CSV/GeoJSON/laporan dapat diunduh dan memuat atribusi serta status mode.
- [ ] `pytest -q` lulus; fitur yang belum dikerjakan tercatat di laporan status.
- [ ] README menunjukkan contoh input, langkah setup, cara audit sumber, dan cara menjalankan aplikasi.

### Nice-to-have (setelah MVP)

- [ ] Integrasi GEE otomatis menggunakan kredensial milik user dan izin yang sah.
- [ ] Perbandingan tutupan mangrove per tahun GMW yang benar-benar diekstrak untuk Demak.
- [ ] Pemetaan multiwaktu garis pantai setelah validasi metode dan datum.
- [ ] GeoTIFF AOI crop dan statistik zonal.
- [ ] PDF laporan berformat formal.
- [ ] Fitur admin/reviewer multi-user, GIS PostGIS.
- [ ] Impor data survei berbasis ponsel.

---

## 16. TEMPLATE OUTPUT YANG HARUS DISERAHKAN ANTIGRAVITY

Setelah implementasi, jawaban akhir developer **WAJIB** berisi:

```text
MANGROVE-FIT — IMPLEMENTATION HANDOFF

1) STATUS MVP: [SELESAI / PARSIAL / TERHAMBAT]
2) PERINTAH JALAN: [perintah tepat sesuai hasil tes]
3) FILE KUNCI: [path aktual aplikasi, requirements, README]
4) SUMBER DATA NYATA:
   - D01: [diunduh / perlu manual / tidak ada; nama berkas; jumlah baris jika diaudit]
   - D02: [diunduh / perlu manual / tidak ada; nama berkas; jumlah baris jika diaudit]
   - D03: [diunduh / perlu manual / tidak ada; nama berkas; jumlah baris jika diaudit]
   - G01–G07: [status per sumber]
5) TARGET XGBOOST: [definisi atau BELUM MEMENUHI SYARAT]
6) METRIK: [hasil pengujian nyata atau BELUM ADA]
7) SHAP: [aktif berbasis model nyata / nonaktif]
8) MODE TAMPILAN: [DEMO / DATA_EXPLORER / VALIDATED_MODEL]
9) HASIL PENGUJIAN: [pytest, smoke, hasil]
10) FITUR BELUM SELESAI: [ringkas dan jujur]
11) LANGKAH MANUAL PENGGUNA: [unduh data / upload / kredensial]
12) BUKTI: [screenshot, folder reports, model card, data audit]
```

Jangan hanya menjawab “aplikasi sudah selesai” tanpa perintah, artefak, dan pengujian.

---

## 17. RUJUKAN TEKNIS UNTUK DEVELOPER

Referensi ini adalah sumber data, dokumentasi, atau publikasi untuk memvalidasi implementasi. Antigravity **harus membaca halaman sumber asli** ketika memperoleh akses, menguji berkas data mentah, dan mengikuti lisensi/ketentuan penggunaan. URL adalah referensi, bukan bukti data berhasil diunduh.

1. van Bijsterveldt, C. E. J., dkk. (2020). Dataset *How to restore mangroves for greenbelt creation along eroding coasts with abandoned aquaculture ponds*. 4TU.ResearchData. https://doi.org/10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23
2. van Bijsterveldt, C. E. J., dkk. (2022). Dataset *To Plant or Not to Plant: When can Planting Facilitate Mangrove Restoration?* 4TU.ResearchData. https://doi.org/10.4121/17927198
3. Gijón Mancheño dkk. (2025). *Monitoring Pilot Study of Temporary Permeable Structures for Mangrove Restoration* [dataset pendukung]. https://doi.org/10.4121/72bb1736-28be-4c10-8f13-c7e57f8a7803
4. Muhammad dkk. (2025). Kajian kerentanan dan rehabilitasi mangrove Bedono. *BMC Ecology and Evolution*. https://doi.org/10.1186/s12862-025-02406-7
5. JAXA. (2026). *Global Mangrove Watch v4.1*, 1985–2025, 30 m. https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm
6. Google Earth Engine. *Sentinel-2 Harmonized Surface Reflectance*. https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
7. Google Earth Engine. *Sentinel-2 Cloud Probability*. https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_CLOUD_PROBABILITY
8. EC JRC / Google. *Global Surface Water v1.4*. https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
9. Badan Informasi Geospasial. *DEMNAS*. https://www.big.go.id/content/produk/demnas
10. Google Antigravity. *Rules and workspace instructions*. https://antigravity.google/docs/rules/

### Catatan khusus IT RUSH 2026

Esai adalah gagasan ilmiah populer; pengguna akan menyusun argumentasi urgensi, penelitian terdahulu, mekanisme, manfaat, risiko dan kelayakan. **Aplikasi adalah demonstrator pendukung**, bukan alasan untuk mengarang hasil penelitian. Jangan menggunakan dataset sintetis sebagai bukti prediksi; setiap visual di esai harus diberi nomor/keterangan/sumber. Sertakan status penggunaan AI dengan jujur dan penuhi administrasi yang diwajibkan guidebook.

---

## 18. PESAN AWAL YANG DISARANKAN DI CHAT ANTIGRAVITY

Salin pesan berikut setelah memasukkan dokumen ini ke workspace:

> **Bangun aplikasi MANGROVE-FIT dari file `MANGROVE-FIT_ANTIGRAVITY_MASTER_SPEC_DEMAK_2026.md` ini. Jangan hanya membuat UI statis. Prioritaskan dataset asli Demak: audit D02 dan D01, lalu bentuk pipeline data dan dashboard Streamlit. Ikuti semua pembatasan ilmiah. Jika data sumber tidak bisa diunduh, tetap buat MVP yang benar-benar bekerja dengan fitur impor file dan status data yang jujur. Jangan membuat hasil XGBoost, SHAP, atau koordinat lapangan fiktif. Jalankan tests dan dokumentasikan apa yang selesai, parsial dan terhambat. Mulai dari FASE 0 sampai FASE 5 tanpa mengulang desain dari nol.**

**AKHIR SPESIFIKASI.**
