import logging
import os
import re

import click
from dotenv import load_dotenv
from flask import Flask, render_template, request, g
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from config import Config  # noqa: E402  (dibaca setelah .env dimuat)
from controllers import (auth_controller, admin_controller, produk_controller, toko_controller,  # noqa: E402
                         akun_controller, keranjang_controller, pesanan_controller, admin_pesanan_controller,
                         admin_pengguna_controller, alamat_controller, ulasan_controller,
                         admin_laporan_controller, otp_controller, google_controller)
from forms.auth_form import PASSWORD_POLICY, PASSWORD_POLICY_MESSAGE, NAMA_POLICY  # noqa: E402
from helpers.kata_sandi import buat_kata_sandi_sementara  # noqa: E402
from helpers.email import mail, email_aktif  # noqa: E402
from helpers.katalog_contoh import isi_katalog  # noqa: E402
from helpers.security_logger import init_security_logger, log_event  # noqa: E402
from helpers.waktu import format_tanggal, format_hari  # noqa: E402
from middlewares.auth_middleware import init_auth_middleware  # noqa: E402
from models import db  # noqa: E402
from models.produk import Produk  # noqa: E402,F401  (wajib diimpor agar terbaca oleh migrasi)
from models.keranjang import KeranjangItem  # noqa: E402,F401
from models.pesanan import Pesanan, PesananItem, PesananRiwayat  # noqa: E402,F401
from models.alamat import Alamat  # noqa: E402,F401
from models.ulasan import Ulasan  # noqa: E402,F401
from models.kode_otp import KodeOtp  # noqa: E402,F401
from models.user import User  # noqa: E402

migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY belum diisi. Salin .env.example menjadi .env lalu isi SECRET_KEY.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL belum diisi di file .env.")

    if app.config["TRUST_PROXY"]:
        # Ambil IP asli klien dari header X-Forwarded-For yang dikirim Nginx
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    init_security_logger(app)
    init_auth_middleware(app)
    mail.init_app(app)
    google_controller.init_google(app)

    register_routes(app)
    register_error_handlers(app)
    register_commands(app)

    @app.template_filter("rupiah")
    def rupiah(value):
        #   (spasi tak terputus): "Rp" tidak pernah terpisah dari angkanya saat layar sempit
        return "Rp " + f"{int(value or 0):,}".replace(",", ".")

    @app.template_filter("tanggal")
    def tanggal(value, jam=True):
        return format_tanggal(value, jam)

    @app.template_filter("tanggal_singkat")
    def tanggal_singkat(value):
        return format_hari(value)

    @app.url_defaults
    def versi_file_statis(endpoint, values):
        """Nginx menyimpan file statis di cache browser 7 hari. Menambah ?v=<waktu ubah file> membuat
        URL berganti setiap file diperbarui, jadi pengunjung langsung memakai app.js versi terbaru."""
        if endpoint == "static" and "filename" in values and "v" not in values:
            path = os.path.join(app.static_folder, values["filename"])
            if os.path.isfile(path):
                values["v"] = int(os.path.getmtime(path))

    @app.context_processor
    def inject_globals():
        user = g.get("user")
        data = {"app_name": app.config["APP_NAME"], "current_user": user,
                "cart_count": keranjang_controller.jumlah_item(user), "kategori_nav": Produk.KATEGORI,
                "email_aktif": email_aktif(), "google_aktif": google_controller.google_aktif()}
        if user is not None and user.punya_izin("kelola_pesanan"):
            data["perlu_verifikasi"] = admin_pesanan_controller.jumlah_perlu_verifikasi()
        return data

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if app.config["SESSION_COOKIE_SECURE"]:
            # Hanya saat sudah HTTPS: browser diminta selalu memakai HTTPS selama 1 tahun
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    return app


def register_routes(app):
    # --- TOKO (publik) ---
    @app.route("/")
    def beranda():
        return toko_controller.beranda()

    @app.route("/jelajah")
    def jelajah():
        return toko_controller.jelajah()

    @app.route("/produk/<int:produk_id>")
    def produk_detail(produk_id):
        return toko_controller.detail(produk_id)

    # --- ULASAN (pembeli yang pesanannya sudah selesai) ---
    @app.route("/produk/<int:produk_id>/ulasan", methods=["POST"])
    def ulasan_simpan(produk_id):
        return ulasan_controller.simpan(produk_id)

    @app.route("/produk/<int:produk_id>/ulasan/hapus", methods=["POST"])
    def ulasan_hapus(produk_id):
        return ulasan_controller.hapus_milik_sendiri(produk_id)

    @app.route("/kredit-foto")
    def kredit_foto():
        return toko_controller.kredit_foto()

    # --- AUTENTIKASI ---
    @app.route("/register", methods=["GET", "POST"])
    def register():
        return auth_controller.register()

    @app.route("/login", methods=["GET", "POST"])
    def login():
        return auth_controller.login()

    # --- KODE OTP EMAIL & LUPA KATA SANDI ---
    @app.route("/verifikasi", methods=["GET", "POST"])
    def verifikasi_kode():
        return otp_controller.verifikasi()

    @app.route("/verifikasi/kirim-ulang", methods=["POST"])
    def verifikasi_kirim_ulang():
        return otp_controller.verifikasi_kirim_ulang()

    @app.route("/lupa-password", methods=["GET", "POST"])
    def lupa_password():
        return otp_controller.lupa_password()

    @app.route("/lupa-password/kode", methods=["GET", "POST"])
    def lupa_password_kode():
        return otp_controller.lupa_password_kode()

    @app.route("/lupa-password/kirim-ulang", methods=["POST"])
    def lupa_password_kirim_ulang():
        return otp_controller.lupa_password_kirim_ulang()

    # --- MASUK DENGAN GOOGLE ---
    @app.route("/login/google")
    def login_google():
        return google_controller.login()

    @app.route("/login/google/callback")
    def login_google_callback():
        return google_controller.callback()

    @app.route("/logout", methods=["POST"])
    def logout():
        return auth_controller.logout()

    # --- KERANJANG (wajib login) ---
    @app.route("/keranjang")
    def keranjang():
        return keranjang_controller.index()

    @app.route("/keranjang/tambah/<int:produk_id>", methods=["POST"])
    def keranjang_tambah(produk_id):
        return keranjang_controller.tambah(produk_id)

    @app.route("/keranjang/<int:item_id>/ubah", methods=["POST"])
    def keranjang_ubah(item_id):
        return keranjang_controller.ubah(item_id)

    @app.route("/keranjang/<int:item_id>/hapus", methods=["POST"])
    def keranjang_hapus(item_id):
        return keranjang_controller.hapus(item_id)

    @app.route("/keranjang/kosongkan", methods=["POST"])
    def keranjang_kosongkan():
        return keranjang_controller.kosongkan()

    # --- CHECKOUT & PESANAN (wajib login, hanya pesanan milik sendiri) ---
    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        return pesanan_controller.checkout()

    @app.route("/pesanan")
    def pesanan():
        return pesanan_controller.index()

    @app.route("/pesanan/<kode>")
    def pesanan_detail(kode):
        return pesanan_controller.detail(kode)

    @app.route("/pesanan/<kode>/konfirmasi")
    def pesanan_konfirmasi(kode):
        return pesanan_controller.konfirmasi(kode)

    @app.route("/pesanan/<kode>/bayar", methods=["POST"])
    def pesanan_bayar(kode):
        return pesanan_controller.unggah_bukti(kode)

    @app.route("/pesanan/<kode>/bukti")
    def pesanan_bukti(kode):
        return pesanan_controller.bukti(kode)

    @app.route("/pesanan/<kode>/batal", methods=["POST"])
    def pesanan_batal(kode):
        return pesanan_controller.batal(kode)

    @app.route("/pesanan/<kode>/terima", methods=["POST"])
    def pesanan_terima(kode):
        return pesanan_controller.terima(kode)

    @app.route("/pesanan/<kode>/beli-lagi", methods=["POST"])
    def pesanan_beli_lagi(kode):
        return pesanan_controller.beli_lagi(kode)

    # --- PROFIL & PENGATURAN AKUN (semua user yang login) ---
    @app.route("/profil")
    def profil():
        return akun_controller.profil()

    @app.route("/pengaturan")
    def pengaturan():
        return akun_controller.pengaturan()

    @app.route("/pengaturan/nama", methods=["POST"])
    def pengaturan_nama():
        return akun_controller.ubah_nama()

    @app.route("/pengaturan/email", methods=["POST"])
    def pengaturan_email():
        return akun_controller.ubah_email()

    @app.route("/pengaturan/password", methods=["POST"])
    def pengaturan_password():
        return akun_controller.ubah_password()

    @app.route("/pengaturan/foto", methods=["POST"])
    def pengaturan_foto():
        return akun_controller.ubah_avatar()

    @app.route("/pengaturan/foto/hapus", methods=["POST"])
    def pengaturan_foto_hapus():
        return akun_controller.hapus_avatar()

    # --- ALAMAT TERSIMPAN (pelanggan) ---
    @app.route("/alamat")
    def alamat():
        return alamat_controller.index()

    @app.route("/alamat/tambah", methods=["POST"])
    def alamat_tambah():
        return alamat_controller.tambah()

    @app.route("/alamat/<int:alamat_id>/edit", methods=["GET", "POST"])
    def alamat_edit(alamat_id):
        return alamat_controller.edit(alamat_id)

    @app.route("/alamat/<int:alamat_id>/hapus", methods=["POST"])
    def alamat_hapus(alamat_id):
        return alamat_controller.hapus(alamat_id)

    @app.route("/alamat/<int:alamat_id>/utama", methods=["POST"])
    def alamat_utama(alamat_id):
        return alamat_controller.jadikan_utama(alamat_id)

    # --- ADMIN ---
    @app.route("/admin")
    def admin_dashboard():
        return admin_controller.dashboard()

    @app.route("/admin/produk")
    def admin_produk():
        return produk_controller.index()

    @app.route("/admin/produk/tambah", methods=["GET", "POST"])
    def admin_produk_tambah():
        return produk_controller.create()

    @app.route("/admin/produk/<int:produk_id>/edit", methods=["GET", "POST"])
    def admin_produk_edit(produk_id):
        return produk_controller.edit(produk_id)

    @app.route("/admin/produk/<int:produk_id>/hapus", methods=["POST"])
    def admin_produk_hapus(produk_id):
        return produk_controller.destroy(produk_id)

    @app.route("/admin/pesanan")
    def admin_pesanan():
        return admin_pesanan_controller.index()

    @app.route("/admin/pesanan/<int:pesanan_id>")
    def admin_pesanan_detail(pesanan_id):
        return admin_pesanan_controller.detail(pesanan_id)

    @app.route("/admin/pesanan/<int:pesanan_id>/status", methods=["POST"])
    def admin_pesanan_status(pesanan_id):
        return admin_pesanan_controller.ubah_status(pesanan_id)

    # --- ULASAN: moderasi & balasan toko (izin kelola_produk) ---
    @app.route("/admin/ulasan")
    def admin_ulasan():
        return ulasan_controller.index()

    @app.route("/admin/ulasan/<int:ulasan_id>/balas", methods=["POST"])
    def admin_ulasan_balas(ulasan_id):
        return ulasan_controller.balas(ulasan_id)

    @app.route("/admin/ulasan/<int:ulasan_id>/hapus", methods=["POST"])
    def admin_ulasan_hapus(ulasan_id):
        return ulasan_controller.hapus(ulasan_id)

    # --- LAPORAN TRANSAKSI (izin lihat_laporan, hanya admin) ---
    @app.route("/admin/laporan")
    def admin_laporan():
        return admin_laporan_controller.index()

    @app.route("/admin/laporan/csv")
    def admin_laporan_csv():
        return admin_laporan_controller.ekspor_csv()

    # --- KELOLA PENGGUNA (izin kelola_user, hanya admin) ---
    @app.route("/admin/pengguna")
    def admin_pengguna():
        return admin_pengguna_controller.index()

    @app.route("/admin/pengguna/tambah", methods=["GET", "POST"])
    def admin_pengguna_tambah():
        return admin_pengguna_controller.tambah()

    @app.route("/admin/pengguna/<int:user_id>")
    def admin_pengguna_detail(user_id):
        return admin_pengguna_controller.detail(user_id)

    @app.route("/admin/pengguna/<int:user_id>/aksi", methods=["POST"])
    def admin_pengguna_aksi(user_id):
        return admin_pengguna_controller.aksi(user_id)

    @app.route("/admin/pengguna/<int:user_id>/edit", methods=["POST"])
    def admin_pengguna_edit(user_id):
        return admin_pengguna_controller.edit(user_id)


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        log_event("CSRF_FAILURE", logging.WARNING, path=request.path, reason=error.description)
        return render_template("error.html", code=400,
                               message="Sesi formulir tidak valid atau kedaluwarsa. Muat ulang halaman lalu coba lagi."), 400

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="Halaman tidak ditemukan."), 404

    @app.errorhandler(413)
    def too_large(error):
        log_event("UPLOAD_REJECTED", logging.WARNING, path=request.path, reason="request_too_large")
        return render_template("error.html", code=413, message="Ukuran file terlalu besar (maksimal 2 MB)."), 413

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", code=500, message="Terjadi kesalahan pada server."), 500


def register_commands(app):
    @app.cli.command("seed-admin")
    @click.option("--username", prompt="Username admin")
    @click.option("--nama", prompt="Nama lengkap admin")
    @click.option("--email", prompt="Email admin")
    @click.option("--password", prompt="Kata sandi admin", hide_input=True, confirmation_prompt=True)
    def seed_admin(username, nama, email, password):
        """Membuat akun admin pertama. Perintah: flask seed-admin"""
        email = email.strip().lower()
        if not re.match(PASSWORD_POLICY, password) or len(password) < 8:
            raise click.ClickException(PASSWORD_POLICY_MESSAGE + " Minimal 8 karakter.")
        if User.query.filter((User.email == email) | (User.username == username)).first():
            raise click.ClickException("Username atau email tersebut sudah terdaftar.")

        admin = User(username=username.strip(), nama_lengkap=nama.strip(), email=email, role=User.ROLE_ADMIN)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Akun admin '{admin.username}' berhasil dibuat.")

    @app.cli.command("seed-katalog")
    @click.option("--perbarui-foto", is_flag=True, help="Ganti foto produk contoh yang sudah ada.")
    def seed_katalog(perbarui_foto):
        """Mengisi katalog contoh dari seed/katalog.json. Perintah: flask seed-katalog"""
        try:
            dibuat, diperbarui = isi_katalog(app, perbarui_foto=perbarui_foto)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"{dibuat} produk contoh ditambahkan, {diperbarui} foto diperbarui.")

    @app.cli.command("buat-pengguna")
    @click.option("--nama", required=True, help="Nama lengkap")
    @click.option("--email", required=True)
    @click.option("--peran", required=True, type=click.Choice(list(User.LABEL_ROLE)))
    def buat_pengguna(nama, email, peran):
        """Membuat akun anggota tim dengan kata sandi sementara acak.

        Kata sandi TIDAK dicetak ke layar (agar tidak tersimpan di riwayat terminal/log), tetapi ditulis
        ke instance/akun_baru.txt (hanya bisa dibaca pemilik file). Bagikan lewat pesan pribadi, minta
        pemilik akun langsung menggantinya di Pengaturan, lalu hapus file tersebut.
        Perintah: flask buat-pengguna --nama "Nama" --email nama@contoh.id --peran staf
        """
        email = email.strip().lower()
        nama = " ".join(nama.split())
        if not re.match(NAMA_POLICY, nama) or not 3 <= len(nama) <= 100:
            raise click.ClickException("Nama hanya boleh huruf, spasi, titik, tanda hubung, apostrof (3-100 karakter).")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", email) or len(email) > 100:
            raise click.ClickException("Format email tidak valid.")
        if User.query.filter_by(email=email).first():
            raise click.ClickException(f"Email {email} sudah terdaftar.")

        password = buat_kata_sandi_sementara()
        user = User(username=auth_controller._buat_username(email), nama_lengkap=nama, email=email, role=peran)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        os.makedirs(app.instance_path, exist_ok=True)
        path = os.path.join(app.instance_path, "akun_baru.txt")
        with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a", encoding="utf-8") as f:
            f.write(f"{nama} | {email} | {User.LABEL_ROLE[peran]} | {password}\n")
        log_event("USER_CREATED", logging.WARNING, user_id=user.id, username=user.username, role=peran, by="cli")
        click.echo(f"Akun {email} ({User.LABEL_ROLE[peran]}) dibuat. Kata sandi sementara ada di {path}")

# Tidak ada objek `app` global: perintah `flask run` / `flask db ...` otomatis memanggil create_app().
