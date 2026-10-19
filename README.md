# Elektronik Store - PBL RKS 323

Aplikasi web e-commerce monolitik untuk penjualan produk elektronik (handphone, laptop,
smartwatch, dan aksesoris). Dibangun dengan Flask dan database SQL, mengikuti pola MVC.

## Status Fitur

| Fitur | Status |
|---|---|
| Login + logging keamanan (login sukses/gagal, akses area admin) | Selesai |
| Register customer | Selesai |
| Manajemen produk / CRUD (khusus admin) | Selesai |
| Halaman utama / katalog produk | Selesai |
| Dashboard admin dasar | Selesai |
| Pengaturan akun (ubah nama, email & kata sandi) | Selesai |
| Tampilan sesuai desain Figma (mobile-first, admin desktop) | Selesai |
| Cari & filter katalog, detail produk, profil | Selesai |
| Keranjang belanja | Selesai |
| Checkout, bukti bayar, riwayat & status pesanan, ulasan, avatar, kelola akun, login Google, Midtrans | Berikutnya |

Riwayat perubahan ada di [CHANGELOG.md](CHANGELOG.md), kontrol keamanan dan format log ada di
[docs/KEAMANAN.md](docs/KEAMANAN.md).

## Teknologi

- Python 3.11+ dan Flask 3 (microframework)
- Flask-SQLAlchemy (ORM) + Flask-Migrate (migrasi tabel)
- Flask-WTF (validasi form + proteksi CSRF)
- PostgreSQL atau MySQL/MariaDB
- Tailwind CSS (CDN)
- pytest untuk pengujian

## Struktur Proyek

```
app.py                  # app factory, routing, error handler, perintah CLI
config.py               # konfigurasi dari environment (.env)
models/                 # Model: User, Produk
forms/                  # validasi input (WTForms)
controllers/            # Controller: auth, admin, produk, katalog
middlewares/            # autentikasi global + otorisasi role admin
helpers/                # upload gambar aman, logger keamanan
templates/              # View (Jinja2)
static/                 # js, folder upload gambar
migrations/             # file migrasi database
tests/                  # pengujian otomatis (pytest)
docs/                   # dokumentasi keamanan
```

## Cara Menjalankan

1. Buat virtual environment dan install dependensi:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Buat database kosong. Database utama proyek ini **PostgreSQL** (sesuai arsitektur SOC tim:
   database di zona terpisah dengan server primary dan backup).

   > **PostgreSQL di Windows lewat WSL:** jika installer Windows tidak bisa diunduh, pasang di WSL
   > Ubuntu: `wsl -d Ubuntu-24.04 -u root -- apt-get install -y postgresql`. Sebelum menjalankan
   > aplikasi, jalankan `scripts\start-postgres-wsl.bat` dan biarkan jendelanya terbuka.

   PostgreSQL:
   ```sql
   CREATE USER ecommerce_user WITH PASSWORD 'password_db';
   CREATE DATABASE db_ecommerce OWNER ecommerce_user;
   ```

   MySQL / MariaDB (alternatif):
   ```sql
   CREATE DATABASE db_ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. Salin `.env.example` menjadi `.env`, lalu isi `SECRET_KEY` dan `DATABASE_URL`.
   Membuat `SECRET_KEY` acak:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Buat tabel dan akun admin pertama:

   ```bash
   flask db upgrade
   flask seed-admin
   ```

   `flask seed-admin` akan menanyakan username, email, dan kata sandi admin
   (tidak ada kata sandi bawaan di dalam kode).

5. Jalankan aplikasi:

   ```bash
   flask run --debug
   ```

   Buka http://127.0.0.1:5000

## Menjalankan Pengujian

```bash
pytest -q
```

Pengujian memakai database SQLite sementara di memori, jadi tidak menyentuh database asli.

## Halaman

| URL | Akses | Keterangan |
|---|---|---|
| `/` | Semua | Beranda: produk unggulan, kategori, ekosistem brand |
| `/jelajah` | Semua | Semua produk + cari, filter, urutkan |
| `/produk/<id>` | Semua | Detail produk |
| `/register` | Tamu | Daftar akun customer |
| `/login` | Tamu | Login |
| `/logout` | Login | Logout (POST) |
| `/keranjang` | Login | Keranjang belanja (tambah/ubah/hapus lewat POST) |
| `/profil` | Login | Profil akun |
| `/pengaturan` | Login | Ubah nama, email & kata sandi |
| `/admin` | Admin | Dashboard admin |
| `/admin/produk` | Admin | Daftar produk |
| `/admin/produk/tambah` | Admin | Tambah produk |
| `/admin/produk/<id>/edit` | Admin | Edit produk |
| `/admin/produk/<id>/hapus` | Admin | Hapus produk (POST) |
