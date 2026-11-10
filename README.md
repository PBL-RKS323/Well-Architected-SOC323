# Well-Architected-SOC323

Proyek PBL tim SOC323 (RKS 3B, Politeknik Negeri Batam): aplikasi web e-commerce **Elektronik Store**
(Flask, pola MVC + Blueprint) beserta konfigurasi infrastruktur SOC.

**Live:** https://toko.neteye.my.id

## Fitur

- **Pelanggan:** daftar, login (+ Google & kode OTP email), cari & filter produk, detail produk dengan
  spesifikasi dan ulasan, keranjang, checkout, unggah bukti bayar, riwayat pesanan, profil & alamat.
- **Admin / Staf:** kelola produk, verifikasi pembayaran & status pesanan, balas ulasan, laporan transaksi
  (CSV), kelola pengguna dan peran (RBAC).
- **Keamanan:** hash kata sandi, CSRF, kunci akun setelah 5x gagal login, upload gambar aman,
  header keamanan, log keamanan untuk Wazuh.

Semua kebutuhan minimal *OUTPUT PBL 1* sudah terpenuhi.

**Teknologi:** Python 3.11+, Flask 3, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, PostgreSQL,
Jinja2, Tailwind CSS, pytest.

## Tim

| Anggota | Peran | Bagian |
|---|---|---|
| Yudha Pratama | Ketua tim, Frontend | `templates/`, `static/`, `infrastructure/`, review Pull Request |
| Intan Sri Diana | Desain UI/UX | `frontend/` (prototipe), `templates/`, `static/` |
| Pedro Juanda Sebayang | Backend | `routes/`, `controllers/`, `models/`, `migrations/` |
| Ripasha Alvarisi L. | Quality Assurance | `tests/` |
| Ihsan Alfareno | Fitur tambahan & keamanan | fitur baru, audit keamanan / pentest |

## Struktur Folder

**Ringkasnya:** frontend = `templates/` + `static/`; backend = semua folder Python (`routes/`,
`controllers/`, `models/`, `forms/`, `middlewares/`, `helpers/`, `migrations/`), ditambah `app.py`
dan `config.py`.

| Bagian | Folder |
|---|---|
| Frontend | `templates/` (halaman HTML), `static/` (JavaScript, foto upload) |
| Backend | `routes/` (Blueprint), `controllers/` (logika), `models/` (database), `forms/` (validasi), `middlewares/` (login & hak akses), `helpers/`, `migrations/`, `app.py`, `config.py` |
| Pendukung | `tests/` (pengujian), `docs/` (dokumentasi), `seed/` (produk contoh), `deploy/` (Nginx & systemd) |
| Lainnya | `frontend/` (prototipe UI Figma, tidak dijalankan), `infrastructure/` (Wazuh, OPNsense, Cloudflare) |

## Cara Menjalankan

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Salin `.env.example` menjadi `.env`, lalu isi:
- `SECRET_KEY` dengan string acak: `python -c "import secrets; print(secrets.token_hex(32))"`
- `DATABASE_URL=sqlite:///toko_lokal.db` (cara tercepat untuk mencoba; produksi memakai PostgreSQL)

```bash
flask db upgrade
flask seed-admin
flask seed-katalog
flask run --debug
```

Buka http://127.0.0.1:5000. Pengujian: `pytest -q`.

PostgreSQL/MySQL, pengaturan email & Google, dan solusi error ada di [docs/INSTALASI.md](docs/INSTALASI.md).

## Alur Kerja Git

- `main` = versi stabil (dinilai & di-deploy), `development` = gabungan pekerjaan tim.
- Buat branch dari `development`: `git checkout development && git pull && git checkout -b fitur/nama-fitur`
- Commit dengan akun GitHub sendiri, push, lalu buka **Pull Request ke `development`**. Ketua tim yang merge.
- Jalankan `pytest -q` sebelum Pull Request. Jangan commit `.env`, database, atau `venv/`.

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [docs/PANDUAN-KODE.md](docs/PANDUAN-KODE.md) | Cara kerja kode, file wajib dibaca per anggota, pertanyaan dosen + jawaban, urutan demo |
| [docs/BACKEND_ERD.md](docs/BACKEND_ERD.md) | Arsitektur database, ERD, normalisasi 3NF, relasi kategori, kupon, favorit, dan pembayaran (Pedro) |
| [docs/KOMPONEN_UI.md](docs/KOMPONEN_UI.md) | Panduan desain UI/UX e-shop, palet warna coral, tipografi, dan komponen antarmuka (Intan) |
| [docs/RENCANA_PENGUJIAN.md](docs/RENCANA_PENGUJIAN.md) | Matriks pengujian QA otomatis (186 pytest cases lulus 100%) dan skenario pengujian (Ripasha) |
| [docs/AUDIT_KEAMANAN.md](docs/AUDIT_KEAMANAN.md) | Laporan audit SAST Bandit, DAST audit suite, SCA dependensi, dan aturan Wazuh SOC (Ihsan) |
| [docs/INSTALASI.md](docs/INSTALASI.md) | Instalasi lengkap, pengujian, solusi error |
| [docs/KEAMANAN.md](docs/KEAMANAN.md) | Kontrol keamanan & format log |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Deploy ke server, HTTPS, Gmail & Google login |
| [docs/DESIGN.md](docs/DESIGN.md) | Arah desain tampilan |
| [CHANGELOG.md](CHANGELOG.md) | Riwayat perubahan |
