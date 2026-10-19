import logging
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
                         akun_controller, keranjang_controller, pesanan_controller, admin_pesanan_controller)
from forms.auth_form import PASSWORD_POLICY, PASSWORD_POLICY_MESSAGE  # noqa: E402
from helpers.katalog_contoh import isi_katalog  # noqa: E402
from helpers.security_logger import init_security_logger, log_event  # noqa: E402
from helpers.waktu import format_tanggal  # noqa: E402
from middlewares.auth_middleware import init_auth_middleware  # noqa: E402
from models import db  # noqa: E402
from models.produk import Produk  # noqa: E402,F401  (wajib diimpor agar terbaca oleh migrasi)
from models.keranjang import KeranjangItem  # noqa: E402,F401
from models.pesanan import Pesanan, PesananItem, PesananRiwayat  # noqa: E402,F401
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

    register_routes(app)
    register_error_handlers(app)
    register_commands(app)

    @app.template_filter("rupiah")
    def rupiah(value):
        return "Rp " + f"{int(value or 0):,}".replace(",", ".")

    @app.template_filter("tanggal")
    def tanggal(value, jam=True):
        return format_tanggal(value, jam)

    @app.context_processor
    def inject_globals():
        user = g.get("user")
        data = {"app_name": app.config["APP_NAME"], "current_user": user,
                "cart_count": keranjang_controller.jumlah_item(user)}
        if user is not None and user.is_admin():
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
    @click.option("--nama", prompt="Nama tampilan admin", default="Admin Toko")
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
    def seed_katalog():
        """Mengisi katalog contoh dari seed/katalog.json. Perintah: flask seed-katalog"""
        try:
            dibuat = isi_katalog(app)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"{dibuat} produk contoh ditambahkan.")

# Tidak ada objek `app` global: perintah `flask run` / `flask db ...` otomatis memanggil create_app().
