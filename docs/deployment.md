# Menjalankan dan distribusi

Paket ini dibuat untuk penggunaan lokal di laptop, sesuai target spesifikasi. Distribusi menggunakan ZIP sumber; tidak ada publikasi daring atau pengiriman data survei ke hosting.

Gunakan launcher di README. Launchers mengikat server ke `localhost`. SQLite berada dalam folder proyek sehingga folder jangan ditempatkan dalam lokasi read-only. Berbagi folder/proyek tidak sama dengan memiliki aplikasi multiuser.

Untuk produksi kelak, rancang autentikasi, pengendalian akses, HTTPS, backup, migrasi DB, model registry, dan uji beban. Jangan memindahkan SQLite aktif antarlaptop atau menjalankan banyak editor pada file yang sama.
