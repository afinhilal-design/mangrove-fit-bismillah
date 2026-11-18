# Kamus data

Koordinat EPSG:4326; urutan [longitude, latitude]. Metadata wajib untuk observasi berisi nilai. Kosong bukan nol.

| Field | Label | Satuan | Rentang fisik / kategori |
|---|---|---|---|
| `mangrove_cover_pct` | Tutupan mangrove | % | (0, 100); None berarti tanpa batas skema |
| `ndvi` | NDVI | indeks | (-1, 1); None berarti tanpa batas skema |
| `ndmi` | NDMI | indeks | (-1, 1); None berarti tanpa batas skema |
| `elevation_m` | Elevasi | m | (None, None); None berarti tanpa batas skema |
| `inundation_duration_h_day` | Lama genangan | jam/hari | (0, 24); None berarti tanpa batas skema |
| `tidal_connectivity` | Konektivitas pasang surut | kategori | baik, terganggu, tidak_diketahui |
| `salinity_ppt` | Salinitas | ppt | (0, None); None berarti tanpa batas skema |
| `substrate_type` | Substrat | kategori | lumpur, pasir, campuran, lainnya, tidak_diketahui |
| `wave_exposure` | Paparan gelombang | kategori | rendah, sedang, tinggi, tidak_diketahui |
| `shoreline_change_m_y` | Perubahan garis pantai | m/tahun | (None, None); None berarti tanpa batas skema |
| `natural_recruitment` | Regenerasi alami | kategori | ada, tidak, tidak_diketahui |
| `propagule_supply` | Pasokan propagul | kategori | cukup, terbatas, tidak_diketahui |
| `accessibility` | Akses lokasi | kategori | mudah, sedang, sulit, tidak_diketahui |
| `soil_ph` | pH tanah | pH | (0, 14) — ditambahkan v0.2 |
| `redox_mv` | Potensial redoks | mV | (-1000, 1000) — ditambahkan v0.2 |
| `bed_slope` | Kemiringan dasar | rasio | (-1, 1) — ditambahkan v0.2 |

**Migrasi v0.2 (18 Nov 2026):** zona lama di SQLite tidak diubah. Saat dibaca (`database.list_zones`), `schemas.upgrade_observations` menambahkan tiga parameter baru sebagai `missing` (nilai kosong, tanpa imputasi). Tidak ada perubahan tabel.

Tujuh parameter inti: salinitas, lama genangan, konektivitas, substrat, gelombang, regenerasi, pasokan propagul. Legal/tutupan diperiksa terpisah.

Metadata per parameter: `value`, `unit`, `date`, `source`, `quality_flag`, `method`, `datum`. Metode belum terisi diberi peringatan. Datum wajib untuk interpretasi elevasi terhadap pasang surut.

`provenance` menyimpan metadata dataset opsional: provider, dataset_name, dataset_version, observation_date, download_date, spatial_resolution_m, license, source_url, processing_method, quality_flag; dan referensi legal.

Status legal: terverifikasi, perlu_verifikasi, dilarang, tidak_diketahui. Jenis tutupan: coastal_mudflat, degraded_coastal, mangrove, sandy_beach, coral_reef, seagrass, open_water, built_area, tidak_diketahui.

Sumber data citra tidak menggantikan pengukuran salinitas/hidroperiode. Skema rentang hanya memeriksa nilai fisik, bukan menentukan kecocokan spesies.