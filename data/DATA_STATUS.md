# Status Dataset — MANGROVE-FIT

> **Diperbarui:** 16 November 2026  
> **Prinsip:** Jangan mengklaim data tersedia sebelum file mentah diaudit. Jangan mengarang nilai dari ringkasan artikel.

---

## Legenda Status

| Status | Arti |
|---|---|
| `NOT_DOWNLOADED` | URL/DOI diketahui; file belum diunduh |
| `MANUAL_DOWNLOAD_REQUIRED` | Memerlukan akses manual (login/permintaan ke penulis) |
| `DOWNLOADED_NOT_AUDITED` | File ada di lokal; isi belum diperiksa kolom per kolom |
| `AUDITED` | File diinventarisasi; kolom, unit, dan format diverifikasi |
| `INTEGRATED` | Data masuk ke pipeline dengan provenance lengkap |
| `BLOCKED` | Akses ditolak/berbayar; petunjuk unduh manual tersedia |

---

## Dataset Ilmiah (Prioritas Sumber Lapangan)

### D01 — van Bijsterveldt dkk. (2020)

| Field | Nilai |
|---|---|
| Judul | Tambak terbengkalai dan sisi laut pesisir Demak |
| DOI | https://doi.org/10.4121/uuid:522c81ad-e989-4374-8ac9-10367c6d4b23 |
| Provider | 4TU.ResearchData |
| **Status** | **`NOT_DOWNLOADED`** |
| Tanggal akses terakhir | — |
| File lokal | — |
| SHA256 | — |
| Lisensi | — (cek di landing page) |
| Isi yang diharapkan | 11 tambak terbengkalai + 10 sisi laut; kedalaman air, pH, redoks, sedimen, kepadatan semai, paparan gelombang, perubahan tepi mangrove |
| Periode data | 2015 |
| Peran dalam proyek | Fitur ekologis + kandidat target respons |
| Catatan temporal | Data 2015; Sentinel-2 baru tersedia 2017 → jangan pakai citra 2022 untuk fitur 2015 |
| Instruksi unduh manual | Buka https://doi.org/10.4121/uuid:522c81ad → klik tombol Download → simpan ke `data/raw/D01/` |

---

### D02 — van Bijsterveldt dkk. (2022) ⭐ PRIORITAS UTAMA

| Field | Nilai |
|---|---|
| Judul | To Plant or Not to Plant: Mangrove seedling survival Demak 2005–2020 |
| DOI | https://doi.org/10.4121/17927198 |
| Provider | 4TU.ResearchData |
| **Status** | **`NOT_DOWNLOADED`** |
| Tanggal akses terakhir | — |
| File lokal | — |
| SHA256 | — |
| Lisensi | — (cek di landing page) |
| Isi yang diharapkan | Survei propagul, pembentukan semai, kelangsungan hidup, pertumbuhan, eksperimen penanaman dan struktur perlindungan; Demak 2005–2020 |
| Periode data | 2005–2020 (cek subperiode per tabel) |
| Peran dalam proyek | **PRIORITAS TARGET AI** — kandidat `seedling_survival_pct` |
| Catatan | Perlu cek: ID eksperimen, tanggal per baris, unit sampel, kolom `seedlings_initial`, `seedlings_alive`, `followup_days` |
| Instruksi unduh manual | Buka https://doi.org/10.4121/17927198 → Download → simpan ke `data/raw/D02/` |

---

### D03 — Gijón Mancheño dkk. (2025)

| Field | Nilai |
|---|---|
| Judul | Batimetri/sedimentasi/struktur permeabel Timbulsloko 2021–2022 |
| DOI | https://doi.org/10.4121/72bb1736-28be-4c10-8f13-c7e57f8a7803 |
| Provider | 4TU.ResearchData |
| **Status** | **`NOT_DOWNLOADED`** |
| Tanggal akses terakhir | — |
| File lokal | — |
| SHA256 | — |
| Peran dalam proyek | Konteks sedimentasi — bukan label survival; tidak di-join otomatis dengan D01/D02 |
| Instruksi unduh manual | Buka DOI di atas → Download → simpan ke `data/raw/D03/` |

---

### D04 — Muhammad dkk. (2025)

| Field | Nilai |
|---|---|
| Judul | Salinitas, tekstur, durasi genangan, vegetasi Bedono |
| DOI / URL | https://doi.org/10.1186/s12862-025-02406-7 |
| Provider | BMC Ecology and Evolution (artikel, bukan repository data) |
| **Status** | **`MANUAL_DOWNLOAD_REQUIRED`** |
| Catatan | Data mentah mungkin perlu diminta langsung ke penulis; jangan fabrikasi dari ringkasan artikel |
| Peran dalam proyek | Pembanding ilmiah — bukan fitur training tanpa persetujuan penulis |

---

## Dataset Geospasial / Penginderaan Jauh

### G01 — JAXA Global Mangrove Watch v4.1

| Field | Nilai |
|---|---|
| Sumber | https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm |
| **Status** | **`NOT_DOWNLOADED`** |
| Format | GeoTIFF multiband, 30 m, 41 band (1985–2025) |
| Peran | Perubahan tutupan mangrove — **bukan target survival** |
| Lisensi | Cek ketentuan JAXA sebelum redistribusi |
| Catatan | Band 1 bukan otomatis = tahun 2025; periksa keterangan band per tahun |
| Instruksi | Buka halaman sumber → pilih area Demak → unduh ke `data/raw/G01/` |

---

### G02 — Sentinel-2 SR Harmonized (via Google Earth Engine)

| Field | Nilai |
|---|---|
| Sumber | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED |
| **Status** | **`NOT_DOWNLOADED`** |
| Format | Raster multiband via GEE API |
| Peran | NDVI, NDMI, MNDWI — fitur vegetasi/air |
| Catatan temporal | Tersedia mulai 2017; jangan pakai untuk data lapangan 2015 |
| Prasyarat | Akun Google Earth Engine + project ID terdaftar |

---

### G03 — DEMNAS BIG

| Field | Nilai |
|---|---|
| Sumber | https://www.big.go.id/content/produk/demnas |
| **Status** | **`NOT_DOWNLOADED`** |
| Format | Raster elevasi |
| Peran | Fitur topografi indikatif |
| Catatan | Periksa datum vertikal; presisi vertikal mungkin tidak cukup untuk mikro-elevasi intertidal |

---

### G04 — JRC Global Surface Water v1.4

| Field | Nilai |
|---|---|
| Sumber | https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater |
| **Status** | **`NOT_DOWNLOADED`** |
| Format | Raster via GEE |
| Peran | Proxy keberadaan air historis (Landsat 1984–2021) |
| Catatan | **Bukan** pengukuran hidroperiode pasang surut |

---

### G05 — Stasiun Pasang Surut BIG Semarang

| Field | Nilai |
|---|---|
| Sumber | https://srgi.big.go.id/tides/smrg |
| **Status** | **`NOT_DOWNLOADED`** |
| Peran | Konteks pasang surut regional |
| Catatan | Tidak mewakili elevasi air/genangan di setiap titik Demak |

---

### G06 — ESA WorldCover 2020/2021

| Field | Nilai |
|---|---|
| Sumber | https://esa-worldcover.org/en/data-access |
| **Status** | **`NOT_DOWNLOADED`** |
| Peran | Masker tutupan lahan |
| Catatan | Tidak menghasilkan label keberhasilan penanaman |

---

### G07 — Batas Administrasi BIG/BPS

| Field | Nilai |
|---|---|
| Sumber | BIG / BPS / instansi daerah |
| **Status** | **`NOT_DOWNLOADED`** |
| Peran | Batas AOI Kabupaten Demak, saringan legal |
| Catatan | Atribusi dan tanggal versi wajib dicatat; jangan buat polygon administrasi sendiri |

---

## Urutan Akuisisi yang Disarankan

```
D02 → D01 → D03 → G01 → G02 → G03 → G04 → G05/G06/G07
```

Mulai dari sumber lapangan (D02) sebelum mengunduh data geospasial.

---

## Langkah Setelah Unduh

Untuk setiap dataset yang berhasil diunduh:

1. Simpan file ke `data/raw/<ID>/` tanpa modifikasi
2. Hitung SHA256: `python -c "import hashlib; print(hashlib.sha256(open('file','rb').read()).hexdigest())"`
3. Inventarisasi isi: nama file, format, ukuran, kolom (untuk CSV/XLSX)
4. Perbarui `data/manifests/<ID>.json` (lihat template di `docs/spesifikasi_sumber.md` §3.3)
5. Perbarui status tabel di atas dari `NOT_DOWNLOADED` ke `DOWNLOADED_NOT_AUDITED`
6. Jalankan `python scripts/02_inventory_raw.py` untuk inventaris otomatis
