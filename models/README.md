# Model belum tersedia

Rilis 0.1 tidak berisi model atau prediksi terlatih. Tidak ada dataset berlabel asli yang disertakan pengguna, sehingga menyalakan XGBoost/SHAP sekarang akan menyesatkan.

Tahap selanjutnya memerlukan:

1. Tentukan target tunggal: kesesuaian/kehadiran habitat, atau hasil rehabilitasi 12 bulan; jangan dicampur.
2. Audit asal label dan sampling negatif, serta hindari kebocoran label dari fitur tutupan tahun yang sama.
3. Bagi train/validation/test berbasis blok pesisir/waktu; fit preprocessing hanya pada train.
4. Buat baseline, latih XGBoost, evaluasi balanced accuracy/F1/PR-AUC dan kalibrasi; uji lokasi independen.
5. Simpan model native JSON/UBJ, checksum, schema fitur, domain, metrik, versi data dan persetujuan ahli.
6. Implementasikan adapter inferensi yang memeriksa screening, fitur lengkap, dan domain sebelum memprediksi.
7. Gunakan SHAP TreeExplainer pada model yang sama; uji aditivitas dan ruang output raw/log-odds/probability.
8. Tambahkan pengujian model nyata sebelum mengubah status UI.

`model_service.check_model_inputs` sudah menyediakan pemeriksaan kelengkapan fitur. Ini belum merupakan implementasi inferensi. Tidak ada pickle/joblib upload, notebook yang mengarang data latih, atau hasil akurasi fiktif. Dependensi AI baru dipilih dan dikunci setelah tahap tersebut diuji.

## Kontrak artefak untuk adapter (opsional, belum aktif)

`mangrove_fit/model_service.py` kini memuat model hanya jika `models/active/model_card.json` dan `models/active/model.ubj` ada.
Kartu harus berisi: `status` (harus `APPROVED`), `version`, `target`, `features` (parameter numerik), `sha256` dari `model.ubj`,
`domain` ({fitur: [min, maks]}), `output_space` (`probability`/`raw`), `approved_by`.
Gerbang: screening bukan EXCLUDED → fitur lengkap tanpa imputasi → nilai dalam domain → baru prediksi.
Penjelasan memakai `pred_contribs` XGBoost (TreeSHAP) dengan uji aditivitas. Pasang dengan `pip install -r requirements-ml.txt`.
UI belum menampilkan skor model; itu menunggu langkah 8 di atas. Tanpa berkas tersebut, perilaku tetap NO_MODEL_AVAILABLE.

## Pipeline yang tersedia (17 Nov 2026)

```
python -m pip install -r requirements-ml.txt
python scripts/train_model.py data/latih.csv --target <kolom_0_1> --features <param...> --block-col <kolom_blok>
#  -> models/candidate/  status PENDING_REVIEW (belum aktif)
python scripts/approve_model.py --reviewer "Nama" --note "..."
#  -> models/active/     status APPROVED (model lama diarsipkan ke models/archive/)
```

- CSV: satu baris per titik sampel, label biner 0/1, kolom blok spasial, fitur = parameter numerik `schemas.PARAMETERS`.
- Baris tidak lengkap dibuang (tidak diimputasi); jumlahnya dicatat di kartu.
- Data dari `data/demo/`, berkas bernama `*SYNTHETIC*`, atau bertanda `is_demo`/`quality_flag=demo` ditolak;
  dengan `--allow-synthetic` kartunya `SYNTHETIC_TEST_ONLY` dan tidak pernah bisa disetujui atau dimuat.
- Persetujuan ditolak bila balanced accuracy uji tidak melampaui baseline prevalensi.
- `shap` (opsional) dipakai untuk mencocokkan ulang nilai TreeSHAP; bila berbeda > 1e-3 penjelasan ditahan.
