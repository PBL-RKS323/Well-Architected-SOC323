import logging
import re
import secrets

from flask import render_template, redirect, url_for, flash, session, request, current_app, g

from controllers.otp_controller import mulai_verifikasi
from forms.auth_form import RegisterForm, LoginForm
from helpers.email import email_aktif
from helpers.security_logger import log_event
from helpers.sesi import mulai_sesi, safe_next_url as _safe_next_url, halaman_awal  # noqa: F401
from models import db
from models.kode_otp import KodeOtp
from models.user import User


def _buat_username(email):
    """Username internal dibuat otomatis dari email (tidak perlu diisi pengguna)."""
    dasar = re.sub(r"[^a-z0-9_.]", "", email.split("@")[0].lower())[:40] or "user"
    username = dasar
    while User.query.filter_by(username=username).first():
        username = f"{dasar}{secrets.randbelow(9000) + 1000}"
    return username


def register():
    if g.user:
        return redirect(url_for("beranda"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        new_user = User(
            username=_buat_username(email),
            nama_lengkap=" ".join(form.nama_lengkap.data.split()),
            email=email,
            role=User.ROLE_CUSTOMER,
            # Jika email aktif, akun baru harus membuktikan email-nya miliknya lewat kode OTP
            email_terverifikasi=not email_aktif(),
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        log_event("REGISTER_SUCCESS", user_id=new_user.id, username=new_user.username)
        if not new_user.email_terverifikasi:
            return mulai_verifikasi(new_user, KodeOtp.VERIFIKASI_EMAIL)
        flash("Pendaftaran berhasil! Silakan login.", "success")
        return redirect(url_for("login"))
    return render_template("auth/register.html", form=form)


def _perlu_otp(user):
    """Langkah kode email setelah kata sandi benar: verifikasi email (pendaftar baru) atau OTP login
    untuk akun panel (jika OTP_LOGIN_PANEL=1). None = langsung masuk. Tanpa email aktif selalu None."""
    if not email_aktif():
        return None
    if not user.email_terverifikasi:
        return KodeOtp.VERIFIKASI_EMAIL
    if current_app.config["OTP_LOGIN_PANEL"] and user.is_staf_toko():
        return KodeOtp.LOGIN
    return None


def login():
    if g.user:
        return redirect(url_for("admin_dashboard" if g.user.is_staf_toko() else "beranda"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.is_locked():
            log_event("LOGIN_BLOCKED", logging.WARNING, email=email, user_id=user.id, reason="account_locked")
            flash("Akun dikunci sementara karena terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.",
                  "danger")
            return render_template("auth/login.html", form=form)

        if user and user.check_password(form.password.data):
            # Pesan khusus hanya setelah kata sandi benar, agar tidak membocorkan status akun ke orang lain
            if not user.aktif:
                log_event("LOGIN_BLOCKED", logging.WARNING, email=email, user_id=user.id, reason="account_disabled")
                flash("Akun ini dinonaktifkan. Hubungi admin toko.", "danger")
                return render_template("auth/login.html", form=form)

            user.reset_failed_login()
            db.session.commit()

            next_url = _safe_next_url(request.args.get("next"))
            tujuan_otp = _perlu_otp(user)
            if tujuan_otp:
                return mulai_verifikasi(user, tujuan_otp, ingat=bool(form.ingat_saya.data), next_url=next_url)

            mulai_sesi(user, ingat=bool(form.ingat_saya.data))

            log_event("SUCCESSFUL_LOGIN", user_id=user.id, username=user.username, role=user.role,
                      remember=int(session.permanent))
            flash(f"Selamat datang, {user.nama_panggilan}!", "success")
            return redirect(halaman_awal(user, next_url))

        # Gagal login: pesan dibuat sama agar penyerang tidak tahu email mana yang terdaftar
        if user:
            just_locked = user.register_failed_login(current_app.config["MAX_LOGIN_ATTEMPTS"],
                                                     current_app.config["LOCKOUT_MINUTES"])
            db.session.commit()
            log_event("FAILED_LOGIN", logging.WARNING, email=email, reason="invalid_password")
            if just_locked:
                log_event("ACCOUNT_LOCKED", logging.WARNING, user_id=user.id, username=user.username,
                          minutes=current_app.config["LOCKOUT_MINUTES"])
        else:
            User.check_dummy_password(form.password.data)
            log_event("FAILED_LOGIN", logging.WARNING, email=email, reason="unknown_email")

        flash("Email atau kata sandi salah!", "danger")
    return render_template("auth/login.html", form=form)


def logout():
    if g.user:
        log_event("LOGOUT", user_id=g.user.id, username=g.user.username)
    session.clear()
    flash("Anda telah berhasil keluar.", "info")
    return redirect(url_for("login"))
