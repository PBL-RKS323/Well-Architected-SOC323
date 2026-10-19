import logging
from functools import wraps

from flask import request, session, redirect, url_for, flash, g

from helpers.security_logger import log_event
from models import db
from models.user import User

# Endpoint yang boleh diakses tanpa login. Endpoint lain otomatis wajib login (default deny).
PUBLIC_ENDPOINTS = {"static", "beranda", "jelajah", "produk_detail", "kredit_foto", "login", "register",
                    "verifikasi_kode", "verifikasi_kirim_ulang", "lupa_password", "lupa_password_kode",
                    "lupa_password_kirim_ulang", "login_google", "login_google_callback"}


def _muat_user():
    """Ambil user dari sesi. Sesi ditolak jika akun dihapus, dinonaktifkan, atau kata sandinya diganti."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is not None and user.aktif and session.get("sesi_token") == user.sesi_token:
        return user
    if user is not None:
        alasan = "account_disabled" if not user.aktif else "password_changed"
        log_event("SESSION_INVALIDATED", logging.WARNING, user_id=user.id, username=user.username, reason=alasan)
        flash("Akun ini dinonaktifkan. Hubungi admin toko." if not user.aktif
              else "Sesi berakhir karena kata sandi akun diganti. Silakan login lagi.", "warning")
    session.clear()
    return None


def _tolak(izin=None):
    log_event("ACCESS_DENIED", logging.WARNING, user_id=g.user.id, username=g.user.username,
              role=g.user.role, path=request.path, **({"permission": izin} if izin else {}))
    flash("Akses ditolak! Kamu tidak punya izin untuk halaman ini.", "danger")
    return redirect(url_for("admin_dashboard" if g.user.is_staf_toko() else "beranda"))


def init_auth_middleware(app):
    @app.before_request
    def load_user_and_check_access():
        g.user = _muat_user()

        # 1. Rute statis dan 404 dibebaskan
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return None

        # 2. Autentikasi global
        if g.user is None:
            flash("Silakan login terlebih dahulu untuk mengakses halaman ini.", "warning")
            # next hanya untuk GET (URL aksi POST tidak bisa dibuka ulang setelah login)
            return redirect(url_for("login", next=request.path if request.method == "GET" else None))

        # 3. Otorisasi area panel: peran dibaca dari database setiap request, bukan dari sesi.
        #    Izin rinci (kelola_produk, kelola_user, ...) dicek lagi oleh izin_required di controller.
        if request.path.startswith("/admin"):
            if not g.user.punya_izin("panel"):
                return _tolak("panel")
            log_event("ADMIN_ACCESS", user_id=g.user.id, username=g.user.username, role=g.user.role,
                      method=request.method, path=request.path)
        return None


def izin_required(izin):
    """RBAC di level controller (lapisan kedua setelah middleware). Contoh: @izin_required("kelola_user")"""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.get("user") is None:
                return redirect(url_for("login"))
            if not g.user.punya_izin(izin):
                return _tolak(izin)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def pelanggan_required(view):
    """Keranjang, checkout, pesanan, dan alamat khusus peran yang punya izin "belanja". Admin & staf
    tidak berbelanja agar tidak bisa membuat pesanan lalu menyetujui bukti bayarnya sendiri."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is not None and not g.user.punya_izin("belanja"):
            flash("Akun admin/staf tidak bisa berbelanja. Gunakan akun pelanggan untuk mencoba alur belanja.",
                  "warning")
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)
    return wrapped
