import logging

from flask import render_template, redirect, url_for, flash, session, g

from controllers.auth_controller import mulai_sesi
from forms.akun_form import UbahNamaForm, UbahEmailForm, UbahPasswordForm
from helpers.security_logger import log_event
from models import db
from models.pesanan import Pesanan


def _render(nama_form=None, email_form=None, password_form=None):
    return render_template(
        "akun/pengaturan.html",
        nama_form=nama_form or UbahNamaForm(prefix="nama", formdata=None, nama_lengkap=g.user.nama_lengkap),
        email_form=email_form or UbahEmailForm(prefix="email", formdata=None),
        password_form=password_form or UbahPasswordForm(prefix="pw", formdata=None),
    )


def profil():
    pesanan_terbaru, ringkasan = [], {}
    if g.user.punya_izin("belanja"):
        milik = Pesanan.query.filter_by(user_id=g.user.id)
        pesanan_terbaru = milik.order_by(Pesanan.created_at.desc()).limit(3).all()
        ringkasan = {
            "aktif": milik.filter(Pesanan.status.in_(Pesanan.STATUS_AKTIF)).count(),
            "selesai": milik.filter_by(status=Pesanan.SELESAI).count(),
        }
    return render_template("akun/profil.html", pesanan_terbaru=pesanan_terbaru, ringkasan=ringkasan)


def pengaturan():
    return _render()


def ubah_nama():
    form = UbahNamaForm(prefix="nama")
    if form.validate_on_submit():
        g.user.nama_lengkap = " ".join(form.nama_lengkap.data.split())
        db.session.commit()
        flash("Nama berhasil diperbarui.", "success")
        return redirect(url_for("pengaturan"))
    return _render(nama_form=form)


def ubah_email():
    form = UbahEmailForm(prefix="email")
    if form.validate_on_submit():
        if not g.user.check_password(form.password_sekarang.data):
            log_event("CREDENTIAL_CHANGE_FAILED", logging.WARNING, user_id=g.user.id,
                      target="email", reason="wrong_current_password")
            form.password_sekarang.errors.append("Kata sandi saat ini salah.")
            return _render(email_form=form)

        g.user.email = form.email_baru.data.strip().lower()
        db.session.commit()
        log_event("EMAIL_CHANGED", logging.WARNING, user_id=g.user.id, username=g.user.username)
        flash("Email berhasil diperbarui.", "success")
        return redirect(url_for("pengaturan"))
    return _render(email_form=form)


def ubah_password():
    form = UbahPasswordForm(prefix="pw")
    if form.validate_on_submit():
        if not g.user.check_password(form.password_sekarang.data):
            log_event("CREDENTIAL_CHANGE_FAILED", logging.WARNING, user_id=g.user.id,
                      target="password", reason="wrong_current_password")
            form.password_sekarang.errors.append("Kata sandi saat ini salah.")
            return _render(password_form=form)
        if g.user.check_password(form.password_baru.data):
            form.password_baru.errors.append("Kata sandi baru tidak boleh sama dengan kata sandi lama.")
            return _render(password_form=form)

        g.user.set_password(form.password_baru.data)
        db.session.commit()

        # Sesi perangkat ini diperbarui dengan pilihan "Ingat saya" yang sama. Sesi di perangkat lain
        # otomatis tidak berlaku karena sesi_token ikut berubah bersama hash kata sandi.
        mulai_sesi(g.user, ingat=session.permanent)

        log_event("PASSWORD_CHANGED", logging.WARNING, user_id=g.user.id, username=g.user.username)
        flash("Kata sandi berhasil diperbarui.", "success")
        return redirect(url_for("pengaturan"))
    return _render(password_form=form)
