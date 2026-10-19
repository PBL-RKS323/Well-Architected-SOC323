"""Kode OTP lewat email: verifikasi email pendaftar baru, OTP login akun panel, dan lupa kata sandi."""
import logging
import time

from flask import render_template, redirect, url_for, flash, session, g

from forms.auth_form import KodeOtpForm, LupaPasswordForm, ResetPasswordForm
from helpers.email import email_aktif, kirim_kode_otp
from helpers.security_logger import log_event
from helpers.sesi import mulai_sesi, halaman_awal, samarkan_email
from models import db
from models.kode_otp import KodeOtp, OtpTerlaluSering
from models.user import User

BATAS_TERTUNDA_DETIK = 15 * 60  # login yang menunggu kode harus selesai dalam 15 menit
PESAN_KODE_SALAH = "Kode salah atau sudah kedaluwarsa."


def _kirim(user, tujuan):
    """Membuat & mengirim kode. Mengembalikan pesan error, atau None jika terkirim."""
    try:
        kode = KodeOtp.buat(user, tujuan)
    except OtpTerlaluSering as e:
        log_event("OTP_THROTTLED", logging.WARNING, user_id=user.id, purpose=tujuan)
        if e.detik >= 3600:
            return "Terlalu banyak permintaan kode. Coba lagi sekitar 1 jam lagi."
        return f"Tunggu {e.detik} detik sebelum meminta kode baru."
    db.session.commit()
    if not kirim_kode_otp(user, kode, KodeOtp.JUDUL[tujuan]):
        return "Email gagal dikirim. Coba lagi beberapa saat lagi."
    log_event("OTP_SENT", user_id=user.id, purpose=tujuan)
    return None


# --- LOGIN TERTUNDA (kata sandi benar, menunggu kode dari email) ---

def mulai_verifikasi(user, tujuan, ingat=False, next_url=None):
    """Sesi login belum dibuat; yang disimpan hanya penanda "menunggu kode" untuk user ini."""
    session.clear()
    session["otp_tertunda"] = {"uid": user.id, "tujuan": tujuan, "ingat": bool(ingat), "next": next_url,
                               "sejak": int(time.time())}
    log_event("LOGIN_PENDING_OTP", user_id=user.id, username=user.username, purpose=tujuan)
    error = _kirim(user, tujuan)
    if error:
        flash(error, "warning")
    else:
        flash(f"Kode 6 digit sudah dikirim ke {samarkan_email(user.email)}. Cek juga folder Spam.", "info")
    return redirect(url_for("verifikasi_kode"))


def _tertunda():
    data = session.get("otp_tertunda")
    if not data or time.time() - data.get("sejak", 0) > BATAS_TERTUNDA_DETIK:
        session.pop("otp_tertunda", None)
        return None, None
    user = db.session.get(User, data["uid"])
    if user is None or not user.aktif:
        session.pop("otp_tertunda", None)
        return None, None
    return data, user


def verifikasi():
    data, user = _tertunda()
    if data is None:
        flash("Waktu verifikasi habis. Silakan masuk lagi.", "warning")
        return redirect(url_for("login"))

    form = KodeOtpForm()
    if form.validate_on_submit():
        hasil = KodeOtp.periksa(user, data["tujuan"], form.kode.data)
        db.session.commit()
        if hasil == KodeOtp.OK:
            if data["tujuan"] == KodeOtp.VERIFIKASI_EMAIL:
                user.email_terverifikasi = True
                log_event("EMAIL_VERIFIED", user_id=user.id, username=user.username)
            db.session.commit()
            mulai_sesi(user, ingat=data["ingat"])
            log_event("SUCCESSFUL_LOGIN", user_id=user.id, username=user.username, role=user.role,
                      remember=int(data["ingat"]), method="password+otp")
            flash(f"Selamat datang, {user.nama_panggilan}!", "success")
            return redirect(halaman_awal(user, data.get("next")))
        if hasil == KodeOtp.HANGUS:
            session.pop("otp_tertunda", None)
            log_event("OTP_LOCKED", logging.WARNING, user_id=user.id, purpose=data["tujuan"])
            flash("Kode salah terlalu banyak. Silakan masuk lagi untuk mendapat kode baru.", "danger")
            return redirect(url_for("login"))
        log_event("OTP_FAILED", logging.WARNING, user_id=user.id, purpose=data["tujuan"], result=hasil)
        form.kode.errors.append(PESAN_KODE_SALAH)
    return render_template("auth/verifikasi.html", form=form, email=samarkan_email(user.email),
                           judul=KodeOtp.JUDUL[data["tujuan"]])


def verifikasi_kirim_ulang():
    data, user = _tertunda()
    if data is None:
        return redirect(url_for("login"))
    error = _kirim(user, data["tujuan"])
    flash(error or f"Kode baru sudah dikirim ke {samarkan_email(user.email)}.", "warning" if error else "info")
    return redirect(url_for("verifikasi_kode"))


# --- LUPA KATA SANDI ---
# Jawaban selalu sama untuk email terdaftar maupun tidak, agar halaman ini tidak bisa dipakai
# untuk menebak email mana yang punya akun (enumerasi akun).

PESAN_UMUM = "Jika email tersebut terdaftar, kode 6 digit sudah dikirim. Cek juga folder Spam/Promosi."


def _user_aktif(email):
    return User.query.filter_by(email=email, aktif=True).first() if email else None


def lupa_password():
    if g.user:
        return redirect(url_for("pengaturan"))
    form = LupaPasswordForm()
    if email_aktif() and form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = _user_aktif(email)
        if user:
            _kirim(user, KodeOtp.RESET_PASSWORD)
        log_event("PASSWORD_RESET_REQUESTED", logging.WARNING, email=email, known=int(user is not None))
        session["reset_email"] = email
        flash(PESAN_UMUM, "info")
        return redirect(url_for("lupa_password_kode"))
    return render_template("auth/lupa_password.html", form=form, aktif=email_aktif())


def lupa_password_kode():
    email = session.get("reset_email")
    if g.user or not email or not email_aktif():
        return redirect(url_for("lupa_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = _user_aktif(email)
        hasil = KodeOtp.periksa(user, KodeOtp.RESET_PASSWORD, form.kode.data) if user else KodeOtp.KEDALUWARSA
        db.session.commit()
        if hasil == KodeOtp.OK:
            # Kata sandi baru membuat sesi lama di perangkat lain otomatis berakhir (sesi_token berubah)
            user.set_password(form.password_baru.data)
            user.reset_failed_login()
            user.email_terverifikasi = True
            db.session.commit()
            session.pop("reset_email", None)
            log_event("PASSWORD_RESET_OTP", logging.WARNING, user_id=user.id, username=user.username)
            flash("Kata sandi berhasil diganti. Silakan masuk dengan kata sandi baru.", "success")
            return redirect(url_for("login"))
        if hasil == KodeOtp.HANGUS:
            log_event("OTP_LOCKED", logging.WARNING, user_id=user.id, purpose=KodeOtp.RESET_PASSWORD)
            flash("Kode salah terlalu banyak. Minta kode baru.", "danger")
            return redirect(url_for("lupa_password"))
        log_event("OTP_FAILED", logging.WARNING, email=email, purpose=KodeOtp.RESET_PASSWORD, result=hasil)
        form.kode.errors.append(PESAN_KODE_SALAH)
    return render_template("auth/reset_password.html", form=form, email=samarkan_email(email))


def lupa_password_kirim_ulang():
    email = session.get("reset_email")
    if not email or not email_aktif():
        return redirect(url_for("lupa_password"))
    user = _user_aktif(email)
    if user:
        _kirim(user, KodeOtp.RESET_PASSWORD)
    flash(PESAN_UMUM, "info")
    return redirect(url_for("lupa_password_kode"))
