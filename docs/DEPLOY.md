# Deploy ke Server (OCI)

Server: VM Oracle Cloud `VM.Standard.A1.Flex` (ARM, 2 OCPU, 12 GB), Ubuntu 24.04, region Batam.
Server ini juga menjalankan aplikasi lain (neteye, leviathan, showtime), jadi semua langkah di bawah
hanya menambah konfigurasi baru dan tidak mengubah yang sudah ada.

| Bagian | Lokasi / nilai |
|---|---|
| Alamat | `https://toko.neteye.my.id` (record DNS A ke IP server, diatur di DomaiNesia) |
| Kode | `/opt/elektronik-store` (repo git) |
| Rahasia | `/opt/elektronik-store/.env` (chmod 600, dibuat acak di server, tidak ada di repo) |
| Database | PostgreSQL 16 lokal, hanya `localhost`, role `ecommerce_user` (bukan superuser) |
| Aplikasi | Gunicorn `127.0.0.1:8100`, service systemd `elektronik-store` |
| Web server | Nginx, `/etc/nginx/sites-available/elektronik-store` (salinan `deploy/nginx-elektronik-store.conf`) |
| Log keamanan | `/opt/elektronik-store/logs/security.log` (untuk Wazuh agent) |
| Bukti bayar | `/opt/elektronik-store/instance/bukti_bayar/` (tidak dilayani Nginx) |

## Pengaturan `.env` produksi

Selain `SECRET_KEY` dan `DATABASE_URL`: `TRUST_PROXY=1` (IP asli dari Nginx), `SESSION_COOKIE_SECURE=1`
(cookie hanya lewat HTTPS), `DEMO_MODE=1` (pemberitahuan toko demo di semua halaman).

## Memperbarui aplikasi

Repo belum di GitHub, jadi kode dikirim sebagai git bundle lewat SSH:

```bash
git bundle create toko.bundle main
scp -i D:\oci.key toko.bundle ubuntu@168.110.216.98:/tmp/toko.bundle
ssh -i D:\oci.key ubuntu@168.110.216.98
cd /opt/elektronik-store
git pull /tmp/toko.bundle main
.venv/bin/pip install -r requirements.txt
.venv/bin/flask db upgrade
sudo systemctl restart elektronik-store
```

Setelah repo ada di GitHub, `git pull` bisa langsung dari remote.

## HTTPS

Setelah `toko.neteye.my.id` mengarah ke IP server:

```bash
sudo certbot --nginx -d toko.neteye.my.id --redirect
```

Certbot menambah blok `listen 443` ke config Nginx dan memperpanjang sertifikat otomatis.
Karena `SESSION_COOKIE_SECURE=1`, login baru berfungsi setelah HTTPS aktif. Pengaturan yang sama
membuat aplikasi mengirim header HSTS (`Strict-Transport-Security: max-age=31536000`).
Status 19 Okt 2026: sertifikat Let's Encrypt untuk `toko.neteye.my.id` sudah terpasang, HTTP dialihkan
ke HTTPS.

## Akun admin pertama

Dibuat dengan password acak. Kredensial ada di `/opt/elektronik-store/instance/ADMIN_AWAL.txt`
(chmod 600). Setelah login, ganti password di Pengaturan lalu hapus file itu.

## Perintah berguna

```bash
sudo systemctl status elektronik-store      # status aplikasi
sudo journalctl -u elektronik-store -n 50   # log Gunicorn
tail -f /opt/elektronik-store/logs/security.log
sudo nginx -t && sudo systemctl reload nginx
```

## Akun anggota tim

Setiap anggota memakai akunnya sendiri (log mencatat siapa melakukan apa). Buat lewat panel
**Pengguna → Tambah Pengguna**, atau dari server:

```bash
cd /opt/elektronik-store
.venv/bin/flask buat-pengguna --nama "Nama Lengkap" --email nama@neteye.my.id --peran staf   # admin / staf / customer
cat instance/akun_baru.txt   # kata sandi sementara (file chmod 600)
rm instance/akun_baru.txt    # hapus setelah dibagikan lewat pesan pribadi
```

Selama email (Gmail SMTP) belum diisi di `.env`, alamat email cukup berformat benar. Setelah email aktif,
pakai email asli: kode lupa kata sandi dan OTP login dikirim ke alamat itu.
Pemilik akun wajib mengganti kata sandi sementara di **Pengaturan** setelah login pertama.

## Login Google & kode OTP lewat Gmail

Kedua fitur mati selama `.env` belum diisi; isi lalu `sudo systemctl restart elektronik-store`.
Edit `.env` di server dengan `nano /opt/elektronik-store/.env` (izin file tetap 600). Jangan kirim isi
`.env` lewat chat/grup.

### 1. Gmail pengirim kode OTP

1. Buat Gmail khusus toko (mis. `elektronikstore.pbl@gmail.com`), jangan Gmail pribadi.
2. Akun Google tersebut: **Keamanan > Verifikasi 2 Langkah** diaktifkan.
3. Buka <https://myaccount.google.com/apppasswords>, buat App Password bernama `Elektronik Store`.
   Google menampilkan 16 huruf sekali saja.
4. Isi `.env`:
   ```
   MAIL_USERNAME=elektronikstore.pbl@gmail.com
   MAIL_PASSWORD=abcdefghijklmnop   # 16 huruf App Password, tanpa spasi
   ```
5. Uji: halaman **Masuk > Lupa kata sandi?** dengan email akun yang asli. Batas Gmail sekitar 500 email/hari.

Yang aktif setelah email diisi:
- **Lupa kata sandi**: kode 6 digit ke email, berlaku 10 menit, hangus setelah 5x salah, kirim ulang tiap 60 detik
  (maks. 5 kode/jam). Halaman selalu menjawab sama untuk email terdaftar/tidak (anti enumerasi akun).
- **Verifikasi email** untuk pendaftar baru: akun baru harus memasukkan kode sebelum bisa masuk.
- **OTP login Admin/Staf** (opsional): isi `OTP_LOGIN_PANEL=1` setelah semua akun panel memakai email asli.
  Jika email gagal dikirim, admin tidak bisa masuk; kembalikan ke `0` untuk sementara.

### 2. Login dengan Google

1. Buka <https://console.cloud.google.com>, buat project `Elektronik Store PBL`.
2. **Google Auth Platform > Branding**: nama aplikasi, email dukungan, domain resmi `neteye.my.id`.
3. **Audience**: External. Selama status *Testing*, hanya Gmail yang ditambahkan di *Test users* yang bisa masuk
   (tambahkan Gmail anggota tim). Scope yang dipakai hanya `openid email profile` (tidak perlu verifikasi Google).
4. **Clients > Create client > Web application**. *Authorized redirect URIs*:
   - `https://toko.neteye.my.id/login/google/callback`
   - `http://localhost:5000/login/google/callback` (untuk uji di laptop)
5. Salin Client ID & Client secret ke `.env`:
   ```
   GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxx
   ```
6. Restart. Tombol **Masuk dengan Google** muncul di halaman Masuk dan Daftar.

Aturan login Google:
- Email Google baru -> otomatis dibuat akun **Pelanggan** (email sudah terverifikasi oleh Google).
- Email sama dengan akun Pelanggan yang sudah ada -> akun tersebut disambungkan ke Google.
- Akun **Admin/Staf tidak bisa** masuk lewat Google (tetap email + kata sandi, dan OTP jika dinyalakan),
  agar pemilik Gmail lain tidak bisa ikut masuk ke panel bila email akun panel salah ketik.
