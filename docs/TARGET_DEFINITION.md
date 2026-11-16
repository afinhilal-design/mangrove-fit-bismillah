# Definisi Target AI — MANGROVE-FIT

> **Status:** Placeholder — target belum dipilih karena dataset berlabel belum diaudit  
> **Versi:** 0.1 · 16 November 2026  
> **Wajib diperbarui** setelah audit dataset D01/D02 selesai

---

## 1. Prinsip Pemilihan Target

Target AI **hanya boleh dipilih** setelah memenuhi semua kriteria berikut:

- [ ] Dataset dengan label tersedia dan telah diaudit file-by-file
- [ ] Unit analisis (plot/titik/zona) terdefinisi jelas
- [ ] Jumlah sampel memadai untuk pemisahan train/validation/test spasial
- [ ] Tidak ada label leakage antara fitur input dan label target
- [ ] Target dipilih oleh tim, bukan otomatis dari nama kolom

---

## 2. Urutan Kandidat Target (Prioritas)

### Target 1 — `seedling_survival_pct` ⭐ PRIORITAS UTAMA

**Definisi:** Persentase bibit mangrove yang hidup pada akhir periode tindak lanjut, dihitung per unit percobaan.

**Syarat ketersediaan data:**
- Jumlah bibit awal per plot/unit (`seedlings_initial`)
- Jumlah bibit hidup pada tanggal survei ulang (`seedlings_alive`)
- Periode tindak lanjut dalam hari (`followup_days`)
- Kondisi lingkungan pada periode yang sama (salinitas, hidroperiode, substrat, gelombang)

**Potensi sumber:** Dataset D02 — van Bijsterveldt dkk. (2022), 4TU DOI: 10.4121/17927198  
**Status:** ❌ BELUM DIAUDIT — tidak bisa dikonfirmasi sampai file mentah tersedia

**Rumus survival rate:** `survival_pct = (seedlings_alive / seedlings_initial) × 100`

**Peringatan:** Jangan mengisi `seedlings_initial` atau `seedlings_alive` dengan asumsi jika kolom tidak tersedia di data mentah.

---

### Target 2 — `seedling_density_m2`

**Definisi:** Kepadatan semai mangrove per meter persegi pada plot pengamatan.

**Syarat:** Unit area plot jelas; tanggal pengamatan dan koordinat tersedia per baris.

**Potensi sumber:** Dataset D01 — van Bijsterveldt dkk. (2020), 4TU DOI: 10.4121/uuid:522c81ad  
**Status:** ❌ BELUM DIAUDIT

---

### Target 3 — `mangrove_border_shift_m`

**Definisi:** Pergeseran batas mangrove dalam meter per tahun (positif = sedimentasi/ekspansi, negatif = abrasi/retraksi).

**Syarat:** Data perubahan batas dengan tanggal pengamatan jelas; bukan hanya satu titik waktu.

**Potensi sumber:** Dataset D01 (kolom `mangrove_border_shift_m`)  
**Status:** ❌ BELUM DIAUDIT

---

### Target 4 — `habitat_suitability_class` ⚠️ BERISIKO TINGGI

**Definisi:** Kelas kesesuaian habitat (misalnya: cocok / tidak cocok / belum pasti).

**Syarat KETAT:** Label HARUS berasal dari survei atau otoritas independen yang terdokumentasi metodenya — **bukan** dari aturan yang sama dengan input model (akan menyebabkan label leakage).

**Status:** ❌ Tidak tersedia saat ini. Jangan dibuat dari aturan screening yang ada.

---

## 3. Yang TIDAK Boleh Dijadikan Target

| Data yang ada | Mengapa bukan target valid |
|---|---|
| Tutupan mangrove dari GMW (citra) | Bukan label keberhasilan penanaman; bisa sama tahunnya dengan fitur |
| NDVI tinggi | Tidak berarti bibit hidup 90% |
| Salinitas rendah | Ini fitur input, bukan label output |
| Status "ELIGIBLE" dari screening | Label buatan aturan kita sendiri = leakage otomatis |

---

## 4. Unit Analisis

Unit analisis tergantung target terpilih:

| Target | Unit Analisis |
|---|---|
| `seedling_survival_pct` | Plot percobaan per ID eksperimen |
| `seedling_density_m2` | Plot pengamatan (ukuran harus tersedia) |
| `mangrove_border_shift_m` | Transek atau segmen garis pantai |
| `habitat_suitability_class` | Titik/polygon dengan label independen |

---

## 5. Penanganan Missing Data

| Penyebab | Perlakuan |
|---|---|
| Kolom tidak ada di file sumber | Tandai `null`; catat di manifest; jangan imputasi |
| Tanggal tidak tersedia | Tandai `date_missing`; jangan asumsikan tahun metadata artikel |
| Koordinat tidak tersedia per baris | Jangan gunakan satu titik untuk semua baris |
| Nilai 0 pada salinitas | Pertahankan sebagai 0 (bukan null) — memiliki makna fisik |

---

## 6. Batas Generalisasi

Setelah model dilatih, model HANYA berlaku untuk:

- Wilayah pesisir yang kondisinya serupa dengan data pelatihan
- Periode yang cocok dengan fitur satelit/lapangan yang digunakan
- Spesies mangrove yang sama dengan eksperimen sumber data

**Model TIDAK boleh** digunakan untuk:
- Memprediksi seluruh pesisir Indonesia tanpa pemeriksaan domain
- Menggantikan survei lapangan dan izin kawasan
- Memberikan jaminan keberhasilan penanaman

---

## 7. Langkah Selanjutnya

1. Unduh Dataset D02 (4TU: doi.org/10.4121/17927198) secara manual
2. Inventaris kolom yang tersedia (`scripts/02_inventory_raw.py`)
3. Verifikasi apakah `seedlings_initial`, `seedlings_alive`, `followup_days` ada
4. Pilih target dan isi bagian ini dengan keputusan yang terdokumentasi
5. Buat `data/manifests/D02.json` dengan status akses dan hash file
