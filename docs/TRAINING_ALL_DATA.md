# Audit seluruh data dan peningkatan XGBoost + SHAP

Tanggal laporan: **19 November 2026 (WIB)**. Status eksperimen **SELESAI**, kelayakan aplikasi **PARSIAL**. Semua model baru berstatus `RESEARCH_ONLY`, tidak aktif di aplikasi.

## Cakupan sebenarnya

Seluruh **97 berkas / 178 tabel atau sheet** di `datamangroveit` telah dibaca, diprofilkan, dan dicatat checksum-nya. Ini tidak berarti 97 berkas dijadikan satu tabel training. Lima berkas mempunyai target yang dapat digunakan pada empat eksperimen terpisah; berkas lain digunakan untuk audit duplikasi, ringkasan fisik/ekologi, atau dicatat hambatan pemetaannya.

| Peran | Jumlah berkas | Pemanfaatan |
|---|---:|---|
| Input model | 5 | Sea-site + tambak, Q4, Q3 survival eksperimen, Q2 propagul |
| Salinan terverifikasi | 1 | `pond_dataset_withNAs.csv` identik secara tabel dengan versi UTF8; tidak menggandakan sampel |
| Koordinat batimetri | 71 | Audit koordinat dan cakupan sumber; tanpa kolom kedalaman atau label biologis |
| Excel pengamatan fisik | 17 | Semua sheet dibaca; ringkasan muka air harian, batimetri, dan tiang sedimen |
| Konteks ekologis Q1 | 2 | Ringkasan struktur hutan per plot dan luas per tahun/zona/tipe |
| Target belum jelas | 1 | Q3 natural establishment memiliki kode survival 0/1/2 tanpa definisi kode dan tanpa ID bibit; tidak ditebak menjadi label biner |

Sembilan workbook muka air menghasilkan 283 ringkasan per sumber-hari. Workbook batimetri dan PoleData menghasilkan 89 ringkasan sheet. Tidak dilakukan join paksa dengan data bibit: identitas lokasi, datum vertikal, dan waktu pengukuran belum terhubung secara terverifikasi. Dua CSV batimetri (`Bathymetry_april_2022_T5.csv`, `Bathymetry_july_2022_T5.csv`) masing-masing mempunyai satu baris koordinat kosong/tidak valid; nomor baris tercatat pada audit. Nilai nol akhir seri PoleData ditandai untuk konfirmasi, tidak otomatis dianggap elevasi atau kehilangan sedimen.

## Perbaikan metode

1. **Fitur diperluas tanpa mengubah skema DB.** Pipeline riset terpisah memakai whitelist fitur, validasi identitas/label, dan encoder tersimpan. Parameter aplikasi tidak ditambah atau dilewati.
2. **Nilai kosong tetap kosong.** XGBoost tree menangani NaN secara native; tidak diisi nol atau rata-rata. Kategori dipelajari hanya dari training fold; kategori belum dikenal menjadi vektor indikator nol, sedangkan kategori kosong tetap NaN. [Dokumentasi XGBoost](https://xgboost.readthedocs.io/en/release_1.7.0/faq.html).
3. **Validasi berkelompok bertingkat.** Maksimal 4 outer folds untuk evaluasi dan 3 inner folds untuk memilih konfigurasi. Kandidat tetap: kedalaman 2/3, 40/100 rounds. Pemilihan memakai average precision internal, dengan ambang klasifikasi dipilih hanya pada prediksi internal. Tidak memilih konfigurasi berdasarkan hasil outer fold. [Dokumentasi validasi berkelompok](https://scikit-learn.org/stable/modules/cross_validation.html).
4. **Koordinat berulang diperhitungkan.** Transek sea-site/tambak yang berbagi koordinat dihubungkan menjadi empat komponen kelompok. Koordinat sama dan transek sama tidak menyeberangi fold. Ini memperbaiki kelemahan eksperimen sebelumnya yang hanya memisahkan nama transek. Kedekatan lokasi yang tidak persis sama masih menjadi keterbatasan.
5. **SHAP untuk observasi yang ditahan dari pelatihan.** Exact TreeSHAP dihitung pada outer test setiap fold; kontribusi kategori digabung kembali ke fitur asal. Uji aditivitas dilakukan pada setiap fold. OOF SHAP menjelaskan beberapa model fold, bukan tepat satu model final.
6. **Model pembanding dievaluasi pada fold yang sama.** Untuk keberadaan semai dan Q4 disediakan model fitur lama, serta baseline prevalensi training untuk semua tugas.

Analisis ini tetap eksploratif karena data telah diperiksa pada eksperimen sebelumnya. Nested CV mengurangi kebocoran pemilihan parameter, tetapi bukan pengganti test eksternal baru. Pengelompokan lokasi tidak membuktikan independensi ekologis seluruh situs.

## Empat eksperimen

| Eksperimen | Sampel berlabel | Kelompok | Fitur dan target |
|---|---:|---:|---|
| Keberadaan semai | 111 | 4 komponen koordinat/transek | 17 fitur numerik yang sama di sea-site/tambak + tipe zona; label keberadaan semai alami |
| Survival Q4 | 397 | 20 blok | Spesies, ukuran bibit dan sedimen bulan 0; hidup pada bulan 16 pada bibit yang hidup bulan 0 |
| Survival Q3 | 240 | 7 blok | Kondisi situs dan perlakuan/spesies; hidup bulan 10, bersyarat hidup bulan 3 |
| Propagul Q2 | 2.387 | 25 perangkap | Spesies, zona, siklus hari dalam tahun; label `prop_count > 0` untuk pengamatan berlabel |

Q4 mempertahankan pengecualian ID ambigu J4 dan bibit P0 yang sudah mati bulan 0. Fitur ukuran berasal dari bulan 0, bukan setelah outcome. Q3 tidak digabung dengan Q4 karena horizon dan definisi kohort berbeda. Q2 mengecualikan 30 baris dengan kunci perangkap/tanggal/spesies ganda, lalu 198 baris tanpa label; angka kosong bukan dianggap tidak ada propagul. Q2 menilai generalisasi ke perangkap yang ditahan, bukan ramalan tahun mendatang.

## Hasil validasi luar

| Model | BA ambang 0,5 | BA ambang dari inner CV | AP/PR-AUC | Brier |
|---|---:|---:|---:|---:|
| Keberadaan semai | 0,4883 | 0,4716 | 0,2871 | 0,2387 |
| Survival Q4 | **0,6364** | **0,6726** | **0,5244** | **0,1968** |
| Survival Q3 | 0,5580 | 0,5580 | 0,4460 | 0,2211 |
| Propagul Q2 | 0,5829 | 0,7301 | 0,4514 | 0,1126 |

BA = balanced accuracy, baseline klasifikasi mayoritas 0,5. AP adalah average precision; Brier lebih rendah lebih baik. BA pada ambang internal memakai keputusan dengan ambang berbeda per outer fold. AP/Brier memakai probabilitas asli, bukan keputusan biner.

**Peningkatan Q4 didukung perbandingan setara:** model satu fitur sedimen pada outer folds yang sama memperoleh BA 0,4914, AP 0,3187, Brier 0,2383. Model diperluas pada ambang sama 0,5 mencapai BA 0,6364, AP 0,5244, Brier 0,1968. Peningkatan BA sebesar 14,50 poin persentase pada evaluasi ini. Dengan pemilihan ambang internal BA menjadi 0,6726, tetapi probabilitas belum dikalibrasi dan validasi lapangan baru belum ada.

**Model keberadaan semai tetap lemah.** BA model fitur lama pada fold baru 0,4759; perluasan hanya menjadi 0,4883 dan AP turun dari 0,3165 menjadi 0,2871. Penambahan data/fitur tidak selalu meningkatkan hasil. Hasil 61,4% pada test eksperimen awal tidak boleh dikutip sebagai skor validasi baru setelah diketahui masalah koordinat bersama.

Angka propagul Q2 tidak boleh digunakan sebagai akurasi survival atau keberhasilan rehabilitasi. Empat target tidak boleh dirata-ratakan menjadi satu angka akurasi aplikasi.

## Interpretasi SHAP Q4

| Fitur | Mean absolute OOF SHAP (log-odds) |
|---|---:|
| Spesies | 0,508783 |
| Ukuran bibit awal | 0,386390 |
| Sedimen awal | 0,217513 |

Ini kontribusi pada prediksi model, bukan pengaruh sebab-akibat. Besarnya kontribusi tidak menunjukkan spesies mana yang harus ditanam tanpa mempertimbangkan kesesuaian ekologis dan legal. Model final dilatih pada seluruh data setelah pemilihan internal; tidak diberi skor evaluasi baru dari data training itu sendiri.

## Skenario esai dan status aplikasi

Ketetapan 19 November 2026 dan titik A–C tetap berada di konfigurasi demo. Data skenario tersebut **tidak digunakan untuk mengganti tanggal/lokasi training**, menambah label, atau membuat data historis menjadi survei terkini. Model Q4/Q3 tidak dipaksakan memberi prediksi pada A–C tanpa input dan hubungan lokasi yang sesuai. Model aplikasi tetap `NO_MODEL_AVAILABLE`.

## Artefak dan reproduksi

Folder hasil: `models/experiments/all_data_v2/`.

- `audit/source_usage.csv`: keputusan penggunaan setiap berkas dan alasannya.
- `audit/source_audit.json`: semua tabel/sheet, jumlah baris, NA, rentang numerik, checksum dan masalah koordinat.
- Ringkasan muka air, batimetri/tiang, Q1 dan kode Q3 tersedia di folder `audit/`.
- Tiap eksperimen berisi `model.ubj`, `model_card.json`, `encoder.json`, `source_manifest.json`, `training.csv`, `oof_predictions.csv`, `oof_shap.csv`, dan `shap_importance.csv`.
- `preparation.json`, `q2_ambiguous_excluded.csv`: log pembentukan kohort dan baris ambigu.
- `summary.json`, `environment.json`, `research_comparison.png`: ringkasan hasil, versi dependensi, dan grafik.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-research.txt
.venv\Scripts\python.exe scripts/train_all_data.py --out models/experiments/all_data_run_baru
.venv\Scripts\python.exe -m pytest tests -q
```

Pengujian lengkap: **82 passed**, mencakup ketetapan waktu awal/akhir, pemisahan outer/inner kelompok, encoder hanya belajar dari training, NaN, koordinat bersama, rekonsiliasi metrik dengan scikit-learn, aditivitas SHAP, penolakan aktivasi artefak riset, dan checksum seluruh sumber. Tidak ada berkas mentah, DB, atau model lama yang ditimpa.
