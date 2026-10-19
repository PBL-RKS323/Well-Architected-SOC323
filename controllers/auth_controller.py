import logging
import re
import secrets

from flask import render_template, redirect, url_for, flash, session, request, current_app, g

from forms.auth_form import RegisterForm, LoginForm
from helpers.security_logger import log_event
from models import db
from models.user import User


def _safe_next_url(target):
    """Hanya izinkan redirect ke path internal (mencegah open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return None


def mulai_sesi(user, ingat):
    """Sesi baru setelah login / ganti kata sandi. Sesi lama dibuang (anti session fixation).

    `ingat` True: sesi bertahan 7 hari ("Ingat saya"). False: berakhir saat browser ditutup.
    """
    session.clear()
    session["user_id"] = user.id
    session["sesi_token"] = user.sesi_token
    session.permanent = ingat


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
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        log_event("REGISTER_SUCCESS", user_id=new_user.id, username=new_user.username)
        flash("Pendaftaran berhasil! Silakan login.", "success")
        return redirect(url_for("login"))
    return render_template("auth/register.html", form=form)


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

            mulai_sesi(user, ingat=bool(form.ingat_saya.data))

            log_event("SUCCESSFUL_LOGIN", user_id=user.id, username=user.username, role=user.role,
                      remember=int(session.permanent))
            flash(f"Selamat datang, {user.display_name}!", "success")

            next_url = _safe_next_url(request.args.get("next"))
            if user.is_staf_toko():
                return redirect(next_url or url_for("admin_dashboard"))
            return redirect(next_url or url_for("beranda"))

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
