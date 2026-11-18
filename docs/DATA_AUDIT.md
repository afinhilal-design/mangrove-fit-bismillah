# Audit Data — MANGROVE-FIT

> **Status:** Audit belum dimulai — dataset belum diunduh  
> **Versi:** 0.1 · 16 November 2026  
> **Prinsip:** Audit file per file; tidak ada asumsi tentang nama kolom atau isi berdasarkan abstrak artikel

---

## Tujuan Dokumen Ini

Mencatat hasil inspeksi file mentah setiap dataset secara sistematis:
- Format dan struktur file
- Kolom yang benar-benar ada (bukan yang diasumsikan dari abstrak)
- Masalah kualitas, missing data, format tanggal, unit
- Keputusan tentang kelayakan penggunaan

---

## Status Audit Keseluruhan

| Dataset | Unduh | Inventaris file | Audit kolom | Keputusan penggunaan |
|---|---|---|---|---|
| D01 | ✅ sea-site (18 Nov 2026) | ⚠️ satu berkas | ✅ lihat bagian D01 | ⚠️ kandidat model saja |
| D02 | ❌ | ❌ | ❌ | ❌ |
| D03 | ❌ | ❌ | ❌ | ❌ |
| D04 | ❌ (perlu kontak penulis) | ❌ | ❌ | ❌ |
| G01 (GMW) | ❌ | ❌ | ❌ | ❌ |
| G02 (Sentinel-2/GEE) | ❌ | ❌ | ❌ | ❌ |
| G03 (DEMNAS) | ❌ | ❌ | ❌ | ❌ |
| G04 (JRC GSW) | ❌ | ❌ | ❌ | ❌ |
| G05 (Pasut BIG) | ❌ | ❌ | ❌ | ❌ |
| G06 (WorldCover) | ❌ | ❌ | ❌ | ❌ |
| G07 (Batas admin) | ❌ | ❌ | ❌ | ❌ |

---

## Template Audit Per Dataset

Gunakan template berikut untuk setiap dataset setelah berhasil diunduh:

```markdown
### [ID] — [Nama Dataset]

**Tanggal audit:** YYYY-MM-DD  
**Auditor:** [nama]  
**File yang diaudit:**
- `data/raw/[ID]/nama_file.csv` — [ukuran] MB — SHA256: [hash]

**Inventaris isi ZIP (jika berlaku):**
- [daftar file dalam ZIP, ukuran, format]

**Kolom yang ditemukan (CSV/XLSX):**
| Nama kolom | Tipe | Unit | Contoh nilai | Missing (%) | Catatan |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ...% | ... |

**Kolom yang DIHARAPKAN tapi TIDAK ADA:**
- [daftar kolom yang diasumsikan tapi tidak ditemukan]

**Masalah kualitas data:**
- [ ] Ada nilai di luar rentang fisik
- [ ] Format tanggal tidak konsisten
- [ ] Duplikasi ID
- [ ] Koordinat di luar wilayah Demak
- [ ] Unit tidak konsisten antar baris

**Keputusan penggunaan:**
- [ ] Bisa digunakan langsung sebagai fitur
- [ ] Bisa digunakan setelah transformasi (jelaskan)
- [ ] Hanya sebagai referensi (bukan fitur training)
- [ ] Tidak bisa digunakan (alasan: ...)

**Masalah temporal:**
- Periode data lapangan: [tahun/bulan]
- Citra satelit yang sesuai: [sumber dan tahun]
- Offset temporal: [hari/bulan]
```

---

## D02 — Rencana Audit (Prioritas)

Setelah file berhasil diunduh dari https://doi.org/10.4121/17927198:

### Kolom yang perlu dikonfirmasi keberadaannya

| Kolom | Diperlukan untuk | Risiko jika tidak ada |
|---|---|---|
| `seedlings_initial` | Hitung survival rate | Target tidak bisa dihitung |
| `seedlings_alive` | Hitung survival rate | Target tidak bisa dihitung |
| `followup_days` | Periode tindak lanjut | Perbandingan antar plot tidak valid |
| `plot_id` atau `experiment_id` | Unit analisis | Tidak bisa pisahkan train/test spasial |
| `latitude`, `longitude` | Peta dan join geospasial | Tidak bisa validasi lokasi |
| `observation_date` atau setara | Temporal alignment | Tidak bisa pakai citra satelit yang sesuai |
| `salinity_ppt` | Fitur model | Kolom penting — cek unit (ppt vs g/L) |
| `inundation_hours` atau setara | Fitur model | Mungkin menggunakan nama berbeda |

### Daftar isi ZIP yang perlu dicek terlebih dahulu
- Apakah ada README atau data dictionary dalam ZIP?
- Berapa banyak file? Format apa (CSV, XLSX, MAT, shapefile)?
- Apakah ada file terpisah per tahun atau per lokasi?

---

## D01 — Hasil audit berkas `sea-site_dataset_withNAs.csv` (18 Nov 2026)

- Format: Windows-1252, setiap baris dibungkus satu field berkutip; dibaca oleh `mangrove_fit/dataset_d01.py`.
- 56 titik, 10 transek (T01, T02, T06, T09, T10, T11, T14, T15, T20, T21), perlakuan ES (26) dan RS (30). Koordinat per titik tersedia.
- Tidak ada kolom tanggal per baris; label vegetasi/S2 merujuk 2015/2016.
- Target dipilih: `SeedlingPresence` → `seedling_presence` (12 positif). Seluruh titik positif berada di 5 transek RS.
- Fitur dipakai: `%t_submerged`×24 → lama genangan, `pH`, `redox`, `slope`. Sedimen (24–26 NA), orgC, BulkDen tidak dipakai; ShearStrngth 7 NA.
- Tidak dipakai karena risiko kebocoran label: `2016_veget`, `S2_2016011`, `mangrove_expansion`, `mangrove_die-back`.
- Belum diverifikasi: satuan `redox` (diasumsikan mV), definisi `slope`, lisensi distribusi ulang.
- Jejak: salinan asli `data/raw/D01/`, tabel latih `data/training/D01_sea_site_seedling.csv`, manifest + SHA-256 `data/manifests/D01.json`.

## D01 — Rencana Audit (awal)

Setelah file diunduh dari https://doi.org/10.4121/uuid:522c81ad:

### Kolom yang perlu dikonfirmasi
- `mangrove_border_shift_m` — kandidat target alternatif
- `seedling_density_m2` — kandidat target alternatif
- Koordinat per plot (bukan hanya satu titik untuk semua data)
- Tanggal pengamatan per baris

---

## Masalah Temporal yang Wajib Diselesaikan

| Dataset | Periode lapangan | Citra satelit yang bisa dipakai | Masalah |
|---|---|---|---|
| D01 | 2015 | Landsat 8 (tersedia 2013+), bukan Sentinel-2 | Sentinel-2 mulai 2017 — tidak bisa pakai untuk data 2015 |
| D02 | 2005–2020 | Tergantung tahun per baris | Gunakan tanggal asli per baris, bukan tahun metadata |
| D03 | 2021–2022 | Sentinel-2 tersedia | Hanya bisa di-join jika lokasi/unit kompatibel dengan D01/D02 |

---

## Kebijakan Anti-Fabrikasi

Hal-hal berikut TIDAK BOLEH dilakukan dalam audit ini:

- ❌ Mengisi nilai kolom dari ringkasan abstrak artikel jika kolom tidak ada di file
- ❌ Menggunakan satu koordinat dari metadata artikel untuk semua baris data
- ❌ Menggabungkan D01 dan D02 tanpa memverifikasi kecocokan unit analisis dan periode
- ❌ Mengekstrak citra Sentinel-2 tahun 2022 untuk data lapangan tahun 2015
- ❌ Membuat nama kolom baru lalu mengklaim sebagai "data asli"

---

## Log Audit

*Bagian ini diisi setelah audit berjalan*

| Tanggal | Dataset | Tindakan | Hasil | Auditor |
|---|---|---|---|---|
| — | — | — | — | — |
