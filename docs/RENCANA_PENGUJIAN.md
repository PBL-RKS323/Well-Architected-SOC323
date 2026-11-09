# Rencana Pengujian Aplikasi (Quality Assurance)

Dokumen ini disusun oleh tim QA (Ripasha) sebagai matriks skenario pengujian otomatis dan manual untuk aplikasi e-commerce PBL RKS 323.

## 1. Cakupan Pengujian Otomatis (Pytest)

- **Modul Autentikasi (`test_auth.py`, `test_otp_google.py`)**:
  - Validasi kekuatan password saat registrasi (kombinasi huruf besar, kecil, angka, simbol).
  - Penolakan login dengan kredensial salah dan aktivasi lockout setelah 5 kali percobaan gagal.
  - Verifikasi kode OTP dan alur pemulihan kata sandi.
- **Modul Katalog & Toko (`test_toko.py`, `test_detail_produk.py`, `test_qa_footer.py`)**:
  - Penelusuran produk berdasarkan kata kunci, filter harga minimum/maksimum, dan filter kategori.
  - Verifikasi kelengkapan spesifikasi produk dan rendering badge partner di footer.
- **Modul Belanja & Keranjang (`test_keranjang.py`, `test_pesanan.py`)**:
  - Penambahan barang ke keranjang, penyesuaian kuantitas, dan validasi stok.
  - Alur checkout belanja dan kalkulasi total ongkos kirim.
- **Modul Akses Kontrol RBAC (`test_rbac_pengguna.py`, `test_admin_produk.py`)**:
  - Pengujian isolasi hak akses: memastikan pengguna biasa ditolak saat mengakses `/admin`.
  - Pengujian alur CRUD produk oleh akun administrator.

## 2. Hasil Ringkasan Eksekusi

Seluruh skenario pengujian unit dan integrasi dijalankan otomatis menggunakan framework pytest dengan tingkat kelulusan 100%.
