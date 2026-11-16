# Metodologi — MANGROVE-FIT

> **Versi:** MVP 0.1 · 16 November 2026  
> **Status:** Rule-based screening aktif; XGBoost dan SHAP belum tersedia

---

## 1. Alur Analisis Keseluruhan

```
[Input: Zona pesisir + observasi parameter]
              |
              v
[1. Validasi data]
  - Format, geometri, satuan, rentang fisik
  - Null ≠ 0; metadata sumber wajib
              |
              v
[2. Ecological & Legal Screening]
  - Cek jenis tutupan (nonhabitat → EXCLUDED)
  - Cek status legal (dilarang → EXCLUDED)
  - Cek ketersediaan 7 parameter inti
              |
        +-----+-----+
        |           |
        v           v
  EXCLUDED     NEEDS_REVIEW / ELIGIBLE
  Stop         Lanjut →
                      |
                      v
         [3. Penilaian kelengkapan data]
           - % parameter inti tersedia
           - Kualitas sumber per observasi
                      |
              +--------+--------+
              |                 |
              v                 v
    [4a. Rule-based]    [4b. XGBoost] ← hanya jika model
     Recommendation      Prediction     tervalidasi tersedia
              |                 |
              v                 v
         [5. Rekomendasi & Prioritas Survei]
              |
              v
         [6. Review Ahli + Ekspor]
```

---

## 2. Penyaringan Ekologis (Screening)

### 2.1 Tiga Status Hasil

| Status | Kondisi | Langkah selanjutnya |
|---|---|---|
| `ELIGIBLE` | Tutupan mendukung habitat, legal tidak dilarang, ada data inti | Kajian lanjutan dan verifikasi parameter |
| `NEEDS_REVIEW` | Legal belum pasti, data penting kosong, atau sinyal degradasi | Survei untuk melengkapi data |
| `EXCLUDED` | Tutupan bukan habitat mangrove, atau legal dilarang | Tidak direkomendasikan untuk penanaman |

### 2.2 Urutan Pemeriksaan

1. **Tutupan lahan** — Jenis habitat yang dikecualikan: `coral_reef`, `seagrass`, `open_water`, `built_area`
2. **Status legal** — Langsung `EXCLUDED` jika `dilarang`; `NEEDS_REVIEW` jika `perlu_verifikasi`
3. **Ketersediaan 7 parameter inti:**
   - `inundation_duration_h_day`
   - `tidal_connectivity`
   - `salinity_ppt`
   - `substrate_type`
   - `wave_exposure`
   - `natural_recruitment`
   - `propagule_supply`

> Aturan lengkap dapat diperiksa di `config/rules.yaml`. Checksum file direkam per analisis untuk reproduksibilitas.

### 2.3 Keterbatasan Screening

- Ambang numerik (salinitas, elevasi, hidroperiode) **tidak ditetapkan** — tidak ada nilai universal yang berlaku untuk semua spesies dan lokasi
- Status `ELIGIBLE` bukan izin tanam; bukan jaminan keberhasilan rehabilitasi
- Aturan merupakan konsep awal yang memerlukan telaah ahli ekologi pesisir setempat

---

## 3. Mesin Rekomendasi (Rule-based)

### 3.1 Logika Rekomendasi

| Sinyal / Kondisi | Rekomendasi Awal |
|---|---|
| Mangrove eksisting sehat | Lindungi dan pantau |
| Habitat layak + propagul & regenerasi alami tersedia | Fasilitasi regenerasi alami |
| Konektivitas pasang surut terganggu | Kaji pemulihan hidrologi |
| Habitat layak + propagul alami terbatas | Pertimbangkan penanaman terbatas |
| Abrasi/gelombang tinggi atau substrat tidak stabil | Kaji dinamika pantai / tunda tanam |
| Status legal atau parameter inti tidak diketahui | Wajib verifikasi lapangan |
| Nonhabitat atau larangan legal | Tidak direkomendasikan |

### 3.2 Yang Harus Dipahami

- Rekomendasi adalah **arahan kajian awal** — bukan perintah intervensi
- Setiap rekomendasi memerlukan verifikasi lapangan dan persetujuan ahli lokal
- Tidak ada skor keberhasilan atau probabilitas dalam mode rule-based

---

## 4. Prioritisasi Urutan Survei

### 4.1 Urutan Default

Zona diurutkan berdasarkan:
1. **Kelompok status:** `NEEDS_REVIEW` → `ELIGIBLE` → `EXCLUDED`
2. **Dalam kelompok:** Kelengkapan data terendah didahulukan (data paling kurang = perlu survei lebih dulu)

### 4.2 Interpretasi

Urutan survei bukan peringkat keberhasilan program. Zona dengan data kurang diprioritaskan karena keputusan tentangnya tidak bisa dibuat tanpa data tambahan.

---

## 5. Model Machine Learning (Rencana — Bersyarat Data)

> **Status saat ini:** `NO_MODEL_AVAILABLE` — bagian ini menjelaskan rencana, bukan implementasi yang sudah berjalan

### 5.1 Algoritma: XGBoost

XGBoost (eXtreme Gradient Boosting) dipilih karena:
- Menangani missing data secara native
- Interpretabel melalui SHAP
- Performa baik pada dataset tabular berukuran sedang
- Tersedia evaluasi kalibrasi probabilitas

Referensi: Chen & Guestrin (2016), "XGBoost: A Scalable Tree Boosting System"

### 5.2 Pemisahan Data (Spatial Cross-Validation)

Data **tidak** dibagi secara acak per baris. Pemisahan dilakukan berdasarkan **blok lokasi** untuk mencegah kebocoran spasial:

```
Train: lokasi A, B, C
Validation: lokasi D, E
Test: lokasi F, G (tidak disentuh selama tuning)
```

Kebocoran spasial terjadi jika piksel/baris yang berdekatan masuk ke train dan test sekaligus — menghasilkan metrik yang terlalu optimistis.

### 5.3 Pemeriksaan Label Leakage

Sebelum training, periksa:
- Apakah ada fitur yang merupakan turunan dari label?
- Apakah citra satelit diambil setelah tanggal pengamatan?
- Apakah label dibuat dari aturan yang sama dengan fitur input?

### 5.4 Metrik Evaluasi yang Digunakan

- **Balanced Accuracy** — untuk dataset tidak seimbang
- **F1-Score (macro)** — rata-rata antar kelas
- **ROC-AUC** dan **PR-AUC** — kinerja ranking
- **Confusion Matrix** — kesalahan per kelas
- **Kalibrasi probabilitas** — Reliability diagram / Brier Score

### 5.5 Kondisi Aktivasi Model

Model hanya diaktifkan di UI jika:
1. Artefak model (file `.json`/`.pkl`) tersedia dan dapat dimuat
2. Schema fitur cocok dengan input zona
3. Metrik validasi memenuhi ambang minimum yang disepakati tim
4. `model_registry` menunjukkan status `approved`

---

## 6. Interpretasi SHAP

### 6.1 Apa itu SHAP?

SHAP (SHapley Additive exPlanations) menghitung kontribusi setiap fitur terhadap prediksi model untuk satu sampel tertentu. Nilai SHAP positif = mendorong prediksi ke arah kelas positif; negatif = sebaliknya.

Referensi: Lundberg & Lee (2017), "A Unified Approach to Interpreting Model Predictions"

### 6.2 Implementasi (Rencana)

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_instance)
```

### 6.3 Yang SHAP Bisa Jelaskan

- Fitur mana yang paling memengaruhi prediksi model untuk zona ini
- Arah pengaruh (meningkatkan atau menurunkan skor)
- Kontribusi relatif tiap fitur

### 6.4 Yang SHAP TIDAK Bisa Jelaskan

- **Hubungan sebab-akibat** — SHAP menjelaskan model, bukan ekologi
- **Kepastian keberhasilan rehabilitasi** — bukan probabilitas bibit hidup
- **Validitas di luar domain pelatihan** — model bisa salah untuk lokasi yang berbeda dari data latih

### 6.5 Tampilan di UI

- Top 5 fitur per zona dengan nilai dan arah kontribusi
- Disclaimer: *"Nilai SHAP mencerminkan kontribusi fitur terhadap prediksi model ini. Ini bukan bukti kausalitas ekologis."*
- SHAP global (ringkasan semua sampel) tersedia di halaman Model

---

## 7. Validasi Data

### 7.1 Validasi Format

- Tipe data setiap kolom
- Rentang fisik: latitude (-90 hingga 90), longitude (-180 hingga 180), salinitas ≥ 0, NDVI ∈ (-1, 1)
- Kategori yang diperbolehkan (lihat `docs/data_dictionary.md`)
- Format tanggal: ISO 8601 (YYYY-MM-DD)

### 7.2 Validasi Geometri

Menggunakan **Shapely**:
- Polygon harus valid (tidak self-intersecting)
- Polygon tertutup (titik pertama = titik terakhir)
- Tidak mendukung geometri 3D atau antimeridian
- Luas dihitung dengan proyeksi metrik (UTM lokal atau LAEA)

### 7.3 Prinsip Null

- `null` = data tidak tersedia / belum diukur
- `0` = nilai terukur yang memang nol (misalnya salinitas 0 ppt = air tawar)
- Keduanya **tidak boleh saling menggantikan**

---

## 8. Ekspor dan Provenance

Semua file ekspor menyertakan:

| Field | Isi |
|---|---|
| `analysis_mode` | `DEMO` / `RULE_BASED` / `VALIDATED_MODEL` |
| `data_quality` | Kualitas data input |
| `model_version` | Versi model (null jika tidak tersedia) |
| `rules_version` | Versi dan checksum `rules.yaml` |
| `analysis_timestamp` | Waktu analisis dalam UTC |
| `source` | Sumber setiap observasi |
| Watermark | "SIMULASI — BUKAN DATA LAPANGAN" jika data demo |

---

## 9. Keterbatasan Metodologi

| Aspek | Keterbatasan |
|---|---|
| Aturan screening | Konsep awal; belum divalidasi ahli ekologi pesisir setempat |
| Ambang nilai | Tidak ada ambang numerik universal untuk salinitas, elevasi, atau hidroperiode |
| Cakupan data | Hanya data yang diinput pengguna; tidak ada pengambilan data otomatis |
| Model | Belum tersedia; tidak ada prediksi AI saat ini |
| Generalisasi | Hasil berlaku untuk zona yang diinput; tidak bisa digeneralisasi otomatis ke seluruh Demak |
| Verifikasi lapangan | Aplikasi tidak bisa menggantikan pengukuran in-situ |

---

## 10. Referensi Teknis

- Streamlit: https://docs.streamlit.io/
- Folium: https://python-visualization.github.io/folium/
- Shapely: https://shapely.readthedocs.io/
- PyProj: https://pyproj4.github.io/pyproj/
- XGBoost: https://xgboost.readthedocs.io/
- SHAP: https://shap.readthedocs.io/
- GeoJSON RFC 7946: https://www.rfc-editor.org/rfc/rfc7946
- SQLite: https://docs.python.org/3/library/sqlite3.html

Referensi ilmiah dataset ada di `docs/spesifikasi_sumber.md`.
