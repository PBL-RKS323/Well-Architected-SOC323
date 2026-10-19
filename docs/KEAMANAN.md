# Dokumentasi Keamanan

Acuan: OWASP Top 10 2025, alur SSDLC (rencana → kode → uji → monitor) per fitur.

## Pemetaan OWASP Top 10 (2025)

| Risiko | Kontrol yang diterapkan | Lokasi |
|---|---|---|
| A01 Broken Access Control | Middleware default-deny, item keranjang & pesanan dicek kepemilikannya (anti IDOR, pesanan orang lain dijawab 404 dan dicatat), bukti bayar disimpan di luar folder publik dan hanya bisa dibuka pemilik/admin, cek role admin dari database tiap request, decorator `admin_required`, akun admin tidak bisa berbelanja (`pelanggan_required`, pemisahan tugas: admin tidak bisa membuat pesanan lalu menyetujui bukti bayarnya sendiri), aksi ubah data hanya lewat POST | `middlewares/auth_middleware.py`, `controllers/pesanan_controller.py` |
| A02 Security Misconfiguration | `SECRET_KEY` & `DATABASE_URL` wajib dari `.env` (aplikasi menolak jalan tanpa itu), debug mati secara default, header keamanan (CSP, X-Frame-Options, nosniff, Referrer-Policy), halaman error tanpa detail teknis | `config.py`, `app.py` |
| A03 Software Supply Chain Failures | Versi dependensi dikunci di `requirements.txt` | `requirements.txt` |
| A04 Cryptographic Failures | Kata sandi di-hash (Werkzeug scrypt), cookie sesi HttpOnly + SameSite=Lax, opsi `SESSION_COOKIE_SECURE` untuk HTTPS | `models/user.py`, `config.py` |
| A05 Injection | Query lewat ORM SQLAlchemy (terparameter), wildcard `%`/`_` di kata kunci pencarian di-escape, parameter filter & tanggal laporan divalidasi terhadap daftar/format yang diizinkan, output Jinja2 auto-escape (XSS, termasuk isi ulasan), input divalidasi WTForms, sel CSV laporan yang diawali `= + - @` diberi awalan `'` (CSV/formula injection) | `models/`, `forms/` |
| A06 Insecure Design | Role customer tidak bisa dipilih saat register, harga & ongkir dihitung ulang di server (bukan dari form), stok dipotong atomik saat checkout (tidak bisa minus walau checkout bersamaan), status pesanan hanya boleh pindah sesuai tabel transisi, maks. 3 pesanan belum lunas per akun (termasuk yang bukti bayarnya belum diverifikasi) dan batal otomatis setelah 24 jam (stok tidak bisa "ditahan"), pengiriman ganda checkout (klik dua kali) ditolak, kode pesanan acak, upload gambar diperiksa isi biner, nama file acak, ulasan hanya dari pembeli yang pesanannya selesai (anti ulasan palsu, satu ulasan per produk per akun), foto profil di-encode ulang tanpa EXIF (lokasi GPS tidak bocor) | `models/pesanan.py`, `controllers/`, `helpers/image_security.py` |
| A07 Authentication Failures | Kebijakan kata sandi kuat, ganti email/kata sandi wajib konfirmasi kata sandi lama, penguncian akun 5x gagal, pesan error login generik, sesi dibersihkan saat login (anti session fixation), sesi berakhir saat browser ditutup (atau 7 hari jika "Ingat saya"), ganti kata sandi membuat sesi di perangkat lain tidak berlaku (sidik hash kata sandi disimpan di sesi), CSRF di semua form | `controllers/auth_controller.py` |
| A08 Software or Data Integrity Failures | Token CSRF global, file upload divalidasi sebelum disimpan | `app.py`, `helpers/image_security.py` |
| A09 Security Logging and Alerting Failures | Log audit ke `logs/security.log`, format seragam untuk Wazuh, karakter baris baru dinetralkan (anti log injection) | `helpers/security_logger.py` |
| A10 Mishandling of Exceptional Conditions | Error handler 400/404/413/500 dengan pesan aman, redirect `next` hanya ke path internal | `app.py`, `controllers/auth_controller.py` |

## Format Log Keamanan (untuk Wazuh)

Lokasi default: `logs/security.log` (bisa diganti lewat `SECURITY_LOG_FILE`).

```
<waktu ISO 8601 WIB> | <LEVEL> | <EVENT> | src_ip=<ip> | key=value | ...
```

Contoh:

```
2026-10-19T14:30:00+07:00 | INFO | SUCCESSFUL_LOGIN | src_ip=192.168.20.10 | user_id=3 | username=budi | role=customer
2026-10-19T14:31:12+07:00 | WARNING | FAILED_LOGIN | src_ip=192.168.66.5 | email=admin@tokoelektronik.id | reason=invalid_password
2026-10-19T14:31:40+07:00 | WARNING | ACCOUNT_LOCKED | src_ip=192.168.66.5 | user_id=1 | username=admin | minutes=5
2026-10-19T14:35:02+07:00 | WARNING | ACCESS_DENIED | src_ip=192.168.20.10 | user_id=3 | username=budi | role=customer | path=/admin
```

| Event | Level | Kapan |
|---|---|---|
| `SUCCESSFUL_LOGIN` | INFO | Login berhasil |
| `FAILED_LOGIN` | WARNING | Login gagal (`reason=invalid_password` / `unknown_email`) |
| `ACCOUNT_LOCKED` | WARNING | Akun dikunci setelah 5 kali gagal (indikasi brute force) |
| `LOGIN_BLOCKED` | WARNING | Percobaan login ke akun yang sedang terkunci |
| `ADMIN_ACCESS` | INFO | Setiap request ke area `/admin` oleh admin |
| `ACCESS_DENIED` | WARNING | Non-admin mencoba membuka area `/admin`, atau user membuka pesanan / bukti bayar milik orang lain (`resource=pesanan` / `bukti_bayar`) |
| `REGISTER_SUCCESS` | INFO | Akun customer baru dibuat |
| `LOGOUT` | INFO | Logout |
| `PRODUCT_CREATE` / `PRODUCT_UPDATE` | INFO | Admin menambah / mengubah produk |
| `PRODUCT_DELETE` | WARNING | Admin menghapus produk |
| `UPLOAD_REJECTED` | WARNING | File upload ditolak (bukan gambar asli / terlalu besar) |
| `CSRF_FAILURE` | WARNING | Request form tanpa token CSRF yang valid |
| `EMAIL_CHANGED` / `PASSWORD_CHANGED` | WARNING | User mengganti email / kata sandi |
| `CREDENTIAL_CHANGE_FAILED` | WARNING | Ganti email/kata sandi gagal karena kata sandi lama salah |
| `ORDER_CREATE` | INFO | Pelanggan membuat pesanan (`kode`, `total`, `items`, `shipping`) |
| `PAYMENT_PROOF_UPLOADED` | INFO | Pelanggan mengunggah bukti transfer |
| `PAYMENT_VERIFIED` | INFO | Admin menerima pembayaran |
| `PAYMENT_REJECTED` | WARNING | Admin menolak bukti transfer |
| `ORDER_STATUS_CHANGE` | INFO | Status pesanan berubah (dikirim, siap diambil, selesai) |
| `ORDER_CANCELLED` | INFO / WARNING | Pesanan dibatalkan pelanggan (INFO) atau admin (WARNING) |
| `ORDER_INVALID_TRANSITION` | WARNING | Admin mencoba aksi yang tidak sah untuk status pesanan saat itu (indikasi request dimanipulasi) |
| `SESSION_INVALIDATED` | WARNING | Sesi lama dipakai setelah kata sandi diganti atau akun dinonaktifkan (`reason=`) |
| `USER_CREATED` / `USER_ROLE_CHANGED` | WARNING | Admin membuat akun / mengubah peran (`role_from`, `role_to`) |
| `USER_DEACTIVATED` / `USER_ACTIVATED` | WARNING | Admin menonaktifkan / mengaktifkan akun |
| `USER_UNLOCKED` | INFO | Admin membuka kunci login akun |
| `AVATAR_CHANGED` / `AVATAR_REMOVED` | INFO | User mengganti / menghapus foto profil |
| `REVIEW_CREATE` / `REVIEW_UPDATE` | INFO | Pembeli menulis / mengubah ulasan (`rating`) |
| `REVIEW_REJECTED` | WARNING | Akun yang belum menyelesaikan pembelian mencoba mengulas (`reason=not_purchased`) |
| `REVIEW_REPLY` | INFO | Staf membalas ulasan |
| `REVIEW_DELETE` | INFO / WARNING | Ulasan dihapus pemiliknya (INFO) atau staf (WARNING, `by=staff`) |
| `REPORT_EXPORTED` | WARNING | Admin mengunduh CSV laporan transaksi (`date_from`, `date_to`, `rows`): pantau unduhan massal |

## RBAC (Role-Based Access Control)

| Izin | Admin | Staf Toko | Pelanggan |
|---|---|---|---|
| panel (dasbor `/admin`) | ya | ya | - |
| kelola_produk | ya | ya | - |
| kelola_pesanan (verifikasi bayar, status, lihat bukti) | ya | ya | - |
| kelola_user | ya | - | - |
| lihat_laporan (laporan transaksi, CSV, angka pendapatan di dasbor) | ya | - | - |
| belanja (keranjang, checkout, pesanan & alamat sendiri, ulasan) | - | - | ya |

Dicek dua lapis: middleware untuk semua `/admin` (izin `panel`) dan `izin_required(...)` di tiap
controller. Peran dibaca dari database setiap request, jadi perubahan peran langsung berlaku.

Jika aplikasi berjalan di belakang Nginx, isi `TRUST_PROXY=1` agar `src_ip` berisi IP asli
klien, bukan IP Nginx.

Konfigurasi Wazuh agent (contoh `ossec.conf` di server web):

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/opt/elektronik-store/logs/security.log</location>
</localfile>
```

## Checklist SSDLC Sprint 1

- [x] Rencana: daftar fitur ATS dan ancaman utamanya (brute force, akses admin tanpa izin, upload berbahaya, XSS, CSRF)
- [x] Kode: kontrol di tabel OWASP di atas
- [x] Uji: 70 tes otomatis (`pytest -q`), termasuk uji negatif (akses ditolak, file palsu, password lemah)
- [x] Monitor: log keamanan siap dikirim ke Wazuh

## Checklist SSDLC Sprint 5 (Checkout & Pesanan)

- [x] Rencana: ancaman utama = manipulasi harga, membuka pesanan orang lain (IDOR), stok minus karena checkout bersamaan,
  bukti bayar bocor ke publik, upload file berbahaya, admin melompati status, stok ditahan pesanan yang tidak dibayar
- [x] Kode: harga dari database, `UPDATE ... WHERE stok >= jumlah`, cek pemilik pesanan, folder bukti bayar privat
  (`BUKTI_BAYAR_FOLDER`, default `instance/bukti_bayar/`) + header `Cache-Control: no-store`, tabel transisi status
  dengan UPDATE bersyarat (anti race condition), batas waktu bayar 24 jam, maks. 3 pesanan belum dibayar
- [x] Uji: 95 tes otomatis, lulus di SQLite dan PostgreSQL (`TEST_DATABASE_URL` ke database khusus uji)
- [x] Monitor: event pesanan & pembayaran baru di tabel log di atas

## Checklist SSDLC: Laporan, Ulasan, Avatar

- [x] Rencana: ancaman utama = ulasan palsu/spam, XSS lewat komentar, file berbahaya atau foto yang membocorkan
  lokasi (EXIF GPS), kebocoran data keuangan ke staf, CSV laporan yang menjalankan rumus saat dibuka di Excel,
  pengambilan data transaksi massal
- [x] Kode: syarat pesanan selesai + unique constraint per produk per akun, Jinja autoescape, foto profil dicek
  magic number lalu di-encode ulang dengan Pillow (EXIF terbuang, batas 40 juta piksel), izin `lihat_laporan`
  khusus admin, sel CSV dinetralkan, ekspor dicatat `REPORT_EXPORTED`
- [x] Uji: `tests/test_ulasan_avatar_laporan.py` (14 tes), lulus di SQLite dan PostgreSQL
- [x] Monitor: event ulasan, avatar, dan ekspor laporan di tabel log di atas
