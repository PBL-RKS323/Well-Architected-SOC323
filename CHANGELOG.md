# Changelog

Setiap perubahan dicatat di sini: apa yang berubah, alasannya, dan cara mengujinya.
Format tanggal: YYYY-MM-DD (WIB).

## [0.10.1] - 2026-10-30 - Siap Dijalankan dari Clone GitHub

Diuji dengan meng-clone branch `development` ke folder kosong, venv baru, dan SQLite.

### Diperbaiki
- Versi dependensi tidak langsung dikunci di `requirements.txt` (SQLAlchemy 2.1.5, alembic 1.20.0, WTForms 3.2.2,
  Werkzeug 3.1.9, Jinja2 3.1.6), sama dengan server produksi. Tanpa ini, instalasi baru mendapat SQLAlchemy 2.1.6
  yang DLL-nya diblokir Smart App Control Windows 11 sehingga `flask db upgrade` gagal.
- `flask seed-admin` dan `flask buat-pengguna` memakai validator email yang sama dengan form login. Sebelumnya
  email berdomain khusus (mis. `.test`) diterima CLI, padahal akun itu tidak akan pernah bisa login.

### Ditambahkan
- Contoh `DATABASE_URL` SQLite di `.env.example` dan tabel pemecahan masalah di README.
- `docs/PANDUAN-KODE.md`: panduan memahami kode untuk tim (alur, file per peran, pertanyaan dosen, urutan demo).

## [0.10.0] - 2026-10-30 - Blueprint & Detail Produk Lengkap

### Diubah
- **Route dipindah ke Blueprint** (syarat ATS: struktur kode dengan blueprint). Folder baru `routes/` berisi
  5 Blueprint: `toko`, `auth`, `belanja`, `akun`, `admin` (prefix `/admin`). `app.py` tidak lagi berisi
  daftar route. Path URL tidak berubah; nama endpoint memakai awalan Blueprint, mis. `url_for("auth.login")`.

### Ditambahkan
- **Detail produk lebih lengkap** (fitur dari prototipe UI Intan, tampilan tetap gaya toko ini):
  - kolom `spesifikasi` (satu baris per item, format `Nama: Nilai`) dan `garansi` di form produk admin;
  - ringkasan 3 spesifikasi pertama di bawah nama produk dan di kartu katalog;
  - breadcrumb Beranda › Kategori › Produk, label "Hemat Rp ...", badge jaminan toko;
  - tab Deskripsi / Spesifikasi / Pengiriman & Garansi (keyboard: panah kiri/kanan, Home/End).
    Tanpa JavaScript semua panel tetap tampil berurutan.
- Spesifikasi & garansi untuk 17 produk contoh di `seed/katalog.json`. `flask seed-katalog` melengkapi
  produk contoh lama yang spesifikasinya masih kosong, tanpa menimpa isian admin.
- Migrasi `a7d3e91c5f20` (kolom `produk.spesifikasi`, `produk.garansi`).
- Tes baru: `tests/test_blueprint.py` (5) dan `tests/test_detail_produk.py` (8), termasuk uji XSS pada
  isi spesifikasi.

**Cara uji:** `flask db upgrade` lalu `flask seed-katalog`; buka detail produk mana pun → breadcrumb,
ringkasan spesifikasi, dan tab tampil; tab Spesifikasi berisi tabel. Di admin, tambah produk dengan
spesifikasi berisi `<script>` → tampil sebagai teks biasa.

## [0.9.1] - 2026-10-30 - Perbaikan Email & Merek Laptop

### Diperbaiki
- Email dengan spasi di awal/akhir (sering terbawa saat salin-tempel) ditolak "Format email tidak valid".
  Sekarang semua form email (daftar, login, lupa kata sandi, ubah email, tambah/edit pengguna) membuang spasi
  dan mengecilkan huruf sebelum divalidasi.
- Koneksi database dicek sebelum dipakai (`pool_pre_ping`), agar tidak error 500 setelah PostgreSQL restart.

### Diubah
- Pilihan merek ditambah Lenovo, Asus, Dell, HP, dan Acer agar laptop bisa dijual. Teks toko tidak lagi
  menyebut hanya Apple, Samsung, dan Xiaomi.

**Cara uji:** ubah email ke `" nama@gmail.com "` (dengan spasi) → tersimpan sebagai `nama@gmail.com`;
tambah produk dengan merek Lenovo kategori Laptop → tampil di beranda dan filter Jelajah.

## [0.9.0] - 2026-10-20 - Login Google & Kode OTP Email

### Ditambahkan
- **Masuk/Daftar dengan Google** (Authlib, OpenID Connect). Email Google baru menjadi akun Pelanggan; akun
  Admin/Staf tetap memakai email + kata sandi.
- **Kode OTP lewat email** (Flask-Mail, Gmail SMTP + App Password): lupa kata sandi, verifikasi email pendaftar
  baru, dan OTP login Admin/Staf (opsional, `OTP_LOGIN_PANEL=1`).
- Tabel `kode_otp`, kolom `users.email_terverifikasi` dan `users.google_sub`.
- Panduan Google Cloud & Gmail di `docs/DEPLOY.md`; variabel baru di `.env.example`.

### Diubah
- Judul beranda "Belanja per Kategori" menjadi "Kategori Belanja". Banner "toko demo" dimatikan (DEMO_MODE=0).

### Cara uji
- `pip install -r requirements.txt`, `flask db upgrade`, `pytest -q` -> 152 passed.

## [0.8.1] - 2026-10-20 - Kelola Akun Lebih Lengkap, Carousel Otomatis

### Ditambahkan
- Kelola Pengguna: admin bisa mengubah nama/email akun lain dan **mereset kata sandi** (kata sandi sementara
  acak, tampil sekali di halaman dengan `Cache-Control: no-store`, sesi lama pemilik akun langsung berakhir).
  Akun sendiri tetap lewat Pengaturan. Event `USER_UPDATED`, `USER_PASSWORD_RESET`.
- Perintah `flask buat-pengguna` untuk membuat akun anggota tim dari server (kata sandi ke file chmod 600).
- Carousel beranda berputar otomatis tiap 3 detik dengan animasi geser dan tombol jeda.

### Diperbaiki
- File statis diberi versi (`?v=`) agar browser tidak memakai `app.js` lama dari cache.

## [0.8.0] - 2026-10-20 - Laporan Transaksi, Ulasan Produk, Foto Profil

Melengkapi 3 kebutuhan OUTPUT PBL 1 yang tersisa (no. 3, 7-8, 9).

### Ditambahkan
- **Laporan transaksi** (`/admin/laporan`, izin baru `lihat_laporan`, khusus admin): rentang tanggal (preset
  7/30 hari, bulan ini, bulan lalu, tahun ini, atau tanggal bebas, maks. 1 tahun), pendapatan, pesanan lunas &
  tingkat konversi, rata-rata per pesanan, barang terjual, grafik pendapatan per hari/bulan, status pesanan,
  produk terlaris, penjualan per merek, daftar transaksi, dan **unduh CSV** (aman dari formula injection).
- **Ulasan produk**: rating 1-5 + komentar di halaman produk, ringkasan rating & sebaran bintang. Hanya pembeli
  yang pesanannya sudah selesai yang bisa mengulas, satu ulasan per produk (bisa diubah/dihapus). Tautan
  "Beri ulasan" di detail pesanan selesai.
- **Moderasi ulasan** (`/admin/ulasan`, admin & staf): balas ulasan (tampil sebagai "Balasan Elektronik Store"),
  hapus ulasan yang melanggar, filter belum dibalas / rating rendah.
- **Foto profil**: unggah di Pengaturan, dipotong persegi 256 px, metadata EXIF dibuang. Avatar tampil di
  header, profil, ulasan, dan panel admin (inisial jika belum ada foto).
- Dasbor: tombol Laporan Transaksi, kartu "Ulasan belum dibalas". Staf tidak lagi melihat angka pendapatan.
- Dependensi baru: Pillow 12.3.0.

### Cara uji
- `flask db upgrade` (tabel `ulasan`, kolom `users.avatar`), `pytest -q` -> 132 passed.

## [0.7.0] - 2026-10-19 - RBAC, Kelola Pengguna, Alamat Saya

### Ditambahkan
- **RBAC**: peran Admin, Staf Toko, Pelanggan dengan daftar izin di `User.IZIN` (panel, kelola_produk,
  kelola_pesanan, kelola_user, belanja). Decorator `izin_required(...)` menggantikan `admin_required`;
  menu panel tampil sesuai izin.
- **Kelola Pengguna** (`/admin/pengguna`, khusus izin kelola_user): daftar & cari, tambah akun staf/admin,
  ubah peran, nonaktifkan/aktifkan, buka kunci login. Admin tidak bisa mengubah/menonaktifkan dirinya
  sendiri dan minimal harus ada satu admin aktif.
- **Alamat Saya** (`/alamat`): simpan sampai 5 alamat, satu alamat utama. Checkout otomatis memakai alamat
  utama, bisa pilih alamat lain, dan ada opsi "Simpan alamat ini".
- Kolom `users.aktif`: akun nonaktif tidak bisa login dan sesinya langsung berakhir.
- Event log: `USER_CREATED`, `USER_ROLE_CHANGED`, `USER_DEACTIVATED`, `USER_ACTIVATED`, `USER_UNLOCKED`.

### Cara uji
- `flask db upgrade` (tabel `alamat`, kolom `users.aktif`), `pytest -q` -> 118 passed.

## [0.6.0] - 2026-10-19 - Review Keamanan, Tampilan HP & Desktop, Katalog 17 Produk

### Diperbaiki (cacat logika & keamanan)
- Ganti kata sandi sekarang membuat sesi di perangkat lain tidak berlaku (`SESSION_INVALIDATED`), dan
  pilihan "Ingat saya" tidak berubah jadi 7 hari setelah ganti kata sandi.
- Akun admin tidak bisa berbelanja (keranjang, checkout, pesanan) agar tidak bisa membuat pesanan lalu
  menyetujui bukti bayarnya sendiri.
- Batas pesanan belum lunas ikut menghitung pesanan yang bukti bayarnya belum diverifikasi.
- Checkout yang terkirim dua kali (klik ganda) tidak membuat pesanan ganda; tombol dikunci setelah klik.
- "Beli Sekarang" langsung ke checkout.

### Diubah (tampilan)
- HP: harga tidak lagi terpotong ("Rp" dan angka selalu satu baris), tombol + di kartu produk dipindah ke
  pojok foto, tab Pesanan Saya muat di layar.
- Admin di HP: navigasi bawah 5 menu, daftar produk & pesanan berupa kartu (tanpa geser ke samping).
- Desktop: kolom cari di header, baris kategori, footer 4 kolom (info toko, belanja, akun), area akun
  dengan sidebar (Profil, Pesanan Saya, Pengaturan), Pesanan Saya 2 kolom, profil menampilkan pesanan terbaru.
- Beranda: carousel 3 produk diskon terbesar (geser manual, tidak berganti otomatis).
- Status pesanan tampil sebagai teks berwarna tanpa titik & latar.
- Foto katalog dipotong ulang tanpa efek blur; foto Galaxy Watch 7 & Galaxy S24 Ultra diganti.
- Header halaman (tombol kembali + judul) menjadi macro `judul_halaman` agar mudah dirawat.

### Ditambahkan
- Nomor resi otomatis `JJN` + 10 angka (kurir fiktif) jika admin tidak mengisi resi.
- Katalog contoh jadi 17 produk (semua kategori terisi). `flask seed-katalog --perbarui-foto` mengganti
  foto produk contoh yang sudah ada tanpa mengubah harga/stok.

### Cara uji
- `pytest -q` (semua lulus).

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
