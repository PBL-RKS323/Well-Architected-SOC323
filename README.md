# Well-Architected-SOC323

Repositori proyek PBL tim SOC323 (RKS 3B, Politeknik Negeri Batam): aplikasi web e-commerce
**Elektronik Store** beserta prototipe UI dan konfigurasi infrastruktur SOC.

Aplikasi live: https://toko.neteye.my.id

## Tim & Pembagian Peran

| Anggota | Peran | Bagian yang dipegang |
|---|---|---|
| Yudha Pratama | Ketua tim, Frontend | `infrastructure/`, review & merge Pull Request |
| Intan Sri Diana | Desain UI/UX | `frontend/` (prototipe UI), `templates/`, `static/` |
| Pedro Juanda Sebayang | Backend | `routes/`, `controllers/`, `models/`, `migrations/` |
| Ripasha Alvarisi L. | Quality Assurance | `tests/`, rencana & laporan pengujian |
| Ihsan Alfareno | Fitur tambahan & kualitas | fitur baru, audit keamanan / pentest |

## Isi Repositori

| Folder | Isi |
|---|---|
| *(root)* | Aplikasi web Flask monolit (MVC): `app.py`, `routes/`, `controllers/`, `models/`, `templates/`, ... |
| `frontend/` | Prototipe UI dari Figma oleh Intan (referensi desain, bukan aplikasi yang di-deploy) |
| `infrastructure/` | Konfigurasi Wazuh, OPNsense, dan skrip Cloudflare |
| `docs/` | Dokumentasi keamanan, desain, dan deploy |

Aplikasi web sengaja tidak dipecah ke folder frontend dan backend terpisah: pada Flask monolit,
tampilan (`templates/`, `static/`) dan logika (`routes/`, `controllers/`, `models/`) berjalan sebagai
satu aplikasi. Pembagian tanggung jawabnya ada di tabel **Tim & Pembagian Peran** di atas.

## Alur Kerja Git

- `main` = versi stabil (yang dinilai & di-deploy). `development` = tempat menggabungkan pekerjaan tim.

1. Jangan bekerja langsung di `main` maupun `development`. Buat branch dari `development`:
   `git checkout development && git pull && git checkout -b fitur/halaman-bantuan`.
2. Commit dengan akun GitHub sendiri (`git config user.email` = email akun GitHub) agar kontribusi tercatat.
3. `git push -u origin <nama-branch>`, lalu buka Pull Request ke `development`. Ketua tim mereview dan merge.
   Penggabungan `development` ke `main` dilakukan ketua tim setelah disepakati.
4. Jalankan `pytest` sebelum membuka Pull Request. Jangan pernah meng-commit `.env`, database, atau `venv/`.

## Memahami Kode (ringkas)

Aplikasi memakai pola **MVC + Blueprint**. Analogi restoran:

| Folder | Di restoran | Tugas |
|---|---|---|
| `routes/` | Pelayan | Menerima URL, meneruskan ke controller (5 Blueprint) |
| `controllers/` | Koki | Logika tiap fitur |
| `forms/` | Pemeriksa pesanan | Validasi input di server |
| `models/` | Gudang bahan | Tabel database sebagai class Python |
| `templates/`, `static/` | Penyajian | Halaman HTML (Jinja2), JavaScript |
| `middlewares/` | Satpam | Wajib login & hak akses per peran (RBAC) |
| `helpers/` | Alat dapur | Upload aman, log keamanan, email |
| `migrations/` | Catatan renovasi | Riwayat perubahan struktur tabel |
| `tests/` | Pencicip | 165 tes otomatis (`pytest -q`) |

Contoh alur tombol **Masuk**: `routes/auth.py` → `forms/auth_form.py` (cek input + CSRF) →
`controllers/auth_controller.py` → `models/user.py` (cocokkan hash kata sandi) →
`helpers/security_logger.py` (catat ke `logs/security.log`) → `templates/auth/login.html`.

Penjelasan lengkap, file wajib dibaca per anggota, **daftar pertanyaan dosen beserta jawabannya**, dan
urutan demo ada di **[docs/PANDUAN-KODE.md](docs/PANDUAN-KODE.md)**.

---

## Aplikasi Web: Elektronik Store

Aplikasi web e-commerce monolitik untuk penjualan produk elektronik (handphone, laptop,
smartwatch, dan aksesoris). Dibangun dengan Flask dan database SQL, mengikuti pola MVC.

## Status Fitur

Kebutuhan fungsional minimal dari *OUTPUT PBL 1* (RKS 304) sudah terpenuhi semua:

| No | Kebutuhan | Halaman | Status |
|---|---|---|---|
| 1 | Admin kelola data barang (tambah, edit, hapus) | `/admin/produk` | Selesai |
| 2 | Admin kelola akun pengguna | `/admin/pengguna` | Selesai |
| 3 | Admin lihat laporan ringkasan transaksi | `/admin/laporan` (+ unduh CSV) | Selesai |
| 4 | Admin lihat & setujui bukti bayar | `/admin/pesanan` | Selesai |
| 5 | Customer registrasi, login, logout | `/register`, `/login` | Selesai |
| 6 | Customer cari & filter katalog | `/jelajah` | Selesai |
| 7 | Customer lihat detail barang dengan ulasan | `/produk/<id>` | Selesai |
| 8 | Customer beri ulasan & komentar | `/produk/<id>#ulasan` | Selesai |
| 9 | Customer kelola profil & upload foto avatar | `/profil`, `/pengaturan` | Selesai |
| 10 | Customer masukkan barang ke cart | `/keranjang` | Selesai |
| 11 | Customer checkout | `/checkout` | Selesai |
| 12 | Customer upload bukti bayar | `/pesanan/<kode>` | Selesai |
| 13 | Customer lihat riwayat pesanan | `/pesanan` | Selesai |

Tambahan: RBAC 3 peran (Admin, Staf Toko, Pelanggan), alamat tersimpan, balasan toko untuk ulasan,
login Google + kode OTP email, spesifikasi & garansi produk, log keamanan untuk Wazuh.
Rencana berikutnya: Midtrans Sandbox (VA bank, QRIS/e-wallet).

Riwayat perubahan ada di [CHANGELOG.md](CHANGELOG.md), kontrol keamanan dan format log ada di
[docs/KEAMANAN.md](docs/KEAMANAN.md), arah desain dan alasannya ada di [docs/DESIGN.md](docs/DESIGN.md).

## Teknologi

- Python 3.11+ dan Flask 3 (microframework)
- Flask-SQLAlchemy (ORM) + Flask-Migrate (migrasi tabel)
- Flask-WTF (validasi form + proteksi CSRF)
- PostgreSQL atau MySQL/MariaDB
- Tailwind CSS (CDN)
- pytest untuk pengujian

## Struktur Proyek

```
app.py                  # app factory, error handler, perintah CLI
config.py               # konfigurasi dari environment (.env)
routes/                 # Blueprint (daftar URL): toko, auth, belanja, akun, admin
models/                 # Model: User, Produk, KeranjangItem, Pesanan
forms/                  # validasi input (WTForms)
controllers/            # Controller: auth, akun, toko, keranjang, pesanan, admin, produk
middlewares/            # autentikasi global + otorisasi role admin
helpers/                # upload gambar aman, logger keamanan, format waktu WIB
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

   **Hanya ingin mencoba cepat tanpa memasang database?** Pakai SQLite (file database dibuat
   otomatis di folder `instance/`). Isi di `.env`: `DATABASE_URL=sqlite:///toko_lokal.db`.
   Untuk produksi tetap gunakan PostgreSQL. File database dan folder `venv/` tidak pernah
   di-commit ke GitHub; setiap anggota membuatnya sendiri dengan langkah di halaman ini.

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

   Opsional, isi 17 produk contoh lengkap dengan foto dan spesifikasi:

   ```bash
   flask seed-katalog
   ```

5. Jalankan aplikasi:

   ```bash
   flask run --debug
   ```

   Buka http://127.0.0.1:5000

## Alur Pesanan

```
Menunggu Pembayaran --(pelanggan unggah bukti)--> Menunggu Verifikasi --(admin terima)--> Diproses
        ^                                              |                                   |
        +-------------(admin tolak + alasan)-----------+                     kurir: Dikirim --> Selesai
                                                                             ambil: Siap Diambil --> Selesai
Batal: pelanggan (sebelum kirim bukti), admin (sebelum dikirim), atau otomatis 24 jam tanpa pembayaran.
Stok dipotong saat checkout dan dikembalikan jika pesanan batal.
```

Data toko untuk checkout (alamat toko, rekening, ongkir) masih **contoh/dummy** dan bisa diganti di `.env`
(`TOKO_ALAMAT`, `BANK_NAMA`, `BANK_NOREK`, `BANK_ATAS_NAMA`, `ONGKIR_FLAT`).

## Menjalankan Pengujian

```bash
pytest -q
```

Pengujian memakai database SQLite sementara di memori, jadi tidak menyentuh database asli.
Untuk menguji di PostgreSQL, buat database khusus uji (isinya dihapus setiap tes!) lalu:

```bash
set TEST_DATABASE_URL=postgresql+psycopg2://ecommerce_user:password_db@127.0.0.1:5432/db_ecommerce_uji
pytest -q
```

## Halaman

| URL | Akses | Keterangan |
|---|---|---|
| `/` | Semua | Beranda: produk unggulan, kategori, ekosistem brand |
| `/jelajah` | Semua | Semua produk + cari, filter, urutkan |
| `/produk/<id>` | Semua | Detail produk + ulasan pembeli |
| `/produk/<id>/ulasan` | Pembeli (pesanan selesai) | Tulis / ubah ulasan (POST) |
| `/register` | Tamu | Daftar akun customer |
| `/login` | Tamu | Login |
| `/logout` | Login | Logout (POST) |
| `/keranjang` | Login | Keranjang belanja (tambah/ubah/hapus lewat POST) |
| `/checkout` | Login | Pilih pengiriman (kurir / ambil di toko), isi alamat, buat pesanan |
| `/pesanan` | Login | Pesanan Saya: cari, filter status |
| `/pesanan/<kode>` | Pemilik | Detail, lacak status, unggah bukti bayar, batalkan, konfirmasi diterima |
| `/pesanan/<kode>/bukti` | Pemilik / Admin | Gambar bukti bayar (tidak bisa diakses publik) |
| `/profil` | Login | Profil akun |
| `/pengaturan` | Login | Foto profil, ubah nama, email & kata sandi |
| `/alamat` | Pelanggan | Alamat tersimpan (maks. 5, satu alamat utama) |
| `/admin` | Admin | Dashboard admin |
| `/admin/produk` | Admin | Daftar produk |
| `/admin/produk/tambah` | Admin | Tambah produk |
| `/admin/produk/<id>/edit` | Admin | Edit produk |
| `/admin/produk/<id>/hapus` | Admin | Hapus produk (POST) |
| `/admin/pesanan` | Admin | Daftar pesanan per status + pencarian |
| `/admin/pesanan/<id>` | Admin | Detail pesanan, cek bukti bayar, terima/tolak, kirim (resi), siap diambil, selesai, batalkan |
| `/admin/ulasan` | Admin / Staf | Balas & hapus ulasan |
| `/admin/laporan` | Admin | Laporan transaksi per rentang tanggal, unduh CSV |
| `/admin/pengguna` | Admin | Kelola akun: tambah staf, ubah peran, nonaktifkan, buka kunci |
