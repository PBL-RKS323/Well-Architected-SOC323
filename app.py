import logging
import os
import re

import click
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, request, g
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from config import Config  # noqa: E402  (dibaca setelah .env dimuat)
from controllers import auth_controller, keranjang_controller, admin_pesanan_controller, google_controller  # noqa: E402
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
from models.kategori import Kategori  # noqa: E402,F401
from models.favorit import Favorit  # noqa: E402,F401
from models.kupon import Kupon  # noqa: E402,F401
from models.pembayaran import Pembayaran  # noqa: E402,F401
from routes import register_blueprints  # noqa: E402

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

    register_blueprints(app)  # route per area ada di folder routes/ (toko, auth, belanja, akun, admin)
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
        fav_count = user.daftar_favorit.count() if user and user.punya_izin("belanja") else 0
        kat_list = [k.nama for k in Kategori.query.filter_by(aktif=True).order_by(Kategori.urutan).all()] or Produk.KATEGORI
        data = {"app_name": app.config["APP_NAME"], "current_user": user,
                "cart_count": keranjang_controller.jumlah_item(user), "favorit_count": fav_count, "kategori_nav": kat_list,
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


def _email_cli(email):
    """Email dari perintah CLI dicek dengan validator yang sama dengan form login, agar tidak terbentuk
    akun yang emailnya ditolak saat login (mis. domain khusus seperti .test atau .local)."""
    email = email.strip().lower()
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        raise click.ClickException(f"Format email tidak valid: {e}")
    if len(email) > 100:
        raise click.ClickException("Email maksimal 100 karakter.")
    return email


def register_commands(app):
    @app.cli.command("seed-admin")
    @click.option("--username", prompt="Username admin")
    @click.option("--nama", prompt="Nama lengkap admin")
    @click.option("--email", prompt="Email admin")
    @click.option("--password", prompt="Kata sandi admin", hide_input=True, confirmation_prompt=True)
    def seed_admin(username, nama, email, password):
        """Membuat akun admin pertama. Perintah: flask seed-admin"""
        email = _email_cli(email)
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
            dibuat, diperbarui, dilengkapi = isi_katalog(app, perbarui_foto=perbarui_foto)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"{dibuat} produk contoh ditambahkan, {diperbarui} foto diperbarui, "
                   f"{dilengkapi} produk dilengkapi spesifikasinya.")

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
        email = _email_cli(email)
        nama = " ".join(nama.split())
        if not re.match(NAMA_POLICY, nama) or not 3 <= len(nama) <= 100:
            raise click.ClickException("Nama hanya boleh huruf, spasi, titik, tanda hubung, apostrof (3-100 karakter).")
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
