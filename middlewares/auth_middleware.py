import logging
from functools import wraps

from flask import request, session, redirect, url_for, flash, g

from helpers.security_logger import log_event
from models import db
from models.user import User

# Endpoint yang boleh diakses tanpa login. Endpoint lain otomatis wajib login (default deny).
PUBLIC_ENDPOINTS = {"static", "beranda", "jelajah", "produk_detail", "kredit_foto", "login", "register"}


def init_auth_middleware(app):
    @app.before_request
    def load_user_and_check_access():
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            user = db.session.get(User, user_id)
            if user is not None and session.get("sesi_token") == user.sesi_token:
                g.user = user
            else:
                # Akun sudah dihapus, atau kata sandinya sudah diganti di perangkat lain
                if user is not None:
                    log_event("SESSION_INVALIDATED", logging.WARNING, user_id=user.id, username=user.username,
                              reason="password_changed")
                    flash("Sesi berakhir karena kata sandi akun diganti. Silakan login lagi.", "warning")
                session.clear()

        # 1. Rute statis dan 404 dibebaskan
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return None

        # 2. Autentikasi global
        if g.user is None:
            flash("Silakan login terlebih dahulu untuk mengakses halaman ini.", "warning")
            # next hanya untuk GET (URL aksi POST tidak bisa dibuka ulang setelah login)
            return redirect(url_for("login", next=request.path if request.method == "GET" else None))

        # 3. Otorisasi area admin: role dibaca dari database, bukan dari sesi
        if request.path.startswith("/admin"):
            if not g.user.is_admin():
                log_event("ACCESS_DENIED", logging.WARNING, user_id=g.user.id,
                          username=g.user.username, role=g.user.role, path=request.path)
                flash("Akses ditolak! Halaman ini khusus untuk Admin.", "danger")
                return redirect(url_for("beranda"))
            log_event("ADMIN_ACCESS", user_id=g.user.id, username=g.user.username,
                      method=request.method, path=request.path)
        return None


def admin_required(view):
    """Lapisan kedua di level controller (pendekatan hybrid: middleware + decorator)."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None or not g.user.is_admin():
            flash("Akses ditolak! Halaman ini khusus untuk Admin.", "danger")
            return redirect(url_for("beranda"))
        return view(*args, **kwargs)
    return wrapped


def pelanggan_required(view):
    """Keranjang & pesanan khusus pelanggan. Admin tidak boleh berbelanja agar tidak bisa membuat
    pesanan lalu menyetujui bukti bayarnya sendiri (pemisahan tugas)."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is not None and g.user.is_admin():
            flash("Akun admin tidak bisa berbelanja. Gunakan akun pelanggan untuk mencoba alur belanja.", "warning")
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)
    return wrapped
