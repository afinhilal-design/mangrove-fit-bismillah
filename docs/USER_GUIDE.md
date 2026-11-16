# Panduan Pengguna — MANGROVE-FIT

> Versi MVP 0.1 · Bahasa: Indonesia  
> Aplikasi berjalan lokal di laptop; tidak perlu koneksi internet untuk data (hanya basemap)

---

## Daftar Isi

1. [Memulai Aplikasi](#1-memulai-aplikasi)
2. [Memahami Mode Kerja](#2-memahami-mode-kerja)
3. [Halaman Beranda](#3-halaman-beranda)
4. [Halaman Peta Kawasan](#4-halaman-peta-kawasan)
5. [Halaman Analisis Lokasi](#5-halaman-analisis-lokasi)
6. [Halaman Perbandingan Zona](#6-halaman-perbandingan-zona)
7. [Halaman Data & Model](#7-halaman-data--model)
8. [Halaman Metodologi](#8-halaman-metodologi)
9. [Mengimpor Data](#9-mengimpor-data)
10. [Mengekspor Hasil](#10-mengekspor-hasil)
11. [Memahami Hasil Screening](#11-memahami-hasil-screening)
12. [Pertanyaan Umum (FAQ)](#12-pertanyaan-umum-faq)

---

## 1. Memulai Aplikasi

### Windows (klik dua kali)
1. Jalankan `02_JALANKAN_WINDOWS.bat`
2. Browser terbuka otomatis di `http://localhost:8501`

### Manual (PowerShell)
```powershell
cd e:\ITRUSH\mangrove-fit-bismillah
.venv\Scripts\Activate.ps1
streamlit run app.py
```

Jika browser tidak terbuka otomatis, buka `http://localhost:8501` secara manual.

---

## 2. Memahami Mode Kerja

Aplikasi memiliki dua mode yang bisa dipilih di **sidebar kiri**:

| Mode | Kapan dipakai | Data yang bisa diubah |
|---|---|---|
| **Demo** | Melihat contoh alur tanpa data asli | Tidak — hanya baca |
| **Analis lokal** | Import dan analisis data kamu sendiri | Ya — data disimpan di SQLite lokal |

> ⚠️ Mode Demo menampilkan watermark **"SIMULASI — BUKAN DATA LAPANGAN"** pada semua hasil. Jangan mengklaim data demo sebagai hasil ilmiah.

---

## 3. Halaman Beranda

Menampilkan:
- **Ringkasan zona** — total zona, jumlah per status screening
- **Tombol navigasi cepat** — Jelajahi peta, Mulai analisis, Impor dataset
- **Status sistem** — apakah mode Demo, Rule-based, atau Model aktif
- **Tiga pertanyaan** sebelum menanam (alur penggunaan)

---

## 4. Halaman Peta Kawasan

### Fitur utama

- **Peta interaktif** (Folium + OpenStreetMap) — klik polygon untuk memilih zona
- **Pencarian zona** — ketik nama atau ID di kotak pencarian
- **Filter status** — tampilkan hanya zona Eligible, Perlu verifikasi, atau Tidak memenuhi
- **Peta skematis offline** — aktifkan toggle jika basemap gagal dimuat (tidak perlu internet)
- **Panel kanan** — tampilkan luas, kelengkapan data, dan rekomendasi awal zona terpilih

### Cara menggunakan peta

1. Klik pada polygon/marker di peta → zona terpilih muncul di panel kanan
2. Atau gunakan dropdown **"Pilih zona"** di panel kanan
3. Klik **"Analisis zona ini"** untuk lanjut ke analisis detail

### Legenda warna

| Warna | Status | Arti |
|---|---|---|
| 🟢 Hijau | Bisa dikaji lanjut | Tersedia dasar untuk evaluasi lanjutan |
| 🟡 Kuning | Perlu verifikasi | Data penting belum lengkap atau legal belum jelas |
| 🔴 Merah | Tidak memenuhi screening | Ada pembatas jelas (nonhabitat/larangan) |

> Hijau **bukan berarti** siap ditanam atau pasti berhasil. Ini hanya status awal.

---

## 5. Halaman Analisis Lokasi

Halaman utama untuk melihat detail satu zona. Terdiri dari 5 tab:

### Tab 1 — Data Input
- Tabel parameter lengkap: nilai, satuan, sumber, tanggal, kualitas, metode, datum
- **Kosong ≠ 0** — nilai kosong menunjukkan data belum tersedia
- Lihat **Provenance dataset & geometri** (klik expand) untuk melihat metadata lengkap

### Tab 2 — Screening
- Status: **Bisa dikaji lanjut / Perlu verifikasi / Tidak memenuhi**
- Daftar alasan screening yang transparan dan dapat diperiksa
- Versi aturan yang digunakan (checksum rules.yaml)

### Tab 3 — Model XGBoost
- Saat ini: **NO_MODEL_AVAILABLE**
- Akan aktif setelah dataset berlabel terverifikasi tersedia dan model dilatih

### Tab 4 — Penjelasan SHAP
- Saat ini: belum tersedia (menunggu model XGBoost)
- SHAP menjelaskan kontribusi fitur terhadap prediksi — **bukan** bukti kausalitas

### Tab 5 — Rekomendasi & Verifikasi
- Rekomendasi awal berbasis aturan (bukan prediksi AI)
- **Mode Analis lokal:** tombol Simpan analisis + form catatan verifikator
- Riwayat catatan ahli tersimpan di database lokal

---

## 6. Halaman Perbandingan Zona

Bandingkan 2–5 zona sekaligus:

1. Pilih zona di multiselect (maksimal 5)
2. Filter berdasarkan status screening (opsional)
3. Pilih pengurutan: urutan survei, kelengkapan data terendah, atau nama
4. Lihat tabel perbandingan dan grafik parameter
5. Ekspor hasil perbandingan

**Urutan survei:** Perlu verifikasi → Bisa dikaji lanjut → Tidak memenuhi. Dalam satu kelompok, data paling tidak lengkap diprioritaskan lebih dahulu.

> ℹ️ Urutan survei **bukan** peringkat program atau prediksi keberhasilan tanam.

---

## 7. Halaman Data & Model

### Tab 1 — Impor & Template
- Unduh template CSV kosong untuk titik sampel
- Unduh contoh data sintetis (CSV dan GeoJSON)
- Upload file CSV atau GeoJSON kamu untuk diimpor

### Tab 2 — Tambah / Edit Zona
- Tambah zona baru dengan form manual
- Edit parameter observasi per baris (nilai, sumber, tanggal, kualitas)
- Tersedia hanya di mode **Analis lokal**

### Tab 3 — Dataset Tersimpan
- Daftar semua zona yang ada di database
- Tombol **Cadangkan seluruh zona** ke GeoJSON
- Daftar dataset yang pernah diimpor

### Tab 4 — Status Model
- Status saat ini: `NO_MODEL_AVAILABLE`
- Syarat integrasi model ditampilkan di sini

---

## 8. Halaman Metodologi

Berisi penjelasan transparan tentang:
- Alur analisis: Screening → Kajian tindakan → Model bersyarat
- Perbedaan: Kesesuaian habitat vs Urgensi intervensi vs Kesiapan tindakan
- Aturan screening dalam format YAML yang dapat dibaca dan diperiksa
- Parameter, satuan, dan sumber data
- Keterbatasan ilmiah yang perlu diketahui

---

## 9. Mengimpor Data

### Format CSV

Kolom wajib: `zone_id`, `zone_name`, `longitude`, `latitude`  
Kolom opsional: semua parameter ekologis

```csv
zone_id,zone_name,longitude,latitude,landcover_type,legal_status,...
ZONA-001,Pantai Utara,110.500,-6.900,coastal_mudflat,perlu_verifikasi,...
```

**Aturan penting:**
- Koordinat: `longitude` (BT) dan `latitude` (LS, nilai negatif untuk selatan khatulistiwa)
- Kolom kosong = `null` (data tidak tersedia) — **jangan isi 0 jika tidak diukur**
- ID zona harus unik dalam satu dataset

**Kategori yang diperbolehkan:**

| Field | Pilihan |
|---|---|
| `landcover_type` | `coastal_mudflat`, `degraded_coastal`, `mangrove`, `sandy_beach`, `coral_reef`, `seagrass`, `open_water`, `built_area`, `tidak_diketahui` |
| `legal_status` | `terverifikasi`, `perlu_verifikasi`, `dilarang`, `tidak_diketahui` |
| `quality_flag` | `measured`, `modelled`, `estimated`, `demo`, `missing` |
| `tidal_connectivity` | `baik`, `terganggu`, `tidak_diketahui` |
| `substrate_type` | `lumpur`, `pasir`, `campuran`, `lainnya`, `tidak_diketahui` |
| `wave_exposure` | `rendah`, `sedang`, `tinggi`, `tidak_diketahui` |
| `natural_recruitment` | `ada`, `tidak`, `tidak_diketahui` |
| `propagule_supply` | `cukup`, `terbatas`, `tidak_diketahui` |

### Format GeoJSON

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "zone_id": "ZONA-001",
      "zone_name": "Pantai Utara"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[110.49,-6.90],[110.50,-6.90],[110.50,-6.91],[110.49,-6.91],[110.49,-6.90]]]
    }
  }]
}
```

**Batas teknis:**
- Ukuran file: maksimal 10 MB
- Jumlah zona: maksimal 1.000 per file
- Vertex per polygon: maksimal 50.000
- Geometri 3D dan antimeridian tidak didukung

---

## 10. Mengekspor Hasil

Tersedia di halaman **Analisis lokasi** dan **Perbandingan zona**:

| Format | Isi | Kegunaan |
|---|---|---|
| CSV | Tabel data + metadata | Analisis lanjutan di Excel/Python |
| GeoJSON | Geometri + hasil screening | Visualisasi di QGIS/ArcGIS |
| HTML | Laporan ringkas siap cetak | Presentasi/dokumentasi |
| Markdown | Teks terformat | Laporan teknis/esai |

Semua file ekspor menyertakan: `analysis_mode`, `data_quality`, `model_version`, `analysis_timestamp`, sumber setiap observasi, dan watermark jika data demo.

---

## 11. Memahami Hasil Screening

### Status ELIGIBLE (Bisa dikaji lanjut)
Zona memenuhi kriteria awal:
- Jenis tutupan mendukung habitat mangrove
- Status legal tidak dilarang
- Setidaknya sebagian parameter inti tersedia

**Langkah selanjutnya:** Verifikasi lapangan, cek kelengkapan data, pertimbangkan parameter yang masih kosong.

### Status NEEDS_REVIEW (Perlu verifikasi)
Ada satu atau lebih kondisi:
- Status legal belum terverifikasi
- Parameter inti penting masih kosong
- Sinyal degradasi terdeteksi

**Langkah selanjutnya:** Prioritaskan survei untuk parameter yang belum tersedia.

### Status EXCLUDED (Tidak memenuhi screening)
Ada pembatas jelas:
- Jenis tutupan bukan habitat mangrove (terumbu, lamun, perairan terbuka, kawasan terbangun)
- Status legal dilarang

**Langkah selanjutnya:** Tidak direkomendasikan untuk penanaman mangrove. Verifikasi status kawasan.

---

## 12. Pertanyaan Umum (FAQ)

**Q: Mengapa skor AI tidak muncul?**  
A: Model XGBoost belum tersedia. Aplikasi menggunakan aturan transparan (`config/rules.yaml`) hingga dataset berlabel terverifikasi tersedia dan model dilatih.

**Q: Apakah data saya aman?**  
A: Data tersimpan hanya di laptop kamu dalam file `data/app.db` (SQLite). Tidak ada upload ke server eksternal.

**Q: Peta tidak muncul, bagaimana?**  
A: Aktifkan toggle **"Peta skematis offline"** di halaman Peta. Data dan analisis tetap berfungsi penuh tanpa basemap.

**Q: Bisa tidak, zona demo diedit?**  
A: Zona demo bersifat baca-saja dan tidak bisa dihapus dari mode Demo. Di mode Analis lokal, kamu bisa menambah zona baru sendiri.

**Q: Apa bedanya "null" dan "0" untuk salinitas?**  
A: `null` = belum diukur/tidak tersedia. `0` = diukur dan hasilnya nol ppt (air tawar). Keduanya memiliki makna berbeda dan tidak boleh saling menggantikan.

**Q: Apakah hasil screening berarti zona siap ditanam?**  
A: Tidak. Hasil screening adalah arahan kajian awal. Setiap tindakan tetap memerlukan: verifikasi lapangan, izin kawasan, konsultasi ahli lokal, dan kajian sosial-ekologis.

**Q: Bagaimana cara backup data saya?**  
A: Tutup aplikasi, lalu salin file `data/app.db` ke lokasi lain. Atau gunakan tombol "Cadangkan seluruh zona sebagai GeoJSON" di halaman Data & model.
