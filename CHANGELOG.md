# Changelog

Setiap perubahan dicatat di sini: apa yang berubah, alasannya, dan cara mengujinya.
Format tanggal: YYYY-MM-DD (WIB).

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
