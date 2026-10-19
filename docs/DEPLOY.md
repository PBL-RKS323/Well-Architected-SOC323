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
Karena `SESSION_COOKIE_SECURE=1`, login baru berfungsi setelah HTTPS aktif.

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
