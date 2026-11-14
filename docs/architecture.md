# Arsitektur

UI Streamlit → validasi & layanan analisis → SQLite / ekspor.

- `app.py`, `pages/`: entrypoint dan enam halaman.
- `ui_components.py`: tampilan, input pengguna, interaksi peta.
- `schemas.py`: skema, nilai null, metadata per observasi, validasi rentang fisik.
- `data_io.py`: parsing CSV/GeoJSON, validasi atomik sebelum menyimpan.
- `geospatial.py`: validasi Shapely; luas melalui UTM lokal atau LAEA bila melintasi zona UTM.
- `screening.py`, `recommendations.py`: status ekologis/legal dan arah kajian, tanpa ML.
- `preprocessing.py`: kelengkapan 7 parameter inti, tanpa imputasi.
- `services.py`: output analisis dengan snapshot dan provenance.
- `prioritization.py`: urutan kerja survei, tanpa skor program.
- `database.py`: zones, observations, datasets, models (tabel kosong), analyses, reviews.
- `model_service.py`, `explain_service.py`: status belum tersedia dan validator fitur; inferensi belum terhubung.
- `report_service.py`: CSV, GeoJSON, Markdown, HTML.

Data zona disimpan sebagai payload JSON dan observasi ternormalisasi dalam satu transaksi. Impor yang gagal tidak meninggalkan zona parsial. Scope demo dan lokal dipisah; tab demo baca-saja. Pembaruan tidak menghapus snapshot lama.

Hasil terkini hanya memakai snapshot bila input dan checksum aturan masih cocok. Setiap catatan ahli menaut pada ID analisis, bukan hasil yang berubah diam-diam. Hasil dihitung ulang untuk puluhan zona; tidak ada cache prediksi yang bisa tertukar. Streamlit mererun UI, sehingga dropdown menyimpan pilihan zona melalui state global dan callback.

Batas deployment: lokal satu pengguna, bound ke localhost melalui launcher. UI Demo/Analis lokal bukan autentikasi atau kontrol akses keamanan. Jangan mengekspose server ke internet sebagai aplikasi produksi.
