# Instalasi Lengkap

Langkah cepat (SQLite) ada di [README](../README.md#cara-menjalankan). Halaman ini berisi pilihan
database lain, pengaturan `.env`, pengujian, dan pemecahan masalah.

## 1. Virtual environment & dependensi

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Versi library di `requirements.txt` sudah dikunci ke versi yang diuji (sama dengan server produksi).
Selalu instal dari file ini.

## 2. Pilih database

| Database | Kapan dipakai | `DATABASE_URL` di `.env` |
|---|---|---|
| SQLite | Mencoba cepat di laptop, tanpa memasang apa pun | `sqlite:///toko_lokal.db` (file dibuat di `instance/`) |
| PostgreSQL | Database utama proyek & server produksi | `postgresql+psycopg2://ecommerce_user:password_db@127.0.0.1:5432/db_ecommerce` |
| MySQL / MariaDB | Alternatif (XAMPP, Laragon) | `mysql+pymysql://root:password_db@127.0.0.1:3306/db_ecommerce` |

Ganti `password_db` dengan kata sandi milikmu sendiri.

**PostgreSQL**, buat user & database:

```sql
CREATE USER ecommerce_user WITH PASSWORD 'password_db';
CREATE DATABASE db_ecommerce OWNER ecommerce_user;
```

> **PostgreSQL di Windows lewat WSL:** jika installer Windows tidak bisa diunduh, pasang di WSL
> Ubuntu: `wsl -d Ubuntu-24.04 -u root -- apt-get install -y postgresql`. Sebelum menjalankan
> aplikasi, jalankan `scripts\start-postgres-wsl.bat` dan biarkan jendelanya terbuka.

**MySQL / MariaDB:**

```sql
CREATE DATABASE db_ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

File database dan folder `venv/` tidak pernah di-commit ke GitHub; setiap anggota membuatnya sendiri.

## 3. File `.env`

Salin `.env.example` menjadi `.env`, lalu isi minimal `SECRET_KEY` dan `DATABASE_URL`.
Membuat `SECRET_KEY` acak:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Pengaturan lain (opsional, penjelasannya ada di `.env.example`):

| Variabel | Fungsi |
|---|---|
| `TOKO_ALAMAT`, `BANK_NAMA`, `BANK_NOREK`, `BANK_ATAS_NAMA`, `ONGKIR_FLAT` | Data toko di halaman checkout (bawaan masih contoh/dummy) |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | Kode OTP lewat Gmail. Kosong = fitur email nonaktif |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Login dengan Google. Kosong = tombol Google disembunyikan |
| `TRUST_PROXY`, `SESSION_COOKIE_SECURE` | Isi `1` di server yang memakai Nginx + HTTPS |

Panduan Gmail App Password dan Google Cloud ada di [DEPLOY.md](DEPLOY.md).

## 4. Tabel, akun admin, dan data contoh

```bash
flask db upgrade        # membuat semua tabel
flask seed-admin        # menanyakan username, email, kata sandi admin (tidak ada sandi bawaan)
flask seed-katalog      # opsional: 17 produk contoh lengkap dengan foto & spesifikasi
flask run --debug       # buka http://127.0.0.1:5000
```

Akun anggota tim (staf/admin) dengan kata sandi sementara acak:

```bash
flask buat-pengguna --nama "Nama Lengkap" --email nama@contoh.id --peran staf
```

Kata sandinya ditulis ke `instance/akun_baru.txt`, bukan ke layar. Bagikan lewat pesan pribadi lalu hapus filenya.

## 5. Pengujian

```bash
pytest -q
```

Tes memakai database SQLite sementara di memori, jadi tidak menyentuh database asli.
Untuk menguji di PostgreSQL, buat database khusus uji (**isinya dihapus setiap tes**) lalu:

```bash
set TEST_DATABASE_URL=postgresql+psycopg2://ecommerce_user:password_db@127.0.0.1:5432/db_ecommerce_uji
pytest -q
```

## 6. Jika ada masalah

| Pesan | Penyebab & solusi |
|---|---|
| `Error: No such command 'db'` | venv belum aktif atau `pip install` gagal. Jalankan `venv\Scripts\activate`, ulangi `pip install -r requirements.txt`, lalu baca pesan error pertamanya. |
| `DLL load failed ... An Application Control policy has blocked this file` | Smart App Control Windows 11 memblokir library versi baru. `requirements.txt` sudah mengunci versi yang lolos (SQLAlchemy 2.1.5); pastikan menginstal dari file itu. |
| `RuntimeError: SECRET_KEY belum diisi` / `DATABASE_URL belum diisi` | File `.env` belum dibuat dari `.env.example`, atau isinya belum diganti. |
| `Format email tidak valid` saat login / `seed-admin` | Domain khusus seperti `.test`, `.local`, `.localhost` ditolak. Pakai email dengan domain biasa. |
| Perubahan template tidak muncul | Jalankan dengan `flask run --debug` agar template dimuat ulang otomatis. |

Langkah di halaman ini sudah diuji dari clone baru repo GitHub (venv baru + SQLite): migrasi,
`seed-admin`, `seed-katalog`, seluruh tes, dan login admin berjalan.
