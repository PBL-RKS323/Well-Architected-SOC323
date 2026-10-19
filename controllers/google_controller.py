"""Masuk / daftar dengan akun Google (OAuth 2.0 + OpenID Connect lewat Authlib)."""
import logging
import re
import secrets

import requests
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import redirect, url_for, flash, session, request, current_app, abort, g

from controllers.auth_controller import _buat_username
from forms.auth_form import NAMA_POLICY
from helpers.security_logger import log_event
from helpers.sesi import mulai_sesi, safe_next_url, halaman_awal
from models import db
from models.user import User

oauth = OAuth()


def init_google(app):
    oauth.init_app(app)
    if app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            "google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


def google_aktif():
    return bool(current_app.config.get("GOOGLE_CLIENT_ID") and current_app.config.get("GOOGLE_CLIENT_SECRET"))


def _nama_dari_google(info, email):
    """Nama Google bisa berisi angka/emoji; disaring agar sesuai aturan nama di aplikasi."""
    nama = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ' .-]", "", info.get("name") or "")
    nama = " ".join(nama.split())[:100]
    if len(nama) < 3 or not re.match(NAMA_POLICY, nama):
        nama = "Pengguna Google"
    return nama


def _gagal(alasan, pesan="Masuk dengan Google gagal. Coba lagi atau masuk dengan email."):
    log_event("GOOGLE_LOGIN_FAILED", logging.WARNING, reason=alasan)
    flash(pesan, "danger")
    return redirect(url_for("login"))


def login():
    if not google_aktif():
        abort(404)
    if g.user:
        return redirect(halaman_awal(g.user))
    session["google_next"] = safe_next_url(request.args.get("next"))
    return oauth.google.authorize_redirect(url_for("login_google_callback", _external=True))


def callback():
    if not google_aktif():
        abort(404)
    try:
        token = oauth.google.authorize_access_token()  # cek state (anti CSRF) + tukar kode + validasi ID token
    except OAuthError as e:
        return _gagal(e.error or "oauth_error", "Masuk dengan Google dibatalkan atau gagal.")
    except requests.RequestException:
        return _gagal("network_error")

    info = token.get("userinfo") or {}
    sub, email = info.get("sub"), (info.get("email") or "").strip().lower()
    if not sub or not email or not info.get("email_verified"):
        return _gagal("email_not_verified", "Email akun Google belum terverifikasi.")

    user = User.query.filter_by(google_sub=sub).first()
    if user is None:
        user = User.query.filter_by(email=email).first()
        if user is not None:
            if user.google_sub and user.google_sub != sub:
                return _gagal("google_account_mismatch")
            if user.is_staf_toko():
                # Akun panel tidak disambungkan otomatis lewat kesamaan email: jika email akun admin pernah
                # salah ketik / milik orang lain, pemilik Gmail itu bisa ikut masuk sebagai admin.
                log_event("GOOGLE_LOGIN_FAILED", logging.WARNING, reason="panel_account", user_id=user.id)
                flash("Akun Admin/Staf masuk dengan email dan kata sandi.", "warning")
                return redirect(url_for("login"))
            user.google_sub = sub

    if user is None:
        user = User(username=_buat_username(email), nama_lengkap=_nama_dari_google(info, email), email=email,
                    role=User.ROLE_CUSTOMER, google_sub=sub)
        # Kata sandi acak yang tidak diketahui siapa pun; jika ingin masuk dengan email + kata sandi,
        # pengguna memakai "Lupa kata sandi" untuk membuatnya.
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
        db.session.flush()
        log_event("REGISTER_SUCCESS", user_id=user.id, username=user.username, method="google")

    if not user.aktif:
        db.session.rollback()
        log_event("LOGIN_BLOCKED", logging.WARNING, user_id=user.id, reason="account_disabled", method="google")
        flash("Akun ini dinonaktifkan. Hubungi admin toko.", "danger")
        return redirect(url_for("login"))

    user.email_terverifikasi = True
    user.reset_failed_login()
    db.session.commit()

    next_url = session.get("google_next")
    mulai_sesi(user, ingat=False)
    log_event("SUCCESSFUL_LOGIN", user_id=user.id, username=user.username, role=user.role, method="google")
    flash(f"Selamat datang, {user.nama_panggilan}!", "success")
    return redirect(halaman_awal(user, next_url))
