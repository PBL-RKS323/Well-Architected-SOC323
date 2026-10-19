# Changelog

Setiap perubahan dicatat di sini: apa yang berubah, alasannya, dan cara mengujinya.
Format tanggal: YYYY-MM-DD (WIB).

## [0.5.3] - 2026-10-19 - Katalog Contoh & Navigasi

### Ditambahkan
- `flask seed-katalog`: 8 produk contoh (Apple, Samsung, Xiaomi) dari `seed/katalog.json`, foto HD dari
  Wikimedia Commons (dipotong & diperkecil ke 1200px, lewat validasi upload yang sama). Produk yang
  namanya sudah ada dilewati.
- Halaman **Kredit Foto** (`/kredit-foto`, link di footer) berisi sumber, pembuat, dan lisensi tiap foto.
- Tombol "Kembali ke toko" di halaman Masuk/Daftar, tombol kembali di Pesanan Saya.

### Diubah
- Menu bawah untuk tamu: Beranda, Jelajah, Keranjang, Masuk (Pesanan & Profil hanya setelah login).
- Footer tampil juga di HP.

### Cara uji
- `pytest -q` -> 99 passed.

## [0.5.2] - 2026-10-19 - Deploy ke OCI

### Ditambahkan
- Aplikasi online di **https://toko.neteye.my.id** (VM Oracle Cloud, Ubuntu 24.04): Gunicorn di
  belakang Nginx, PostgreSQL 16 lokal, sertifikat Let's Encrypt. Panduan di `docs/DEPLOY.md`.
- `deploy/elektronik-store.service` (systemd) dan `deploy/nginx-elektronik-store.conf`.
- `DEMO_MODE`: pemberitahuan "toko demo" di semua halaman (rekening & produk masih contoh).
- Header HSTS dikirim saat `SESSION_COOKIE_SECURE=1` (HTTPS).
- `gunicorn` di `requirements.txt`.

### Keamanan
- Rahasia produksi (SECRET_KEY, password database) dibuat acak di server, hanya di `.env` (chmod 600).
- Database hanya mendengar di localhost, role aplikasi bukan superuser.
- Password admin pertama acak, disimpan di file chmod 600 di server (tidak dikirim lewat chat).

### Cara uji
- `pytest -q` -> 96 passed.
- `curl -I https://toko.neteye.my.id` -> 200 dengan header CSP, HSTS, X-Frame-Options.

## [0.5.1] - 2026-10-19 - Audit Anti-Slop

Tampilan diperiksa dengan aturan [antislop](https://github.com/miqdadbadjuber/anti-slop) agar tidak
terlihat seperti template AI. Keputusan desain dicatat di `docs/DESIGN.md`.

### Diubah
- **Kontras warna (WCAG AA)**: biru `#2F80ED` menjadi `#1A68D1`, abu `#6B7280` menjadi `#636B78`,
  merah `#F04438` menjadi `#C8291D`. Teks abu muda (`slate-400`) diganti abu yang lolos 4,5:1.
- **Area sentuh minimal 44px** di HP: tombol + kartu produk, stepper jumlah, ikon header, hapus item,
  salin, tab, paginasi, filter.
- **Klaim tanpa data dihapus**: "PROMO MINGGU INI" menjadi "Diskon N%", "Dikirim ke seluruh Indonesia"
  dan "estimasi 2-4 hari kerja" diganti info ongkir flat yang sebenarnya, "biasanya selesai dalam
  beberapa jam" dihapus.
- **Dekorasi dikurangi**: ikon sparkle & api, gradien banner, bayangan di semua kartu & tombol, animasi
  zoom foto, panah di tombol (kecuali Checkout), label "AKSI/PERINGATAN" & "EKOSISTEM" di dasbor/beranda.
- Dasbor admin: kartu Total Pendapatan jadi satu-satunya titik fokus (biru penuh).
- Pilihan pengiriman & pembayaran di checkout menampilkan cincin fokus saat dipilih lewat keyboard.

### Cara uji
- `pytest -q` -> 95 passed.

## [0.5.0] - 2026-10-19 - Sprint 5: Checkout & Pesanan

### Ditambahkan
- **Checkout** (`/checkout`) sesuai desain: pilih **Dikirim kurir** (ongkir flat Rp 15.000) atau
  **Ambil di toko** (gratis), alamat/data pengambil, catatan, ringkasan, tombol bayar menempel di bawah layar HP.
  Alamat otomatis diisi dari pesanan terakhir.
- **Pembayaran transfer bank manual**: halaman konfirmasi (nomor pesanan + tombol salin, rekening tujuan,
  batas bayar 24 jam) lalu pelanggan **mengunggah bukti transfer**. Opsi QRIS/E-Wallet (Midtrans) tampil
  sebagai "Segera".
- **Pesanan Saya** (`/pesanan`): kartu pesanan dengan status, foto produk, total, tab Semua/Aktif/Selesai/
  Dibatalkan, pencarian nomor pesanan atau nama produk, tombol Bayar / Lacak / Beli Lagi.
- **Detail & lacak pesanan**: timeline langkah (dibuat, bukti dikirim, pembayaran diterima, dikirim / siap
  diambil, selesai), nomor resi, alamat, rincian biaya, batalkan pesanan, konfirmasi pesanan diterima.
- **Admin - Pesanan** (`/admin/pesanan`): tab per status dengan jumlah, pencarian kode/nama/email, detail
  pesanan dengan bukti bayar, tombol Terima / Tolak (wajib alasan) / Tandai Dikirim (+resi) / Siap Diambil /
  Selesai / Batalkan, riwayat status. Badge jumlah pesanan yang menunggu verifikasi di menu.
- **Dasbor admin** mengikuti desain: total pendapatan (hanya pesanan lunas), total pesanan, status operasional
  (perlu verifikasi, perlu dikirim, stok menipis), produk terlaris, tabel pesanan terbaru.
- Navigasi bawah HP sekarang 5 menu (Beranda, Jelajah, Keranjang, Pesanan, Profil), menu Pesanan Saya di profil.
- Tabel baru `pesanan`, `pesanan_item` (salinan nama & harga saat checkout), `pesanan_riwayat`.

### Keamanan
- Harga, ongkir, dan total dihitung di server dari database; nilai harga dari form diabaikan.
- Stok dipotong dengan `UPDATE ... WHERE stok >= jumlah` sehingga tidak bisa minus saat checkout bersamaan.
- Pesanan & bukti bayar hanya bisa dibuka pemiliknya (admin boleh melihat bukti). Percobaan membuka milik
  orang lain dijawab 404 dan dicatat `ACCESS_DENIED`.
- Bukti bayar disimpan di folder privat `instance/bukti_bayar/` (bukan `static/`), divalidasi isi biner,
  dikirim dengan `Cache-Control: private, no-store`.
- Status hanya bisa pindah sesuai tabel transisi; UPDATE bersyarat mencegah race condition (mis. stok
  dikembalikan dua kali). Aksi tidak sah dicatat `ORDER_INVALID_TRANSITION`.
- Maksimal 3 pesanan belum dibayar per akun; pesanan yang tidak dibayar 24 jam batal otomatis dan stoknya
  kembali.
- Event log baru: `ORDER_CREATE`, `PAYMENT_PROOF_UPLOADED`, `PAYMENT_VERIFIED`, `PAYMENT_REJECTED`,
  `ORDER_STATUS_CHANGE`, `ORDER_CANCELLED`, `ORDER_INVALID_TRANSITION`.

### Diubah
- Menghapus produk tidak menghapus riwayat pesanan (item pesanan menyimpan nama & harga).
- `TEST_DATABASE_URL` opsional untuk menjalankan tes di PostgreSQL; tabel dibersihkan setelah tiap tes.

### Cara uji
- `flask db upgrade` (membuat tabel pesanan).
- `pytest -q` -> 95 passed (SQLite), juga lulus di PostgreSQL 16.
- Manual: tambah produk ke keranjang -> Checkout -> unggah bukti di detail pesanan -> login admin ->
  Pesanan -> Terima -> Tandai Dikirim -> login pelanggan -> Pesanan Sudah Diterima.

## [0.4.0] - 2026-10-19 - Sprint 4: Keranjang Belanja

### Ditambahkan
- Tabel `keranjang_item` (satu baris per user + produk, disimpan di database, tidak hilang saat
  logout).
- Tambah ke keranjang dari kartu produk (tombol +) dan dari halaman detail (pilih jumlah,
  tombol Keranjang / Beli Sekarang).
- Halaman **Keranjang** (`/keranjang`) sesuai desain: versi kosong dengan rekomendasi produk,
  versi berisi dengan stepper jumlah, hapus item, kosongkan keranjang, ringkasan subtotal dan
  hemat dari diskon.
- Badge jumlah item di ikon keranjang (header) dan menu Keranjang di navigasi bawah.
- Peringatan di keranjang jika stok habis atau stok kurang dari jumlah yang dipilih.

### Aturan
- Jumlah per produk maksimal 5 dan tidak boleh melebihi stok.
- Produk dengan stok 0 tidak bisa ditambahkan.
- Menghapus produk (admin) ikut menghapus produk itu dari semua keranjang.
- Tombol Checkout masih nonaktif (dikerjakan di sprint berikutnya).

### Keamanan
- Semua aksi keranjang wajib login, lewat POST + token CSRF.
- Item keranjang hanya bisa diubah pemiliknya (cek `user_id`, mencegah IDOR).
- Input jumlah divalidasi di server (bukan angka, negatif, atau terlalu besar ditolak/dibatasi).
- Redirect setelah tambah ke keranjang hanya ke path internal.

### Diperbaiki
- Tombol + di kartu produk sempat tetap tampil sebagai link login walau sudah login (macro
  Jinja yang di-import tidak membawa variabel template). Sekarang memakai `g.user`.

### Cara uji
- `flask db upgrade` (membuat tabel `keranjang_item`).
- `pytest -q` → 70 passed.

## [0.3.0] - 2026-10-19 - Sprint 3: Tampilan Sesuai Desain Figma

### Ditambahkan
- **Sistem desain** dari moodboard Figma: font Inter + Plus Jakarta Sans, palet warna (Bright Blue
  `#2F80ED`, Soft Gray, Peach, Slate, Coral Red, Warm Yellow), tombol pill, sudut 8-16px,
  bayangan lembut, ikon garis tipis Lucide (disimpan sebagai macro, tanpa skrip eksternal).
- **Layout mobile-first** untuk toko: header ringkas + navigasi bawah (Beranda, Jelajah, Profil)
  di HP, menu atas di desktop. **Layout admin desktop** dengan sidebar.
- **Beranda**: kolom pencarian, produk unggulan (diskon terbesar), belanja per kategori,
  produk per ekosistem brand.
- **Jelajah** (`/jelajah`): pencarian nama/merek/kategori/deskripsi, filter kategori, merek,
  rentang harga, urutan (terbaru, termurah, termahal, nama), paginasi 12 produk.
- **Detail produk** (`/produk/<id>`): foto, badge diskon/stok, harga coret, ringkasan, info
  pengiriman, produk lain dari merek yang sama.
- **Profil** (`/profil`) dan form ubah nama di Pengaturan.
- Harga normal (opsional) untuk menampilkan diskon dan harga coret.
- Register memakai **nama lengkap** + persetujuan syarat; username internal dibuat otomatis
  dari email. Login punya opsi **Ingat saya**.
- Dashboard admin: sapaan sesuai jam (WIB), kartu statistik, produk terbaru, peringatan stok
  (≤ 5 unit). Daftar produk admin bisa dicari.

### Diubah
- Endpoint `katalog` diganti `beranda`; `katalog_controller` menjadi `toko_controller`.
- Sesi: tanpa "Ingat saya" berakhir saat browser ditutup, dengan "Ingat saya" bertahan 7 hari.
- CSP mengizinkan Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`).

### Keamanan
- Karakter `%` dan `_` dalam kata kunci pencarian di-escape agar tidak menjadi wildcard SQL.
- Parameter filter yang tidak valid (kategori/merek di luar daftar, harga bukan angka) diabaikan.

### Cara uji
- `pytest -q` → 55 passed.
- `flask db upgrade` untuk menambah kolom `users.nama_lengkap` dan `produk.harga_normal`.

## [0.2.1] - 2026-10-19 - Penyesuaian Tampilan & Katalog

### Diubah
- Katalog dikelompokkan per ekosistem brand (Apple, Samsung, Xiaomi) sesuai fokus toko:
  produk elektronik (handphone, laptop, smartwatch, dll).
- Merek produk sekarang dipilih dari daftar (Apple, Samsung, Xiaomi), bukan diketik bebas.
  Urutan kategori: Handphone, Laptop, Smartwatch, Tablet, Audio, Aksesoris.
- Navbar menampilkan ikon user + username (badge role dihapus).
- Badge "Mode Admin" di dashboard dihapus.

### Ditambahkan
- Tombol mata di semua kolom kata sandi untuk menampilkan/menyembunyikan isi (JS terpisah,
  tetap sesuai Content-Security-Policy).

### Cara uji
- `pytest -q` → 36 passed.

## [0.2.0] - 2026-10-19 - Pengaturan Akun

### Ditambahkan
- Halaman **Pengaturan** (`/pengaturan`) untuk semua user yang login: ubah email dan ubah
  kata sandi. Keduanya wajib memasukkan kata sandi saat ini sebagai konfirmasi.
- Kata sandi baru tidak boleh sama dengan yang lama, sesi diperbarui setelah ganti kata sandi.
- Event log baru: `EMAIL_CHANGED`, `PASSWORD_CHANGED`, `CREDENTIAL_CHANGE_FAILED`.
- Link "Pengaturan" di navbar.

### Diperbaiki
- Kebijakan kata sandi sebelumnya hanya menerima simbol `@$!%*?&`, sehingga kata sandi seperti
  `Admin123#` ditolak. Sekarang semua simbol diterima (tetap wajib huruf besar, huruf kecil,
  angka, simbol, minimal 8 karakter).

### Cara uji
- `pytest -q` → 33 passed.
- Manual: login, buka Pengaturan, ganti email/kata sandi, logout, login dengan data baru.

## [0.1.1] - 2026-10-19 - Database PostgreSQL

### Diubah
- PostgreSQL ditetapkan sebagai database utama (PostgreSQL 16, terpasang di WSL Ubuntu 24.04
  untuk pengembangan lokal). MySQL tetap bisa dipakai lewat `DATABASE_URL`.
- Database `db_ecommerce` dengan user khusus `ecommerce_user` (bukan superuser `postgres`),
  hak aksesnya hanya untuk database aplikasi.

### Ditambahkan
- `scripts/start-postgres-wsl.bat` untuk menyalakan PostgreSQL di WSL.

### Cara uji
- Jalankan `scripts\start-postgres-wsl.bat`, lalu `flask db upgrade` dan `flask run`.
  Halaman katalog tampil (HTTP 200) dan tabel `users`, `produk` ada di `db_ecommerce`.

## [0.1.0] - 2026-10-19 - Sprint 1: Fitur Dasar (Luaran ATS)

### Ditambahkan
- **Struktur proyek MVC**: `models/`, `forms/`, `controllers/`, `middlewares/`, `helpers/`,
  `templates/`, app factory `create_app()` di `app.py`, konfigurasi dari `.env`.
- **Database**: model `User` (role `admin`/`customer`) dan `Produk` (nama, merek, kategori,
  harga, stok, deskripsi, gambar), migrasi awal Flask-Migrate.
- **Register**: pendaftaran akun customer dengan kebijakan kata sandi kuat
  (min. 8 karakter, huruf besar, huruf kecil, angka, simbol), cek username/email unik.
- **Login & logout**: hash kata sandi Werkzeug, sesi dibersihkan saat login (anti session
  fixation), logout lewat POST + CSRF, penguncian akun 5 menit setelah 5 kali gagal.
- **Logging keamanan** ke `logs/security.log` (format ISO 8601 WIB, siap dibaca Wazuh):
  `SUCCESSFUL_LOGIN`, `FAILED_LOGIN`, `ACCOUNT_LOCKED`, `LOGIN_BLOCKED`, `ADMIN_ACCESS`,
  `ACCESS_DENIED`, `REGISTER_SUCCESS`, `LOGOUT`, `PRODUCT_CREATE/UPDATE/DELETE`,
  `UPLOAD_REJECTED`, `CSRF_FAILURE`.
- **Otorisasi**: middleware global default-deny (semua halaman wajib login kecuali katalog,
  login, register) + decorator `admin_required` di controller admin. Role dibaca dari
  database setiap request.
- **CRUD produk (admin)**: tambah, lihat, edit, hapus; upload gambar divalidasi ekstensi,
  ukuran (maks. 2 MB), dan isi biner (magic number), nama file diganti acak.
- **Katalog**: halaman utama menampilkan produk dalam grid, harga format Rupiah, status stok.
- **Dashboard admin**: penanda "Mode Admin", ringkasan jumlah produk, stok, stok habis,
  customer, dan produk terbaru.
- **Header keamanan**: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy.
- **Pengujian**: 24 tes pytest (auth, otorisasi, CRUD, upload berbahaya, XSS, CSRF, log).

### Cara uji
- `pytest -q` → 24 passed.
- Manual: `flask run --debug`, daftar akun customer, login, buka `/admin` (harus ditolak),
  login sebagai admin, tambah/edit/hapus produk, cek `logs/security.log`.
