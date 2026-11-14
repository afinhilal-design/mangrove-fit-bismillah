# Verifikasi rilis 0.1

Tanggal: 14 November 2026. Lingkungan: Linux x86_64, Python 3.12.14, Streamlit 1.50.0.

**Hasil otomatis: 51 pengujian lulus.** Perintah: `python -m pytest tests -q`. Hasil mentah: `test_results.txt`. `pip check`: tidak ada konflik dependensi. Ini bukti perangkat lunak, bukan validasi model atau validasi ekologis.

Browser QA: beranda tampil; peta OSM dan tiga polygon tampil; klik polygon B memperbarui pilihan, data, dan rekomendasi; pilihan B terbawa ke halaman analisis; tabel/grafik perbandingan tampil; halaman data dan status model tampil; renderer skematis diuji; tangkapan layar disertakan.

| Kriteria sumber | Hasil | Bukti / batas |
|---|---|---|
| AT-01 instalasi/run | Teruji Linux | Virtual environment baru, dependencies terpasang, server berjalan, seluruh halaman AppTest lulus; Windows/macOS belum diuji |
| AT-02 pilihan zona | Lulus | Klik polygon B di browser, panel berubah; screenshot peta |
| AT-03 data kurang | Lulus | Missing salinity → NEEDS_REVIEW tanpa skor AI |
| AT-04 CSV sah | Lulus | Tiga titik contoh, koordinat, sumber dan nilai benar |
| AT-05 latitude 120 | Lulus | Ditolak validator |
| AT-06 polygon berpotongan | Lulus | Ditolak INVALID_GEOMETRY |
| AT-07 salinitas kosong | Lulus | Null dipertahankan sampai DB dan ekspor; nilai 0 tetap 0 |
| AT-08 nonhabitat/legal | Lulus | EXCLUDED dan tidak ada rekomendasi tanam |
| AT-09 tanpa model | Lulus | NO_MODEL_AVAILABLE, null prediksi/SHAP |
| AT-10 fitur model salah | Sebagian / tahap ML belum berlaku | Validator MISSING_REQUIRED_FEATURES diuji; tidak ada model nyata atau pipeline inferensi yang diuji |
| AT-11 SHAP model nyata | Belum berlaku | Model belum tersedia |
| AT-12 tiga zona | Lulus | Urutan survei, tabel, alasan dan grafik |
| AT-13 ekspor metadata | Lulus | CSV dan GeoJSON roundtrip, observasi/provenance/geometri/timestamp/mode/versi/watermark |
| AT-14 luas | Lulus | Hasil UTM dan LAEA dibanding referensi geodesik independen; titik tanpa luas |
| AT-15 pindah zona/refresh | Lulus pada cakupan uji | State A↔C, map B→analisis B, penyimpanan/reopen DB, snapshot lama tak tertimpa |
| AT-16 internet mati | Sebagian | Jalur skematis lokal dan fallback diuji; pemutusan jaringan fisik/seluruh asset browser offline belum diuji |
| AT-17 ukuran/format | Lulus | Ukuran berlebih, format tidak sesuai, kategori/angka/tanggal salah ditolak |
| AT-18 watermark | Lulus | Ekspor demo membawa SIMULASI; UI demo juga berwatermark |

Tambahan: impor atomik, demo tidak bisa ditimpa ruang lokal, formula CSV/HTML injection guard, pembaruan snapshot, catatan peninjau, semua halaman Streamlit, clear dropdown tanpa crash, form tambah zona dan penyimpanan analisis+review.

Belum disimpulkan: performa di perangkat pengguna, perangkat Windows/macOS, browser seluler, uji lapangan, kualitas sumber asli, akurasi AI, keuntungan ekologis, atau keberhasilan rehabilitasi. Rilis ini MVP lokal berbasis aturan dengan batas di atas, bukan penyelesaian tahap AI.
