# Rencana & Matriks Pengujian Aplikasi (Quality Assurance)
Disusun oleh: **Ripasha Alvarisi L.** (Quality Assurance Engineer)
Proyek: PBL Rekayasa Keamanan Siber (RKS 323), Politeknik Negeri Batam

---

## 1. Matriks Cakupan Pengujian Otomatis (Pytest)

Pengujian perangkat lunak mencakup pengujian unit fungsional, pengujian integrasi database, hingga *automated dynamic security audit* (DAST):

| Modul Test | File Pengujian | Jumlah Test | Fokus Pengujian & Verifikasi |
| :--- | :--- | :---: | :--- |
| **Autentikasi & OTP** | `test_auth.py`, `test_otp_google.py` | 27 | Format email, validasi password kuat, Google Auth, alur OTP. |
| **RBAC & User Isolation** | `test_rbac_pengguna.py`, `test_akun.py` | 28 | Akses kontrol (admin/staf/pelanggan), token sesi, biodata profil. |
| **Katalog & Detail Toko** | `test_toko.py`, `test_detail_produk.py`, `test_qa_footer.py` | 27 | Filter multi-parameter, carousel hero, spesifikasi, 16 partner badge. |
| **Kupon & Voucher Checkout** | `test_kupon_checkout.py` | 6 | Diskon persen/nominal, batas maksimal potongan, validasi API AJAX. |
| **Wishlist & Favorit** | `test_wishlist_favorit.py` | 4 | Toggle favorit, isolasi wishlist antar-pengguna, response AJAX. |
| **Keranjang & Pesanan** | `test_keranjang.py`, `test_pesanan.py` | 44 | Stok decrement, kupon checkout, stepper status pesanan, pembayaran. |
| **Model ERD Best Practice** | `test_erd_best_practice.py` | 6 | Relasi kategori, kupon voucher, cascade constraint, pembayaran audit. |
| **Ulasan & Upload Avatar** | `test_ulasan_avatar_laporan.py` | 14 | Sanitasi file gambar Pillow, validasi rating bintang, ekspor laporan. |
| **Katalog Keamanan SOC** | `test_katalog_keamanan.py` | 11 | Audit logging event, sanitasi karakter XSS, penolakan path traversal. |
| **DAST Security Audit** | `test_dast_audit.py` | 6 | Fuzzing SQL Injection, XSS reflected, penegakan token CSRF, IDOR. |
| **Admin & Blueprints** | `test_admin_produk.py`, `test_blueprint.py` | 13 | Operasi CRUD produk admin, integritas rute blueprint Flask. |

---

## 2. Hasil Ringkasan Eksekusi Pengujian

- **Framework**: `pytest 9.1.1` (Python 3.13)
- **Total Test Cases**: **186 tests**
- **Tingkat Kelulusan (Pass Rate)**: **100% Passed (186/186)**
- **Waktu Eksekusi Total**: ~2 menit
- **Status Regresi**: Zero regression (semua dependensi terisolasi dengan aman di database memori / sqlite testing).
