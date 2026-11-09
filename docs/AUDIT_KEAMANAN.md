# Laporan Audit Keamanan & Hardening Aplikasi

Dokumen ini disusun oleh tim Keamanan Siber (Ihsan Alfareno) sebagai inventarisasi kontrol keamanan aplikasi e-commerce PBL RKS 323.

## 1. Mekanisme Pertahanan Aplikasi

- **Otentikasi & Manajemen Sesi**:
  - Penyimpanan kata sandi menggunakan fungsi hash satu arah Werkzeug (PBKDF2/scrypt).
  - Pembatasan upaya login: penguncian akun sementara setelah 5 kali gagal untuk mitigasi serangan brute-force.
  - Mitigasi timing attack: komparasi hash palsu saat email login tidak terdaftar.
  - Invalidasi sesi: hash SHA-256 dipasang pada sesi sehingga saat kata sandi diganti, sesi aktif di perangkat lain langsung tidak berlaku.
- **Proteksi Formulir & Request**:
  - Flask-WTF CSRF protection aktif pada seluruh form transaksi dan perubahan data.
  - Validasi ketat sisi klien (HTML5) dan sisi server (WTForms field validators).
  - Sanitasi file upload: pengecekan magic bytes biner menggunakan library deteksi tipe berkas untuk mencegah ekstensi palsu atau web shell.
- **Header Keamanan HTTP**:
  - `Content-Security-Policy`: membatasi eksekusi skrip pihak ketiga yang tidak tepercaya.
  - `X-Frame-Options: DENY`: mencegah serangan clickjacking.
  - `X-Content-Type-Options: nosniff`: mencegah MIME type sniffing.
  - `Strict-Transport-Security` (HSTS): memastikan komunikasi terenkripsi penuh melalui HTTPS.

## 2. Integrasi SIEM / SOC (Wazuh)

Log audit keamanan dicatat secara terstruktur dalam format satu baris di folder log dengan penanganan karakter pemisah guna mencegah kerentanan log injection. Log ini dihubungkan ke Wazuh Agent menggunakan aturan deteksi di folder `infrastructure/`.
