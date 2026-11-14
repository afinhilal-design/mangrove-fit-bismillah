# MANGROVE-FIT — Spesifikasi Lengkap Pengembangan Aplikasi Web

> **Dokumen serah-terima untuk pengembang (developer handoff)**  
> **Versi:** 1.0 — 14 November 2026  
> **Bahasa antarmuka:** Indonesia  
> **Status:** Spesifikasi perancangan, **belum** merupakan laporan pengujian atau bukti kemampuan prediksi  
> **Target awal:** MVP aplikasi web lokal; dapat ditingkatkan menjadi sistem berbasis data dan model terlatih

## A. Identitas Proyek

**Judul esai (20 kata):**  
**MANGROVE-FIT: Aplikasi Web Prioritisasi Rehabilitasi Mangrove di Pesisir Berbasis XGBoost dan SHAP melalui Integrasi Data Hidrologi, Geospasial, dan Dinamika Pantai**

**Subtema utama:** Teknologi. **Pendukung:** Lingkungan.  
**Jenis produk:** aplikasi web pendukung keputusan (*decision support system*, DSS) berbasis peta interaktif.

### A.1. Ringkasan untuk developer

Buat aplikasi **MANGROVE-FIT** yang membantu petugas pesisir, peneliti, dan kelompok masyarakat mengevaluasi **apakah suatu kawasan pantai layak dipertimbangkan untuk rehabilitasi mangrove**, faktor lingkungan apa yang membatasi kesesuaiannya, dan **tindakan apa yang harus diperiksa atau diprioritaskan**: perlindungan mangrove eksisting, regenerasi alami, perbaikan konektivitas hidrologi, penanaman terbatas, atau penundaan intervensi.

Aplikasi menampilkan peta lokasi, input parameter lingkungan, analisis kesesuaian, penjelasan faktor, prioritas penanganan, ekspor laporan, dan catatan verifikasi lapangan. Model **XGBoost** dan penjelas **SHAP** hanya aktif sebagai *prediksi terlatih* jika dataset berlabel yang memadai serta artefak model yang lolos validasi sudah tersedia. **Jangan membuat probabilitas, akurasi, atau penjelasan SHAP palsu** hanya agar dashboard terlihat penuh.

### A.2. Batasan ilmiah wajib

1. **Kesesuaian habitat ≠ persentase keberhasilan rehabilitasi.** Prediksi kesesuaian dari data kehadiran/ketiadaan mangrove tidak boleh diberi label “peluang bibit hidup” atau “keberhasilan penanaman”.
2. **Tidak semua pesisir cocok ditanami mangrove.** Daerah terumbu, lamun, pantai berpasir berenergi gelombang tinggi, kawasan non-habitat mangrove, dan area berstatus hukum tertentu harus disaring sebelum rekomendasi.
3. **Citra satelit tidak mengukur langsung** salinitas air pori, tekstur substrat, hidroperiode lokal, atau laju keberhasilan penanaman. Parameter tersebut harus berasal dari observasi lapangan, data sekunder terverifikasi, atau diberi status *belum tersedia*.
4. Sistem **tidak memerintahkan pekerjaan sipil**, pembukaan tanggul, atau penanaman otomatis. Hasilnya merupakan rekomendasi awal yang wajib ditinjau ahli/pengelola setempat.
5. Nilai contoh, skor, zona, batas kategori, pembobotan, dan dataset demo adalah **ilustrasi**, bukan hasil eksperimen.
6. Jangan menyebut sistem “real-time”, “akurasi 95%”, atau “prediksi tervalidasi” tanpa integrasi/pengujian yang benar-benar dilakukan.

---

## B. Sasaran, Pengguna, dan Manfaat

### B.1. Masalah yang disasar

Kegiatan rehabilitasi mangrove bisa kurang efektif jika lokasi dipilih tanpa mempertimbangkan hidroperiode, salinitas, elevasi intertidal, dinamika sedimen/pantai, dan peluang regenerasi alami. MANGROVE-FIT diarahkan agar pengguna **memeriksa kelayakan sebelum menanam** dan mendapatkan alasan yang dapat ditindaklanjuti.

### B.2. Tujuan fungsional

1. Menampilkan kawasan pesisir dan zona kandidat rehabilitasi pada peta interaktif.
2. Mengumpulkan dan melacak asal-usul data hidrologi, geospasial, ekologi, dan dinamika pantai.
3. Melakukan **penyaringan kelayakan awal (ecological/legal screening)**, termasuk kondisi data tidak cukup.
4. Jika ada model terlatih: memprediksi **kesesuaian habitat mangrove** dengan XGBoost dan menjelaskan faktor model dengan SHAP.
5. Membandingkan beberapa zona dan membantu menentukan **prioritas survei/tindakan**, tanpa mengabaikan persyaratan ekologis.
6. Memberikan rekomendasi tindakan awal yang transparan dan dapat diedit ahli.
7. Menyimpan analisis, ekspor CSV/GeoJSON/PDF (PDF opsional MVP), serta catatan verifikasi lapangan.

### B.3. Peran pengguna

| Peran | Hak akses |
|---|---|
| Pengunjung/Demo | Melihat peta dan skenario **simulasi**; tidak dapat mengubah data resmi |
| Analis | Impor data, membuat zona, menjalankan analisis, membandingkan dan ekspor |
| Verifikator/Ahli | Meninjau sumber data, mengoreksi status lapangan dan rekomendasi |
| Admin | Mengelola pengguna, model aktif, versi dataset, konfigurasi dan audit |

MVP lokal cukup menyediakan **Demo** dan **Analis lokal**. Autentikasi berbasis peran dapat masuk tahap produksi.

---

## C. Cakupan Pengembangan (Scope)

### C.1. MVP — wajib dibuat

- [ ] Beranda ringkasan, penjelasan tujuan dan batasan sistem.
- [ ] **Peta interaktif** dengan basemap, legenda, pilihan zona, klik zona, dan informasi koordinat.
- [ ] Import **CSV titik** dan **GeoJSON polygon** dengan validasi format, kolom, serta CRS.
- [ ] Form tambah/edit zona pesisir dan input parameter lingkungan manual.
- [ ] Simpan sumber, tanggal, metode pengukuran, dan status kualitas masing-masing parameter.
- [ ] Sistem penyaringan: *eligible / needs review / excluded* disertai alasan.
- [ ] Penilaian berbasis aturan transparan (*rule-based screening*) untuk mode tanpa model.
- [ ] Mode prediksi XGBoost **hanya ketika model terlatih/tervalidasi benar-benar ada**.
- [ ] Penjelasan SHAP hanya ketika mode model valid aktif.
- [ ] Mesin rekomendasi strategi rehabilitasi berbasis aturan ekologis yang dapat ditinjau ahli.
- [ ] Halaman perbandingan zona, filter, dan pengurutan prioritas.
- [ ] Ekspor hasil CSV dan GeoJSON; laporan ringkas HTML/Markdown.
- [ ] Dataset contoh **SINTETIS** dengan watermark “SIMULASI — BUKAN DATA LAPANGAN”.
- [ ] Dokumentasi cara menjalankan, persyaratan data, keterbatasan, dan contoh tangkapan layar.

### C.2. Fitur pengembangan berikutnya — tidak perlu untuk MVP

- [ ] Integrasi otomatis Google Earth Engine/Sentinel-2 dengan akun berizin.
- [ ] Analisis perubahan garis pantai multiwaktu (misalnya transek/DSAS terverifikasi).
- [ ] Upload GeoTIFF, pipeline raster, polygonisasi, statistik zonal.
- [ ] PostgreSQL + PostGIS, FastAPI, API publik, login multiuser.
- [ ] Modul survei lapangan berbasis perangkat seluler dan sinkronisasi offline.
- [ ] Training/retraining model pada server dan panel monitoring drift data.
- [ ] Ekspor PDF formal, pemberitahuan, dan audit trail lanjutan.

### C.3. Bukan tujuan MVP

- Diagnosis keberhasilan rehabilitasi tanpa data hasil penanaman.
- Menentukan spesies mangrove hanya dari NDVI atau skor tunggal.
- Mengeluarkan rekomendasi “langsung tanam” tanpa pemeriksaan lapangan.
- Mengklaim pengukuran pasang surut/salinitas otomatis jika sumbernya tidak ada.
- Mengotomatisasi perubahan morfologi pantai atau rekayasa hidrologi.

---

## D. Rekomendasi Stack Teknologi

**Utamakan satu basis kode Python agar mudah dikembangkan mahasiswa.**

| Lapisan | Teknologi MVP | Catatan |
|---|---|---|
| Bahasa | Python 3.11 atau 3.12 | Gunakan virtual environment dan versi dependensi dikunci |
| UI | Streamlit | Navigasi multipage, form, tabel, unduh berkas |
| Peta | Folium + `streamlit-folium` | Peta interaktif dan pemilihan marker/polygon |
| Data tabular | Pandas, NumPy | Imputasi dan validasi |
| Geospasial | GeoPandas, Shapely, PyProj | CRS, operasi polygon dan geometri |
| Raster (opsional) | Rasterio, Rioxarray | Diaktifkan pada fase analisis raster |
| AI | XGBoost + scikit-learn | Model berbasis dataset berlabel |
| Explainability | SHAP | TreeExplainer, tampilkan top contributors yang benar |
| Grafik | Plotly | Histogram parameter, perbandingan zona |
| Penyimpanan lokal | SQLite + berkas GeoJSON/Parquet | Mudah digunakan untuk demo; PostGIS untuk skala luas |
| Validasi | Pydantic atau Pandera | Validasi skema data |
| Test | pytest | Unit/integrasi/smoke |
| Paket | `requirements.txt` atau `pyproject.toml` | Pin versi hasil uji, jangan bergantung pada `latest` |

Arsitektur MVP: **Streamlit UI → Services → (Screening + Rules + Optional ML + SHAP) → SQLite/Files**. Semua logika bisnis ditempatkan di modul `services`, **bukan** ditanam di halaman UI.

---

## E. Struktur Navigasi dan Halaman

### E.1. Beranda (`pages/1_Beranda.py`)

Komponen:
- Logo/nama MANGROVE-FIT, subjudul “Peta Kesesuaian dan Prioritas Rehabilitasi Mangrove Pesisir”.
- Ringkasan empat kartu: total zona, zona bisa dikaji, zona perlu survei, zona tidak memenuhi screening.
- Informasi **status sistem**: `DEMO`, `RULE-BASED`, `MODEL TRAINED — NOT VALIDATED`, atau `MODEL VALIDATED`.
- Tombol “Mulai Analisis”, “Lihat Peta”, “Impor Dataset”.
- Catatan bahwa hasil tidak menggantikan kajian lapangan.

### E.2. Peta Kawasan (`pages/2_Peta.py`)

- Basemap (OpenStreetMap, satelit hanya jika layanan dan izin tersedia).
- Polygon kandidat zona dengan warna **status kelayakan**; satu layer terpisah untuk **kelas kesesuaian model**.
- Layer opsional: tutupan mangrove saat ini, garis pantai historis, batas administrasi, sumber data.
- Search zona, filter status, kontrol legenda, info skala, koordinat klik.
- Klik polygon membuka panel nama zona, luas, status data, ringkasan faktor dan tombol “Analisis”.
- Visual “data hilang” dengan warna netral/arsiran; jangan otomatis diberi warna hijau/merah.

### E.3. Analisis Lokasi (`pages/3_Analisis.py`)

Input: pilih zona/unggah data/form manual.  
Output: screening → fitur tersedia → hasil model jika valid → faktor utama → rekomendasi, disertai sumber data dan cap waktu.

Sediakan tampilan tab:
1. Data input dan kelengkapan.
2. Hasil screening.
3. Hasil model (jika tersedia).
4. Penjelasan SHAP (jika tersedia).
5. Rekomendasi dan verifikasi ahli.

Tampilkan **NO_MODEL_AVAILABLE** jika belum ada artefak ML. Jangan mengganti hasil model dengan skor acak.

### E.4. Perbandingan Zona (`pages/4_Perbandingan.py`)

- Tabel per zona: ID, nama, luas ha, screening, kelas habitat, kelengkapan data, urgensi degradasi, opsi tindakan, tingkat keyakinan/ketidakpastian.
- Filter dan sort berdasarkan kriteria yang dipilih.
- Grafik berdampingan untuk dua/tiga zona.
- Ekspor CSV/GeoJSON; jelaskan bahwa **prioritas survei** tidak sama dengan “pasti berhasil ditanami”.

### E.5. Dataset dan Model (`pages/5_Data_Model.py`)

- Upload/unduh template CSV dan GeoJSON.
- Data dictionary, kelengkapan, nilai tidak valid, sumber, tanggal, rentang spasial.
- Status model, versi, tanggal latih, target label, metrik validasi, area pelatihan dan area uji.
- Jika belum ada label valid: tampilkan “Model belum tersedia; mode penilaian berbasis aturan digunakan”.
- Admin bisa memilih artefak model terverifikasi; jangan menerima sembarang file pickle dari pengguna umum.

### E.6. Tentang & Metodologi (`pages/6_Metodologi.py`)

- Penjelasan XGBoost vs SHAP dengan bahasa Indonesia.
- Pemisahan screening ekologis, prediksi habitat, dan prioritas tindakan.
- Sumber data, batasan spasial dan ketidakpastian.
- Penjelasan bahwa SHAP menunjukkan kontribusi **terhadap prediksi model**, bukan bukti kausalitas.

---

## F. Dataset dan Parameter

### F.1. Data esensial dan pilihan

| Field teknis | Unit/tipe | Mengapa penting | Sumber yang disarankan | Kewajiban |
|---|---|---|---|---|
| `zone_id` | string unik | Identitas lokasi | Dibuat pengguna | Wajib |
| `zone_name` | string | Nama zona | Pengguna | Wajib |
| `geometry` | GeoJSON polygon/point | Lokasi dan batas | Pengguna/GIS | Wajib |
| `landcover_type` | kategori | Menyaring nonhabitat | Peta/survei | Wajib untuk keputusan final |
| `legal_status` | kategori | Batas izin/konservasi | Tata ruang/verifikasi | Wajib untuk keputusan final |
| `mangrove_cover_pct` | 0–100% | Tutupan eksisting | GMW/survei | Dianjurkan |
| `ndvi` | -1 s.d. 1 | Kondisi vegetasi/permukaan | Sentinel-2 | Opsional |
| `ndmi` | -1 s.d. 1 | Proksi kandungan air vegetasi | Sentinel-2 | Opsional |
| `elevation_m` | meter + datum | Posisi topografi | DEMNAS/survei | Dianjurkan; datum wajib |
| `inundation_duration_h_day` | jam/hari | Hidroperiode lokal | Logger/model/survei | Penting untuk kelayakan |
| `tidal_connectivity` | baik/terganggu/tidak diketahui | Akses pasang surut | Survei | Penting |
| `salinity_ppt` | ppt | Kondisi salinitas | Survei | Penting |
| `substrate_type` | lumpur/pasir/campuran/lainnya | Habitat penanaman | Survei | Penting |
| `wave_exposure` | rendah/sedang/tinggi/tidak diketahui | Energi gelombang | Kajian/survei | Penting |
| `shoreline_change_m_y` | m/tahun | Abrasi/sedimentasi historis | Analisis multiwaktu | Opsional |
| `natural_recruitment` | ada/tidak/tidak diketahui | Peluang regenerasi alami | Survei | Penting |
| `propagule_supply` | cukup/terbatas/tidak diketahui | Kebutuhan penanaman | Survei | Penting |
| `accessibility` | kategori | Kelayakan logistik | Survei | Opsional |
| `observation_date` | ISO YYYY-MM-DD | Umur data | Metadata | Wajib per observasi |
| `data_source` | string | Provenance | Metadata | Wajib per observasi |
| `quality_flag` | measured/modelled/estimated/demo/missing | Kepercayaan | Metadata | Wajib per observasi |

**Aturan penting:** kosong (`null`) bukan nol. Nilai `0` untuk salinitas, NDVI, atau perubahan garis pantai memiliki arti fisik dan tidak boleh dipakai sebagai pengganti data kosong.

### F.2. Dataset terbuka yang relevan

1. **Global Mangrove Watch v4.1:** sebaran dan perubahan mangrove tahunan 1985–2025, raster 30 m. **Bukan label keberhasilan rehabilitasi**. Sumber: <https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm>.
2. **Sentinel-2 L2A Harmonized:** citra permukaan multispektral; band resolusi 10/20/60 m, reflektansi disimpan dengan faktor skala 10.000. Koleksi GEE: `COPERNICUS/S2_SR_HARMONIZED`. Sumber: <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED>.
3. **DEMNAS/BIG:** elevasi topografi. Penggunaan untuk zona pasang surut harus memerhatikan datum vertikal, bias vegetasi dan validasi lokal. Sumber: <https://tanahair.indonesia.go.id/> (cek layanan dan ketersediaan).
4. **Pengukuran lokal:** salinitas, substrat, konektivitas air, hidroperiode, dan propagul. Tidak boleh disamakan dengan produk citra satelit.
5. **Data administrasi/status lahan:** verifikasi melalui pemerintah/instansi berwenang dan/atau data resmi sebelum rekomendasi implementasi.

Wajib menyimpan `provider`, `dataset_name`, `dataset_version`, `observation_date`, `download_date`, `spatial_resolution_m`, `license`, `source_url`, `processing_method`, dan `quality_flag` sejauh tersedia.

### F.3. Rumus indikator citra

Untuk Sentinel-2 setelah nilai reflektansi diskalakan menjadi 0–1:

```text
NDVI = (B8 - B4) / (B8 + B4)
NDMI = (B8 - B11) / (B8 + B11)
```

- `B8`: near-infrared (NIR), `B4`: red, `B11`: shortwave infrared (SWIR).
- Terapkan masking awan/bayangan dan tangani denominator nol.
- Jangan menafsirkan NDMI sebagai pengukuran langsung kelembapan tanah atau salinitas.
- Harmonisasikan resolusi 10 m vs 20 m dengan resampling terdokumentasi; hindari mengklaim resolusi 10 m untuk produk awal 20/30 m.

### F.4. Sistem koordinat

- Impor/ekspor GeoJSON: **EPSG:4326** `[longitude, latitude]` mengikuti spesifikasi GeoJSON.
- Untuk **menghitung luas (hektare)** dan jarak: proyeksikan ke CRS metrik yang sesuai (misalnya UTM setempat atau equal-area), bukan luas derajat pada EPSG:4326.
- Terapkan pemeriksaan validitas polygon, self-intersection, duplicate IDs, nilai latitude/longitude, dan batas luar lokasi.
- Jika zona meliputi lebih dari satu UTM, gunakan CRS equal-area yang sesuai.
- Jangan gunakan DEM tanpa mengetahui referensi vertikal untuk menyimpulkan elevasi relatif terhadap pasang surut.

---

## G. Skema Data Impor dan Penyimpanan

### G.1. CSV contoh untuk titik/sampel (semua angka di bawah **simulasi**)

```csv
zone_id,zone_name,longitude,latitude,landcover_type,legal_status,mangrove_cover_pct,ndvi,ndmi,elevation_m,inundation_duration_h_day,tidal_connectivity,salinity_ppt,substrate_type,wave_exposure,shoreline_change_m_y,natural_recruitment,propagule_supply,observation_date,data_source,quality_flag
SIM-A,Zona Simulasi A,112.500,-6.900,coastal_mudflat,perlu_verifikasi,15,0.31,0.12,0.40,5,baik,22,lumpur,rendah,-0.8,ada,cukup,2026-01-01,SYNTHETIC_DEMO,demo
SIM-B,Zona Simulasi B,112.510,-6.910,degraded_coastal,perlu_verifikasi,5,0.14,0.05,0.65,1,terganggu,31,campuran,sedang,-1.4,tidak,terbatas,2026-01-01,SYNTHETIC_DEMO,demo
SIM-C,Zona Simulasi C,112.520,-6.920,sandy_beach,perlu_verifikasi,0,0.02,-0.03,0.80,,tidak_diketahui,,pasir,tinggi,-2.1,tidak,tidak_diketahui,2026-01-01,SYNTHETIC_DEMO,demo
```

Penting: koordinat **fiktif untuk menguji sistem**, bukan lokasi rehabilitasi nyata. Kolom kosong harus terbaca sebagai `null`. Lokasi titik **bukan polygon area** dan tidak boleh otomatis diberi luas.

### G.2. Contoh GeoJSON minimal

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "zone_id": "SIM-01",
        "zone_name": "Zona Polygon Contoh",
        "data_source": "SYNTHETIC_DEMO",
        "quality_flag": "demo"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[112.49,-6.90],[112.50,-6.90],[112.50,-6.91],[112.49,-6.91],[112.49,-6.90]]]
      }
    }
  ]
}
```

### G.3. Entitas penyimpanan

| Entitas | Kolom minimal |
|---|---|
| `zones` | `id`, `name`, `geometry_json`, `landcover_type`, `legal_status`, `created_at`, `updated_at` |
| `observations` | `id`, `zone_id`, `parameter`, `value`, `unit`, `date`, `source`, `quality_flag`, `method`, `datum` |
| `datasets` | `id`, `name`, `version`, `url`, `license`, `date_imported`, `checksum` |
| `models` | `id`, `version`, `target`, `feature_schema`, `metrics_json`, `training_area`, `status`, `artifact_path` |
| `analyses` | `id`, `zone_id`, `timestamp`, `screening_status`, `model_id_nullable`, `prediction_nullable`, `recommendation`, `warnings_json` |
| `reviews` | `id`, `analysis_id`, `reviewer`, `notes`, `decision`, `reviewed_at` |

Saat analisis dijalankan, simpan *snapshot* fitur dan versi model/aturan yang digunakan agar hasil dapat direproduksi.

---

## H. Pipeline Analisis dan Machine Learning

### H.1. Urutan pipeline (jangan dibalik)

```text
[Zona dipilih / data diimpor]
           |
           v
[Validasi file, geometri, satuan, sumber, tanggal]
           |
           v
[Ecological & legal screening]
      |              |
      |              +--> EXCLUDED / NEEDS REVIEW -> Jelaskan alasan, tidak ada "tanam"
      v
[Eligible + kelengkapan fitur]
           |
           +--> Model tidak ada / fitur tidak valid -> RULE-BASED / NEEDS DATA
           |
           v
[XGBoost model terlatih] -> [Prediksi kesesuaian habitat]
           |
           v
[SHAP] -> [Faktor kontribusi prediksi]
           |
           v
[Rules keputusan ekologis + kelayakan lapangan]
           |
           v
[Rekomendasi & prioritas survei / tindakan]
           |
           v
[Review ahli -> ekspor dan penyimpanan]
```

### H.2. Definisi label ML

**Pilih salah satu target yang benar-benar didukung dataset.** Jangan menggabungkan definisinya:

- **Target MVP dengan ML (jika dataset tersedia):** `habitat_suitability` atau probabilitas kehadiran habitat mangrove **di area yang secara ekologis memenuhi screening**. Positif/negatif harus berasal dari pengamatan atau data referensi independen yang dapat ditelusuri.
- **Target lanjutan:** `restoration_outcome_12m` (contoh: tingkat hidup bibit 12 bulan, pertumbuhan/regenerasi) **hanya apabila ada catatan rehabilitasi nyata** lengkap dengan intervensi dan kondisi awal.
- Jika pelabelan hanya menggunakan GMW tahun yang sama dengan variabel tutupan mangrove, berisiko **label leakage** dan hasil terlalu optimistis. Jangan memasukkan turunan label ke fitur.
- Titik non-mangrove tidak otomatis negatif ekologis; bisa merupakan area terdegradasi, lahan nonhabitat atau wilayah belum disurvei. Butuh strategi sampling negatif yang ditinjau ahli.

### H.3. Fitur awal kandidat model

Kelompok variabel: hidroperiode/inundasi, konektivitas pasang surut, salinitas, substrat, elevasi yang terkalibrasi datum, paparan gelombang, perubahan garis pantai, indeks vegetasi, dan karakteristik tutupan historis.

**Ketersediaan dan kualitas data lebih penting daripada jumlah parameter.** Jika observasi kunci tidak ada, aplikasi menyatakan `INSUFFICIENT_DATA`, bukan mengisi nilai rata-rata tanpa peringatan.

### H.4. Training XGBoost (hanya saat label valid tersedia)

1. Data cleaning: tipe, rentang, unit, missing, duplikasi, outlier dan provenance.
2. Pisahkan **train/validation/test** berdasarkan **blok lokasi** dan/atau periode waktu, bukan acak antar-piksel yang berdekatan.
3. Buat baseline sederhana: logistic regression/random forest atau aturan ahli.
4. Pipeline preprocessing di-fit **hanya pada data train**; encoding/imputasi tidak boleh mempelajari data test.
5. Latih `XGBClassifier` dengan hyperparameter awal yang dapat dituning; rekam `random_state`, split dan versi data.
6. Gunakan evaluasi yang tepat: balanced accuracy, F1, precision/recall, PR-AUC, ROC-AUC bila sesuai, confusion matrix dan kalibrasi probabilitas.
7. Uji generalisasi ke lokasi pesisir yang **berbeda**; laporkan ketidakpastian dan domain ketidaksesuaian distribusi.
8. Kalibrasi probabilitas jika diperlukan berdasarkan validasi terpisah; hindari menyebut skor sebagai probabilitas jika belum dikalibrasi.
9. Simpan model, kolom fitur, encoder, metrik, tanggal, training domain dan **versi dataset**.
10. Aktifkan model di UI hanya jika schema input cocok, artefak dapat dimuat, dan pengujiannya dapat dipertanggungjawabkan.

**Pengaturan awal model (hipotesis tuning, bukan optimum):** `n_estimators=300`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `objective=binary:logistic`, `eval_metric=logloss`, `random_state=42`. Evaluasi dan revisi parameter, jangan mengklaim setting terbaik sebelum eksperimen.

### H.5. SHAP

- Gunakan `shap.TreeExplainer` pada model XGBoost yang benar-benar menghasilkan prediksi.
- Untuk klasifikasi biner, **periksa ruang output SHAP** (log-odds/raw atau probability). Dalam ruang raw, nilai SHAP **bukan langsung persentase peluang**.
- Tampilkan **top 5** fitur penyumbang prediksi per zona, arah kontribusi, besaran, dan nilai input.
- Pisahkan **SHAP global** (ringkasan seluruh sampel) dan **SHAP lokal** (zona terpilih).
- Jika model/baseline belum ada, tab SHAP menampilkan pesan penjelas, bukan plot simulasi yang menyerupai hasil model.
- Tampilan contoh: “Pada model ini, fitur X meningkatkan skor prediksi. Hal ini tidak membuktikan X sebagai penyebab ekologis.”

### H.6. Contoh pseudocode inferensi aman

```python
def analyse_zone(zone, observed_data, active_model=None):
    features, data_warnings = validate_and_prepare(zone, observed_data)
    screening = ecological_screening(zone, features)

    if screening.status == "EXCLUDED":
        return result(screening=screening, model_output=None,
                      recommendation="Tidak merekomendasikan penanaman")
    if screening.status == "NEEDS_REVIEW":
        return result(screening=screening, model_output=None,
                      recommendation="Survei/verifikasi diperlukan")

    if active_model is None or not active_model.is_approved:
        return result(screening=screening, model_output=None,
                      recommendation=rules_only_recommendation(features),
                      mode="RULE_BASED")

    if not active_model.features_available(features):
        return result(screening=screening, model_output=None,
                      recommendation="Lengkapi parameter model", mode="INSUFFICIENT_DATA")

    score = active_model.predict_suitability(features)
    explanations = active_model.explain_with_shap(features)
    advice = recommendation_engine(screening, features, score)
    return result(screening=screening, model_output=score,
                  explanations=explanations, recommendation=advice,
                  model_version=active_model.version)
```

Implementasi asli boleh berbeda, tetapi pemisahan screening dan prediksi **harus dipertahankan**.

---

## I. Aturan Keputusan Ekologis dan Prioritisasi

### I.1. Status screening yang harus tersedia

- `ELIGIBLE`: lokasi secara awal memenuhi syarat untuk evaluasi lanjutan; **bukan izin tanam**.
- `NEEDS_REVIEW`: data penting, izin, atau kelayakan ekologis belum pasti.
- `EXCLUDED`: terdapat pembatas jelas; misalnya kawasan nonhabitat atau larangan aktivitas tanpa izin.

### I.2. Aturan rekomendasi awal

| Sinyal/kondisi | Tindakan awal di dashboard | Catatan |
|---|---|---|
| Mangrove sehat/eksisting | **Lindungi dan pantau** | Bukan sasaran penanaman ulang otomatis |
| Habitat layak, propagul & regenerasi alami tersedia | **Fasilitasi regenerasi alami** | Pantau rekrutmen dan kondisi hidrologi |
| Konektivitas pasang surut terganggu | **Kaji pemulihan hidrologi** | Memerlukan kajian teknik, izin, dan ahli |
| Habitat layak, propagul alami terbatas | **Pertimbangkan penanaman terbatas** | Survei spesies, musim, dan substrat terlebih dahulu |
| Abrasi/gelombang tinggi atau substrat tidak stabil | **Kaji dinamika pantai / tunda tanam** | Penanaman langsung mungkin tidak efektif |
| Status lahan dan/atau parameter inti tidak diketahui | **Wajib verifikasi lapangan** | Jangan diberi status “siap ditanam” |
| Nonhabitat mangrove atau batas legal melarang | **Tidak direkomendasikan** | Jangan berikan skor layak tanam |

**Seluruh aturan di atas adalah panduan konsep awal**. Buat `rules.yaml` agar dapat disunting setelah telaah ahli; jangan hardcode ambang salinitas, elevasi atau hidroperiode universal tanpa dasar lokasi/spesies.

### I.3. Pisahkan tiga hasil yang sering tercampur

1. **Kesesuaian habitat:** apakah kondisi ekologis mendukung mangrove? (output model jika tersedia).
2. **Urgensi intervensi:** seberapa perlu lokasi ditangani? (indikasi degradasi, ancaman/risiko, dll.).
3. **Kesiapan tindakan:** apakah kondisi lapangan, sosial, legal dan data cukup untuk bertindak?

**Prioritas program** hanya dihitung untuk zona yang lolos screening, dengan bobot yang **dapat dikonfigurasi dan ditinjau ahli**. Untuk MVP, lebih aman gunakan *kategori keputusan* dan *urutan survei* tanpa mengarang skor komposit “ilmiah”.

### I.4. Status dashboard

- **Hijau:** tersedia data cukup dan direkomendasikan untuk evaluasi restorasi lanjut.
- **Kuning:** memerlukan perbaikan kondisi, verifikasi, atau data tambahan.
- **Merah:** tidak cocok/terbatas berdasarkan screening atau risiko yang jelas.
- **Abu-abu:** belum ada data atau analisis belum dijalankan.

Legenda **harus menyebut dasar klasifikasi** (screening, ML, atau prioritas) dan tidak mencampur makna hijau dengan “pasti berhasil ditanam”.

---

## J. Alur Interaksi Pengguna (User Journey)

**Alur 1 — Demo tanpa dataset asli**

1. Pengguna klik “Lihat Simulasi”.
2. Sistem menampilkan 3 polygon contoh, label jelas `SIMULASI`.
3. Pengguna memilih satu zona.
4. Muncul metadata fitur sintetik dan hasil **rule-based screening**.
5. Jika model AI belum tersedia, sistem **tidak** menampilkan probabilitas XGBoost atau SHAP palsu.
6. Pengguna melihat rekomendasi beserta alasan; bisa unduh ringkasan berwatermark `SIMULASI`.

**Alur 2 — Analisis data pengguna**

1. Analis impor CSV/GeoJSON dengan metadata sumber.
2. Sistem validasi skema, geometri, kualitas, tanggal dan unit.
3. Pengguna memperbaiki error/menandai data yang tidak tersedia.
4. Sistem menjalankan screening.
5. Jika model tervalidasi siap dan fitur cocok, pengguna dapat memilih “Prediksi XGBoost”.
6. Hasil model + SHAP + rekomendasi disajikan terpisah.
7. Pengguna mencatat keputusan verifikator dan mengekspor laporan.

**Alur 3 — Perbandingan wilayah**

1. Analis memilih 2–5 zona.
2. Aplikasi menampilkan tabel perbandingan kondisi dan status.
3. Aplikasi memberi prioritas *survey* atau *aksi awal* dengan alasan transparan.
4. Pengguna mengunduh CSV/GeoJSON dan catatan kebutuhan verifikasi.

---

## K. Kontrak Layanan Internal / API Masa Depan

Untuk MVP Streamlit, fungsi service cukup; **tidak wajib** membuat server REST. Namun gunakan kontrak data yang memudahkan migrasi ke FastAPI.

| Fungsi atau endpoint opsional | Input | Output |
|---|---|---|
| `create_zone()` / `POST /api/zones` | GeoJSON + metadata | `zone_id`, status validasi |
| `list_zones()` / `GET /api/zones` | Filter bbox/status | Ringkasan zona |
| `validate_dataset()` / `POST /api/import/validate` | CSV/GeoJSON | Errors, warnings, schema summary |
| `run_screening()` / `POST /api/screen` | `zone_id` | Screening + reasons |
| `run_analysis()` / `POST /api/analyse` | `zone_id`, `model_version?` | Result + warnings + advice |
| `compare_zones()` / `POST /api/compare` | Array `zone_id` | Ranked comparison |
| `get_model_status()` / `GET /api/model` | - | Status, version, target, metrics |
| `export_results()` / `GET /api/export` | Format, zone IDs | File unduhan |

**Contoh output analisis dengan model belum tersedia:**

```json
{
  "zone_id": "SIM-A",
  "analysis_mode": "RULE_BASED",
  "data_quality": "DEMO",
  "screening": {
    "status": "NEEDS_REVIEW",
    "reasons": ["Status legal belum diverifikasi"]
  },
  "model": {
    "status": "NOT_AVAILABLE",
    "version": null,
    "target": null,
    "suitability_score": null,
    "shap_factors": null
  },
  "recommended_action": "Verifikasi status lahan sebelum tindakan",
  "human_review_required": true,
  "warnings": ["SIMULASI: bukan data lapangan atau hasil prediksi AI"]
}
```

Status sukses/error API agar konsisten: `VALIDATION_ERROR`, `INVALID_GEOMETRY`, `MISSING_REQUIRED_FEATURES`, `NO_MODEL_AVAILABLE`, `OUT_OF_DOMAIN`, `INSUFFICIENT_DATA`, `IMPORT_ERROR`, `INTERNAL_ERROR`.

---

## L. Struktur Proyek yang Diminta

```text
mangrove-fit/
├── README.md
├── requirements.txt                 # versi dipin setelah testing
├── .env.example
├── .gitignore
├── app.py                           # entrypoint Streamlit
├── pages/
│   ├── 1_Beranda.py
│   ├── 2_Peta.py
│   ├── 3_Analisis.py
│   ├── 4_Perbandingan.py
│   ├── 5_Data_Model.py
│   └── 6_Metodologi.py
├── mangrove_fit/
│   ├── config.py
│   ├── schemas.py
│   ├── database.py
│   ├── data_io.py
│   ├── geospatial.py
│   ├── preprocessing.py
│   ├── screening.py
│   ├── recommendations.py
│   ├── prioritization.py
│   ├── model_service.py
│   ├── explain_service.py
│   ├── report_service.py
│   └── ui_components.py
├── config/
│   ├── rules.yaml
│   └── demo_mode.yaml
├── data/
│   ├── demo/                          # hanya contoh sintetik
│   ├── raw/                           # .gitignore jika privat/berukuran besar
│   ├── processed/
│   └── app.db
├── models/
│   └── README.md                      # belum ada model sampai terlatih
├── notebooks/
│   └── train_xgboost.ipynb            # tahap jika label tersedia
├── scripts/
│   ├── seed_demo.py
│   └── check_data.py
├── tests/
│   ├── test_import.py
│   ├── test_geospatial.py
│   ├── test_screening.py
│   ├── test_recommendations.py
│   ├── test_ml_status.py
│   └── test_export.py
└── docs/
    ├── data_dictionary.md
    ├── architecture.md
    ├── limitations.md
    └── deployment.md
```

### L.1. Perintah instalasi lokal yang harus didukung

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_demo.py
streamlit run app.py
```

`.env.example` minimal:

```dotenv
APP_MODE=demo
DATABASE_URL=sqlite:///data/app.db
MODEL_ARTIFACT_PATH=
MAP_DEFAULT_LAT=-6.9
MAP_DEFAULT_LON=112.5
MAP_DEFAULT_ZOOM=10
MAX_UPLOAD_MB=10
# Opsional tahap lanjutan:
GEE_PROJECT_ID=
```

Jangan meng-commit kredensial Earth Engine, access token atau data sensitif. File demo tetap diberi status sintetik. Pastikan folder data dibuat otomatis pada startup bila belum ada.

---

## M. Desain UI/UX yang Diharapkan

**Arah tampilan:** profesional, ramah lingkungan, dan mudah dibaca untuk pengguna non-teknis.

- Warna utama hijau mangrove tua + netral; gunakan merah/kuning/hijau hanya untuk status nyata yang dijelaskan legenda.
- Sidebar: Beranda, Peta, Analisis, Perbandingan, Data & Model, Metodologi.
- Peta dominan pada halaman Peta; panel kanan menampilkan data zona dan hasil analisis.
- Jangan memenuhi halaman dengan grafik yang tidak memiliki data.
- Setiap angka memiliki label **unit, sumber, tanggal pengamatan**, dan kualitas.
- Tombol “Analisis Lokasi”, “Tinjau Data”, “Bandingkan Zona”, “Unduh Ringkasan”.
- Gunakan tooltips menjelaskan: NDVI, hidroperiode, SHAP, screening, suitability.
- Rancang empty state: belum ada zona, belum ada data, model belum dilatih, validasi gagal.
- Dukung layar laptop; untuk seluler cukup layout responsif dasar.
- Semua file ekspor harus menyertakan `analysis_mode`, `data_quality`, `model_version`, `analysis_timestamp`.

**Mock ringkas halaman Analisis**:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ MANGROVE-FIT   Beranda | Peta | Analisis | Perbandingan | Data      │
├───────────────────────┬─────────────────────────────────────────────┤
│ PETA / ZONA PESISIR   │ ZONA B — Status: MEMERLUKAN VERIFIKASI      │
│                       │ Sumber data: demo / lapangan / satelit       │
│ [Polygon hijau]       │ [Kelengkapan data] [Status screening]        │
│ [Polygon kuning]      │                                             │
│ [Polygon abu-abu]     │ Habitat suitability: Tidak tersedia (*)     │
│                       │ XGBoost: Model belum tersedia               │
│ Klik lokasi           │ SHAP: Tidak tersedia                       │
│                       │                                             │
│                       │ Rekomendasi awal: survei hidrologi           │
│                       │ Alasan: konektivitas belum terverifikasi    │
│                       │ [Unduh Ringkasan] [Bandingkan Zona]         │
└───────────────────────┴─────────────────────────────────────────────┘
(*) Jangan tampilkan angka jika model/label belum valid.
```

---

## N. Keamanan, Mutu Data, dan Performa

### N.1. Keamanan minimum

- Batasi berkas unggahan (contoh 10 MB configurable), tipe MIME/ekstensi, serta jumlah geometri/titik.
- Validasi isi sebenarnya; penamaan berkas dinormalisasi untuk mencegah path traversal.
- Hindari menjalankan artefak pickle/joblib dari pengguna tidak tepercaya. Model diunggah hanya oleh admin dan diverifikasi.
- Jangan mengeksekusi string ekspresi dari CSV/YAML pengguna.
- Hindari mengekspor formula spreadsheet mentah bila nilai sel berawalan `=`, `+`, `-`, `@` dari input teks.
- Data lokasi komunitas atau lokasi konservasi sensitif perlu akses dan distribusi yang sesuai.
- Untuk produksi, gunakan HTTPS, autentikasi, backup, dan logging sesuai kebutuhan.

### N.2. Kualitas dan kesesuaian data

- Validasi unit (`ppt`, `m`, `m/tahun`, `%`), rentang fisik, tanggal dan sumber.
- Tampilkan **data confidence** berbasis kelengkapan dan sumber, jangan samakan dengan confidence model.
- Pantau input **out-of-distribution** saat model ada: lokasi di luar domain pelatihan harus diberi peringatan dan boleh ditolak.
- Jika data salinitas/hidroperiode krusial tidak tersedia: rekomendasi = **verifikasi**, bukan “lokasi layak tanam”.
- Model tidak perlu dipaksa mengeluarkan skor untuk semua wilayah.

### N.3. Kinerja minimum MVP

- Dapat dijalankan lokal pada laptop biasa tanpa GPU.
- 3 polygon demo dan puluhan zona dapat dimuat dengan lancar; pengujian performa dilakukan setelah implementasi.
- Panggilan pemrosesan berat menggunakan cache yang sesuai tetapi perubahan data harus invalidasi cache.
- Jika layanan basemap/data eksternal gagal, aplikasi tetap menampilkan data lokal dan pesan kesalahan yang jelas.

---

## O. Pengujian dan Kriteria Penerimaan (Acceptance Criteria)

Developer diminta menunjukkan bukti berupa screenshot/video demo + hasil `pytest`.

| ID | Skenario uji | Hasil yang diwajibkan |
|---|---|---|
| AT-01 | Jalankan dari README pada laptop baru | Aplikasi terbuka tanpa kesalahan impor |
| AT-02 | Pilih salah satu zona demo | Polygon/marker dipilih, metadata tampil |
| AT-03 | Klik zona dengan data kurang | Tampil `NEEDS_REVIEW`, bukan skor palsu |
| AT-04 | Unggah CSV template sah | Data diterima, nama dan koordinat benar |
| AT-05 | Unggah CSV dengan lat 120 | Ditolak dengan pesan rentang latitude |
| AT-06 | Unggah GeoJSON polygon self-intersecting | Ditolak atau diperbaiki dengan pemberitahuan |
| AT-07 | Input salinitas kosong | Tersimpan `null`, bukan `0` |
| AT-08 | Input lokasi nonhabitat/larangan legal | Tidak diberi rekomendasi “langsung tanam” |
| AT-09 | Model tidak ada | UI menampilkan `NO_MODEL_AVAILABLE`, SHAP tidak dibuat |
| AT-10 | Model tersedia tetapi fitur salah | Ditolak, tampil `MISSING_REQUIRED_FEATURES` |
| AT-11 | Uji SHAP model nyata | Faktor dan output konsisten dengan model serta ruang output |
| AT-12 | Bandingkan 3 zona | Tabel, alasan dan urutan hasil tampil |
| AT-13 | Ekspor CSV/GeoJSON | Geometri, metadata mode, sumber dan tanggal terbawa |
| AT-14 | Hitung luas polygon | Hektare dihitung dari proyeksi metrik yang benar |
| AT-15 | Ganti zona dan refresh | Data dan status tidak tertukar |
| AT-16 | Matikan koneksi internet | Data lokal/demo masih bisa ditampilkan; basemap gagal secara elegan |
| AT-17 | Unggah file terlalu besar/format salah | Validasi menolak dan tidak crash |
| AT-18 | Ekspor mode demo | File jelas mencantumkan `SIMULASI` |

**Definisi selesai MVP:** AT-01 sampai AT-10, AT-12, AT-14, AT-15, AT-17, AT-18 berhasil. AT-11 hanya berlaku jika model benar-benar tersedia. AT-13 dan AT-16 diselesaikan sejauh kemampuan komponen peta/file lokal.

---

## P. Tahapan Implementasi untuk Teman Pengembang

### Sprint 1 — Kerangka dan peta

- [ ] Inisialisasi repositori + environment.
- [ ] Streamlit multipage dan tema.
- [ ] Modul GeoJSON/CSV import dan validator.
- [ ] Penyimpanan SQLite sederhana.
- [ ] Peta interaktif dengan klik zona dan tabel metadata.
- [ ] Tiga zona demo sintetik.

**Hasil:** peta dapat dipilih dan data tidak hilang selama sesi tersimpan.

### Sprint 2 — Screening dan keputusan

- [ ] Modul aturan screening ekologis/legal.
- [ ] Form input data dengan nilai null dan sumber.
- [ ] Rule-based recommendation engine beserta alasan.
- [ ] Halaman analisis dan perbandingan.
- [ ] Ekspor hasil + metadata.
- [ ] Unit test data, geometri, screening dan rekomendasi.

**Hasil:** MVP konseptual yang fungsional tanpa memalsukan AI.

### Sprint 3 — Model XGBoost dan SHAP (bersyarat data)

- [ ] Audit ketersediaan **dataset dengan label sah**.
- [ ] Jika tidak ada label: tetap tampilkan `NO_MODEL_AVAILABLE`, lengkapi desain pipeline training.
- [ ] Jika ada label: training/validation/test spasial, baseline, metrik, model registry.
- [ ] Hubungkan inferensi model ke service.
- [ ] Hubungkan SHAP yang benar ke halaman analisis.
- [ ] Uji kalibrasi, generalisasi dan out-of-domain.

**Hasil:** kemampuan ML hanya diklaim ketika bukti pelatihan dan pengujian tersedia.

### Sprint 4 — Perapian dan handoff

- [ ] Responsif laptop/mobile, loading/error/empty states.
- [ ] Penjelasan metodologi/sumber/batasan.
- [ ] Dokumentasi README dan contoh input.
- [ ] Skrip pengujian dan tangkapan layar fitur.
- [ ] Paket demo lokal yang bisa dijalankan ulang.

---

## Q. Deliverables yang Harus Diserahkan Developer

1. **Source code** lengkap (`.py`, `requirements.txt`, konfigurasi) dan repositori.
2. `README.md` (instalasi Windows, cara run, cara import, troubleshooting).
3. **Aplikasi web fungsional** dengan peta, form, screening, rekomendasi, perbandingan, ekspor.
4. Dataset contoh sintetik CSV dan GeoJSON, jelas `SIMULASI`.
5. `docs/data_dictionary.md`, `docs/architecture.md`, `docs/limitations.md`.
6. Pengujian (`pytest`) dan daftar hasil acceptance test.
7. Screenshot: beranda, peta, analisis lokasi, penjelasan rekomendasi, perbandingan zona, halaman data/model.
8. Jika AI benar-benar dibuat: dataset/metadata yang legal dibagikan, notebook training, metrik evaluasi, model version, dan penjelasan SHAP.
9. Ringkasan komponen yang **sudah berjalan**, **masih simulasi**, dan **belum tersedia**.

---

## R. Definisi Kesuksesan Penelitian/Konsep

Hasil yang dapat dibenarkan dari MVP adalah:

> “Telah dirancang/dikembangkan prototipe aplikasi web MANGROVE-FIT yang mengintegrasikan data lingkungan pesisir, penyaringan kelayakan awal, serta rekomendasi rehabilitasi transparan. Arsitektur mendukung integrasi XGBoost dan SHAP setelah dataset berlabel serta validasi model tersedia.”

**Tidak boleh mengklaim** akurasi prediksi, persentase keberhasilan tanam, pengurangan biaya rehabilitasi, atau dampak ekologis sebagai hasil penelitian bila belum diukur.

**Indikator keberhasilan pengembangan teknis:** skema impor valid, peta dan data konsisten, aturan keputusan dapat diaudit, hasil dapat diekspor, tidak ada label model fiktif, dan seluruh acceptance test minimum dipenuhi.

**Indikator penelitian lanjutan:** performa model pada lokasi uji independen, kesepakatan rekomendasi dengan ahli, ketepatan prioritasi survei, serta evaluasi hasil rehabilitasi setelah intervensi.

---

## S. Referensi Teknis dan Ilmiah untuk Pengembang

Rujukan berikut digunakan untuk memilih pendekatan teknis dan menjaga ketepatan klaim. Periksa versi, lisensi, cakupan waktu, dan ketersediaan layanan saat implementasi.

1. **Wetlands International Indonesia — *Mangrove restoration: to plant or not to plant?*** Panduan yang menekankan restorasi kondisi ekologis dan regenerasi alami.  
   <https://indonesia.wetlands.org/publication/mangrove-restoration-to-plant-or-not-to-plant/>
2. **JAXA / Global Mangrove Watch — Dataset v4.1.** Peta perubahan mangrove, 1985–2025, 30 m; bukan label keberhasilan penanaman.  
   <https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm>
3. **Google Earth Engine — Harmonized Sentinel-2 L2A Surface Reflectance.** Deskripsi band, skala reflektansi, data, dan caveat.  
   <https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED>
4. **XGBoost — dokumentasi Python dan scikit-learn interface.**  
   <https://xgboost.readthedocs.io/en/stable/python/python_api.html>
5. **SHAP — TreeExplainer.** Perbedaan output raw/log-odds vs probability dan konfigurasi penjelasan.  
   <https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html>
6. **Streamlit — dokumentasi resmi.**  
   <https://docs.streamlit.io/>
7. **GeoJSON — RFC 7946.**  
   <https://www.rfc-editor.org/rfc/rfc7946>
8. **Mangrove Rehabilitation Guidelines (2024).** Pentingnya menilai hidrologi sebelum memutuskan penanaman.  
   <https://www.pilbaraports.com.au/about-pilbara-ports/publications/forms-and-publications/forms-and-publications/guideline/2024/may/mangrove-rehabilitation-guidelines>

### Catatan lomba IT RUSH 2026

Menurut guidebook yang diberikan, esai bersifat ilmiah populer, isi 3–5 halaman, dapat berupa gagasan/telaah pustaka, dan prototipe **tidak diwajibkan**. Aplikasi ini dapat menjadi proof-of-concept pendukung esai, **bukan alasan untuk menyajikan data buatan sebagai hasil penelitian**. Patuhi pernyataan penggunaan AI dan ketentuan orisinalitas panitia.

---

## T. Instruksi Singkat yang Dapat Disalin ke Teman

> Buatkan aplikasi web **MANGROVE-FIT** menggunakan Python + Streamlit sesuai seluruh spesifikasi pada file ini. Fokusnya **pesisir pantai**, bukan hanya lahan bekas tambak. Mulai dari **MVP fungsional**, meliputi peta interaktif, impor CSV/GeoJSON, input data hidrologi-geospasial, pemeriksaan kelayakan ekologis dan legal, rekomendasi tindakan restorasi, perbandingan zona, serta ekspor. Pakai dataset DEMO sintetik yang jelas diberi label; jangan memalsukan hasil XGBoost/SHAP. Siapkan modul XGBoost dan SHAP sebagai tahap lanjutan jika dataset berlabel valid tersedia. Sertakan source code, README, file contoh, dan test. Sebelum coding, tampilkan struktur proyek, pembagian modul, dan urutan implementasi; lalu kerjakan sampai aplikasi bisa dijalankan lokal.

**Prioritas desain terpenting:** sistem harus lebih berguna daripada peta tutupan mangrove biasa, yakni menjawab **“lokasi ini perlu ditanami, dipulihkan hidrologinya, dibiarkan beregenerasi, dilindungi, atau perlu disurvei dulu?”**, beserta alasan dan status keandalan datanya.

