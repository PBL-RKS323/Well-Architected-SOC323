# CHECKLIST WEB E-COMMERCE

**Kode PBL:** RKS-323 (Well-Architected-SOC323)  
**Tema E-commerce:** Elektronik Store (e-shop) - Platform E-Commerce Terintegrasi Wazuh SIEM SOC

---

## Daftar Anggota
| NIM | Nama | Peran |
|---|---|---|
| 4332501048 | Ihsan Alfareno | Security Engineer & SOC |
| 4332501057 | Intan Sri Diana | UI/UX Designer & Frontend |
| 4332501041 | Pedro Juanda Sebayang | Backend Developer |
| 4332501053 | Ripasha Alvarisi L. | Quality Assurance (QA) & Tester |
| 4332501059 | Yudha Pratama | Team Leader & DevSecOps |

---

## Panduan untuk AI Agent
*   Tugas di bawah ini adalah fitur wajib yang harus diimplementasikan.
*   Gunakan `[ ]` untuk fitur yang belum selesai, dan `[x]` untuk fitur yang sudah selesai.
*   Kolom **Paraf Dosen** dan **Catatan** dapat diisi oleh agent atau user saat evaluasi.

---

## Checklist Progres

- [x] **FR-001: Customer / User - Registrasi Akun**
  - [x] Form pendaftaran akun customer baru
  - [x] Validasi input data (email, password, nama, dst)
  - [x] Enkripsi password (password hashing)
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Form pendaftaran di `templates/auth/register.html`, controller `controllers/auth_controller.py:register()`, validasi regex ketat pada `forms/auth_form.py:RegisterForm`, dan hashing PBKDF2:SHA256 pada `models/user.py`. Dilengkapi opsi login/register Google OIDC dan verifikasi OTP email.

- [x] **FR-002: Autentikasi - Login & Logout**
  - [x] Form login untuk Customer dan Admin
  - [x] Proteksi akses halaman berbasis peran (role-based access)
  - [x] Fitur logout dan manajemen sesi (session/token)
  - [x] Logging autentikasi gagal dan login admin
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Form login di `templates/auth/login.html` dan controller `controllers/auth_controller.py:login()`. Sistem RBAC dengan permission mapping di `models/user.py` serta middleware otorisasi default-deny di `middlewares/auth_middleware.py`. Fitur logout aman via POST CSRF di `controllers/auth_controller.py:logout()`. Token sesi dinamis (`sesi_token`) otomatis mencabut akses perangkat lain saat ganti kata sandi. Proteksi brute-force 5x gagal kunci akun 5 menit, terintegrasi audit logger Wazuh di `helpers/security_logger.py`.

- [x] **FR-003: Customer - Katalog Produk (Halaman Utama)**
  - [x] Tampilan utama katalog barang / produk pilihan
  - [x] Pencarian produk berdasarkan nama (search)
  - [x] Pengelompokan / filter berdasarkan kategori produk
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Halaman utama di `templates/toko/beranda.html` dengan banner carousel auto-slide dan kartu produk responsif. Pencarian dan filter kategori di `controllers/toko_controller.py:jelajah()` dan `templates/toko/jelajah.html`, mendukung sortir harga termurah/termahal/terbaru, filter merek, sanitasi query SQLi, serta relasi tabel `Kategori` di database.

- [x] **FR-004: Admin - CRUD Katalog Barang**
  - [x] Tambah produk baru (nama, deskripsi, harga, stok, & unggah foto, dst)
  - [x] Lihat dan kelola seluruh daftar katalog produk
  - [x] Edit / perbarui informasi dan foto produk
  - [x] Hapus produk dari katalog
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Kelola katalog admin di `controllers/admin_produk_controller.py` dan template `templates/admin/produk/`. Mendukung form upload gambar aman (validasi MIME/magic bytes dan sanitasi EXIF via `helpers/image_security.py`), spesifikasi teknis, garansi, harga normal/diskon, dan perlindungan hapus jika terkait pesanan aktif.

- [x] **FR-005: Customer - Detail Produk & Ulasan**
  - [x] Halaman detail spesifikasi dan stok produk
  - [x] Melihat ulasan/penilaian dari pembeli lain
  - [x] Form penulisan ulasan & rating produk
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Halaman detail di `templates/toko/produk_detail.html` dan `controllers/toko_controller.py:produk_detail()`. Menampilkan tab spesifikasi, status stok, garansi, tombol favorit wishlist, rating bintang 1-5, daftar ulasan pembeli terverifikasi, form ulasan (`forms/ulasan_form.py`), serta fitur admin membalas ulasan.

- [x] **FR-006: Customer - Keranjang Belanja & Checkout**
  - [x] Menambah, mengubah jumlah, atau menghapus item di keranjang (cart)
  - [x] Ringkasan belanja dan proses pengisian data checkout
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Keranjang belanja di `controllers/keranjang_controller.py`, model `models/keranjang.py`, dan template `templates/belanja/keranjang.html` (validasi stok real-time). Checkout belanja di `controllers/pesanan_controller.py:checkout()` dan `templates/belanja/checkout.html`, mendukung integrasi Buku Alamat, kurir/ambil sendiri, ongkir dinamis, dan validasi kupon diskon voucher (AJAX).

- [x] **FR-007: Customer - Upload Bukti Bayar & Riwayat**
  - [x] Form unggah foto/file bukti transfer pembayaran
  - [x] Halaman riwayat transaksi dan penelusuran status pesanan
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Form upload bukti bayar di `templates/belanja/pesanan_detail.html` dan `controllers/pesanan_controller.py:unggah_bukti_bayar()`. Berkas bukti bayar disimpan di luar webroot publik (`instance/bukti_bayar/`) untuk privasi finansial. Pelacakan status 5 tahap dengan visual stepper (*Menunggu Pembayaran -> Menunggu Verifikasi -> Diproses -> Dikirim -> Selesai*), terintegrasi di dasbor Profil Pengguna.

- [x] **FR-008: Admin - Approval Bukti Bayar**
  - [x] Melihat daftar transaksi & foto bukti transfer customer
  - [x] Verifikasi persetujuan (Approve) atau penolakan (Reject)
  - [x] *Alternatif:* Sistem pembayaran menggunakan Midtrans Sandbox
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Panel admin verifikasi pesanan di `controllers/admin_pesanan_controller.py` dan `templates/admin/pesanan/`. Admin dapat melihat preview bukti bayar secara aman via endpoint terlindungi (`/admin/pesanan/<kode>/bukti`). Verifikasi Approve mengubah status ke `diproses` dan mencatat data verifikator di tabel `pembayaran`; Reject dapat membatalkan pesanan. Sistem transfer bank terverifikasi + model audit finansial telah beroperasi penuh.

- [x] **FR-009: Admin - Manajemen Akun Pengguna**
  - [x] Melihat daftar akun terdaftar (Customer & Admin)
  - [x] Kelola status aktif/nonaktif atau hapus akun pengguna
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Manajemen pengguna di `controllers/admin_user_controller.py` dan `templates/admin/user/daftar.html`. Admin dapat melihat daftar pengguna, mengubah peran RBAC (`admin`, `staf`, `customer`), menonaktifkan/mengaktifkan akun (mencabut sesi instan tanpa merusak riwayat transaksi), membuka akun terkunci (*unlock* brute-force), dan mereset kata sandi sementara.

- [x] **FR-010: Admin - Laporan Transaksi**
  - [x] Rekapitulasi laporan penjualan berdasarkan rentang tanggal
  - [x] Cetak / export laporan ke format PDF atau Excel
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Laporan penjualan di `controllers/admin_laporan_controller.py` dan `templates/admin/laporan/index.html`. Rekapitulasi omset, total pesanan sukses, dan item terlaris berdasarkan filter tanggal. Ekspor laporan ke file CSV (dapat dibuka di Microsoft Excel / Google Sheets) dilengkapi sanitasi proteksi CSV/Formula Injection (CWE-1236).

- [x] **FR-011: Pengujian & Deployment Sistem**
  - [x] Pengujian fungsionalitas sistem (unit testing)
  - [x] Peluncuran aplikasi (deployment)
  - **Paraf Dosen:** 
  - **Catatan:** Selesai 100%. Suite pengujian otomatis menggunakan Pytest dengan **193 test cases lulus 100%** (mencakup unit test model, controller, RBAC, keranjang, checkout, kupon, wishlist, ulasan, serta DAST audit). Audit keamanan SAST Bandit lulus dengan **0 High, 0 Medium vulnerabilities**. Konfigurasi deployment siap produksi dengan Nginx reverse proxy, HTTPS, Gunicorn, systemd service, dan live di `https://toko.neteye.my.id`.
