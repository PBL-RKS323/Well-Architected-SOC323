# Laporan Audit Keamanan & Hardening Aplikasi (SOC 323)
Disusun oleh: **Ihsan Alfareno** (Fitur Tambahan & Keamanan Siber / SOC)
Proyek: PBL Rekayasa Keamanan Siber (RKS 323), Politeknik Negeri Batam

---

## 1. Hasil Audit Keamanan Menyeluruh (Deep Full Scan)

### A. Static Application Security Testing (SAST - Bandit)
- **Tool**: `Bandit v1.8.3`
- **Total Baris Kode**: 3.944 baris kode Python
- **Hasil**: **0 High Severity, 0 Medium Severity**.
- **Remediasi yang Diterapkan**:
  - Penghapusan host binding publik `0.0.0.0` pada modul dev runner (`HOST` default `127.0.0.1`).
  - Pencegahan eksekusi debug mode saat rilis produksi (`FLASK_DEBUG=0`).
  - Penanganan exception log keamanan secara spesifik `(OSError, UnicodeDecodeError, ValueError)` guna mencegah silent failure.

### B. Dynamic Application Security Testing (DAST - test_dast_audit.py)
Pengujian otomatis terhadap vektor serangan OWASP Top 10 pada runtime aplikasi:
- **SQL Injection**: Lolos pengujian fuzzer pada endpoint pencarian, filter, dan pagination (`' OR 1=1`, `UNION SELECT`). Parameter binding SQLAlchemy ORM aktif penuh.
- **Cross-Site Scripting (Reflected XSS)**: Lolos pengujian payload `<script>`, `<img onerror>`, dan `<svg/onload>` via context-aware auto-escaping Jinja2.
- **CSRF Token Enforcement**: Pengujian POST tanpa token menghasilkan HTTP 400 Bad Request; logout via GET ditolak (HTTP 405).
- **IDOR & RBAC**: Verifikasi pencegahan eskalasi hak akses pelanggan ke panel admin serta isolasi mutlak data alamat dan pesanan antar-pengguna.
- **Brute-Force Lockout**: Akun pengguna terkunci otomatis setelah 5 kali gagal autentikasi berturut-turut.
- **HTTP Security Headers**: Header `X-Content-Type-Options: nosniff` dan `X-Frame-Options: DENY` terverifikasi aktif pada seluruh respon HTTP.

### C. Software Composition Analysis (SCA / Dependency Audit)
- **Tool**: `pip-audit v2.8.0`
- **Temuan Awal**: 41 CVE pada paket `pillow 12.3.0` dan advisory pada `pip 26.1.2`.
- **Tindakan**: Upgrade menyeluruh ke **Pillow 13.0.0** dan **pip 26.3**.
- **Hasil**: **0 known vulnerabilities found** (100% Bersih).

---

## 2. Arsitektur Monitoring SIEM / SOC (Wazuh)

Aplikasi terhubung ke **Wazuh Agent** melalui berkas log audit terstruktur `logs/security.log`. Aturan korelasi lokal disesuaikan di `infrastructure/wazuh_ecommerce_rules.xml`:

1. **Rule 100201 (Level 5)**: Percobaan login gagal (`FAILED_LOGIN`).
2. **Rule 100202 (Level 10)**: Korelasi threshold brute-force login (5 kegagalan dalam rentang 60 detik dari IP yang sama, pemetaan MITRE ATT&CK T1110).
3. **Rule 100203 (Level 8)**: Upaya request dengan CSRF token tidak valid (`CSRF_FAILURE`, MITRE ATT&CK T1557).
4. **Rule 100204 (Level 7)**: Upaya upload berkas berbahaya / manipulasi magic byte (`UPLOAD_REJECTED`).
5. **Rule 100205 (Level 6)**: Upaya brute-force / enumerasi kode kupon promo (`COUPON_ABUSE`).
6. **Rule 100206 (Level 9)**: Upaya pelanggaran isolasi IDOR / privilege escalation antar-pengguna (`IDOR_ATTEMPT`).
