# Model Card — MANGROVE-FIT

> **Status model:** `NO_MODEL_AVAILABLE`  
> **Versi:** Placeholder 0.1 · 16 November 2026  
> **Dokumen ini akan diperbarui** setelah model XGBoost dilatih dan divalidasi

---

> [!IMPORTANT]
> Tidak ada model yang dilatih atau diaktifkan pada versi MVP 0.1 ini. Semua kolom di bawah berstatus **BELUM TERSEDIA** dan hanya akan diisi setelah proses training, validasi, dan persetujuan selesai.

---

## 1. Informasi Model

| Field | Nilai |
|---|---|
| Nama model | — |
| Versi | — |
| Tanggal training | — |
| Algoritma | XGBoost (XGBClassifier / XGBRegressor) |
| Target label | — (lihat `docs/TARGET_DEFINITION.md`) |
| Status persetujuan | `AWAITING_DATA` |
| Path artefak | — |

---

## 2. Tujuan dan Penggunaan

**Tujuan yang dimaksud:**  
Membantu penilaian kesesuaian habitat mangrove di pesisir Kabupaten Demak berdasarkan data hidrologi, geospasial, dan ekologi lapangan. Output model adalah probabilitas kesesuaian habitat, **bukan** jaminan keberhasilan penanaman.

**Pengguna yang dimaksud:**  
Peneliti, analis pesisir, dan pengelola rehabilitasi yang sudah memahami keterbatasan model.

**Penggunaan yang TIDAK dianjurkan:**
- Menetapkan lokasi penanaman tanpa survei lapangan
- Menggantikan izin kawasan atau keputusan tata ruang
- Generalisasi ke wilayah di luar domain pelatihan
- Mengklaim probabilitas sebagai "persen keberhasilan bibit"

---

## 3. Dataset Pelatihan

| Field | Nilai |
|---|---|
| Sumber utama | — (target: D02, van Bijsterveldt dkk. 2022) |
| DOI sumber | https://doi.org/10.4121/17927198 |
| Status akses | `NOT_DOWNLOADED` |
| Periode data | — |
| Jumlah sampel (train) | — |
| Jumlah sampel (validasi) | — |
| Jumlah sampel (test) | — |
| Metode pembagian | Spasial (blok lokasi) — bukan acak per piksel |
| Hash dataset | — |

---

## 4. Fitur Input Model

| Field | Keterangan | Status |
|---|---|---|
| `inundation_duration_h_day` | Lama genangan (jam/hari) | Belum konfirmasi |
| `tidal_connectivity` | Konektivitas pasang surut | Belum konfirmasi |
| `salinity_ppt` | Salinitas (ppt) | Belum konfirmasi |
| `substrate_type` | Jenis substrat | Belum konfirmasi |
| `wave_exposure` | Paparan gelombang | Belum konfirmasi |
| `natural_recruitment` | Regenerasi alami | Belum konfirmasi |
| `propagule_supply` | Pasokan propagul | Belum konfirmasi |
| `ndvi` | Indeks vegetasi Sentinel-2 | Belum konfirmasi |
| `ndmi` | Indeks kandungan air vegetasi | Belum konfirmasi |
| `elevation_m` | Elevasi (dengan datum) | Belum konfirmasi |

> Daftar fitur final ditentukan setelah audit dataset dan pemeriksaan temporal alignment.

---

## 5. Metrik Evaluasi

| Metrik | Nilai | Catatan |
|---|---|---|
| Balanced Accuracy | — | — |
| F1-Score (macro) | — | — |
| ROC-AUC | — | — |
| PR-AUC | — | — |
| Confusion Matrix | — | — |
| Kalibrasi probabilitas | — | — |

---

## 6. Hyperparameter

Pengaturan awal (hipotesis — belum dioptimasi):

```python
XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    eval_metric='logloss',
    random_state=42
)
```

> Hyperparameter ini BELUM divalidasi. Akan direvisi setelah eksperimen.

---

## 7. Keterbatasan dan Risiko

| Risiko | Tingkat | Mitigasi |
|---|---|---|
| Label leakage (fitur = turunan label) | Tinggi | Periksa setiap fitur terhadap definisi target |
| Overfitting pada lokasi pelatihan | Tinggi | Gunakan pembagian spasial, laporkan metrik per lokasi |
| Temporal mismatch (Sentinel-2 vs data lapangan) | Tinggi | Verifikasi tahun citra sesuai tanggal pengamatan |
| Out-of-domain prediction | Sedang | Tampilkan peringatan untuk input di luar distribusi latih |
| Interpretasi kausal SHAP | Sedang | Perjelas dalam UI: SHAP = kontribusi prediksi, bukan sebab |
| Generalisasi ke luar Demak | Tinggi | Jangan diklaim tanpa validasi tambahan |

---

## 8. Interpretasi SHAP

Setelah model tersedia:

- Gunakan `shap.TreeExplainer` pada model XGBoost yang telah dilatih
- Tampilkan **top 5 fitur** per zona dengan arah dan besaran kontribusi
- Pisahkan SHAP global (ringkasan semua sampel) dan SHAP lokal (zona terpilih)
- Sertakan disclaimer: *"Kontribusi fitur terhadap prediksi model — bukan bukti kausalitas ekologis"*

---

## 9. Versi Perangkat Lunak

| Paket | Versi (rencana) |
|---|---|
| Python | 3.11.x |
| xgboost | 3.2.0 |
| scikit-learn | — |
| shap | — |
| pandas | 2.3.3 |
| numpy | 2.3.5 |

---

## 10. Riwayat Model

| Versi | Tanggal | Perubahan | Status |
|---|---|---|---|
| 0.0 (placeholder) | 2026-11-16 | Belum ada model | `NO_MODEL_AVAILABLE` |

---

## 11. Kontak dan Persetujuan

Model hanya dapat diaktifkan di UI setelah:
- [ ] Dataset berlabel diaudit dan terdokumentasi
- [ ] Pipeline training dijalankan dan metrik dievaluasi
- [ ] Pembagian train/validation/test spasial diverifikasi
- [ ] Tidak ada label leakage yang terdeteksi
- [ ] Persetujuan peninjau dicatat di sini

**Peninjau:** —  
**Tanggal persetujuan:** —
