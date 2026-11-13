import logging
import os

from flask import render_template, redirect, url_for, flash, session, g, current_app, request

from controllers.auth_controller import mulai_sesi
from forms.akun_form import UbahBiodataForm, UbahNamaForm, UbahEmailForm, UbahPasswordForm, AvatarForm
from helpers.email import email_aktif
from helpers.image_security import simpan_avatar, delete_image
from helpers.security_logger import log_event, ambil_aktivitas_keamanan
from models import db
from models.alamat import Alamat
from models.favorit import Favorit
from models.pesanan import Pesanan


def folder_avatar():
    return os.path.join(current_app.config["UPLOAD_FOLDER"], "avatar")


def _buat_biodata_form(formdata=None):
    return UbahBiodataForm(
        prefix="nama",
        formdata=formdata,
        nama_lengkap=g.user.nama_lengkap,
        telepon=g.user.telepon or "",
        jenis_kelamin=g.user.jenis_kelamin or "",
        tanggal_lahir=g.user.tanggal_lahir,
    )


def _render(nama_form=None, email_form=None, password_form=None, avatar_form=None):
    return render_template(
        "akun/pengaturan.html",
        nama_form=nama_form or _buat_biodata_form(),
        email_form=email_form or UbahEmailForm(prefix="email", formdata=None),
        password_form=password_form or UbahPasswordForm(prefix="pw", formdata=None),
        avatar_form=avatar_form or AvatarForm(prefix="foto", formdata=None),
    )


def ubah_avatar():
    form = AvatarForm(prefix="foto")
    if form.validate_on_submit():
        nama_file = simpan_avatar(form.avatar.data, folder_avatar())
        if nama_file is None:
            log_event("UPLOAD_REJECTED", logging.WARNING, user_id=g.user.id, target="avatar",
                      filename=form.avatar.data.filename)
            form.avatar.errors.append("File ditolak. Pastikan berupa foto JPG/PNG asli, maksimal 2 MB.")
            return _render(avatar_form=form)

        lama, g.user.avatar = g.user.avatar, nama_file
        db.session.commit()
        delete_image(lama, folder_avatar())
        log_event("AVATAR_CHANGED", user_id=g.user.id, username=g.user.username)
        flash("Foto profil berhasil diperbarui.", "success")
        if request.referrer and "profil" in request.referrer:
            return redirect(url_for("akun.profil", tab="profil"))
        return redirect(url_for("akun.pengaturan"))
    return _render(avatar_form=form)


def hapus_avatar():
    if g.user.avatar:
        delete_image(g.user.avatar, folder_avatar())
        g.user.avatar = None
        db.session.commit()
        log_event("AVATAR_REMOVED", user_id=g.user.id, username=g.user.username)
        flash("Foto profil dihapus.", "success")
    if request.referrer and "profil" in request.referrer:
        return redirect(url_for("akun.profil", tab="profil"))
    return redirect(url_for("akun.pengaturan"))


def profil():
    pesanan_terbaru, ringkasan = [], {}
    semua_pesanan = []
    alamat_list = []
    daftar_favorit = []

    if g.user.punya_izin("belanja"):
        milik = Pesanan.query.filter_by(user_id=g.user.id)
        semua_pesanan = milik.order_by(Pesanan.created_at.desc()).limit(10).all()
        pesanan_terbaru = semua_pesanan[:3]
        total_favorit = g.user.daftar_favorit.count() if hasattr(g.user, "daftar_favorit") else 0
        ringkasan = {
            "aktif": milik.filter(Pesanan.status.in_(Pesanan.STATUS_AKTIF)).count(),
            "selesai": milik.filter_by(status=Pesanan.SELESAI).count(),
            "total": milik.count(),
            "favorit": total_favorit,
        }
        alamat_list = Alamat.milik(g.user.id).all()
        if hasattr(g.user, "daftar_favorit"):
            fav_items = g.user.daftar_favorit.order_by(Favorit.created_at.desc()).limit(8).all()
            daftar_favorit = [item.produk for item in fav_items if item.produk is not None]

    nama_form = _buat_biodata_form()
    email_form = UbahEmailForm(prefix="email", formdata=None)
    password_form = UbahPasswordForm(prefix="pw", formdata=None)
    avatar_form = AvatarForm(prefix="foto", formdata=None)

    aktivitas_keamanan = ambil_aktivitas_keamanan(g.user.id, email=g.user.email, username=g.user.username, limit=6)

    keamanan_info = {
        "status_2fa": "Aktif (Wajib)" if (current_app.config.get("OTP_LOGIN_PANEL") and g.user.is_staf_toko()) else ("Tersedia" if email_aktif() else "Nonaktif"),
        "email_terverifikasi": g.user.email_terverifikasi,
        "role_label": g.user.label_role,
        "sesi_token_preview": g.user.sesi_token,
    }

    tab_aktif = request.args.get("tab", "profil")

    return render_template(
        "akun/profil.html",
        pesanan_terbaru=pesanan_terbaru,
        semua_pesanan=semua_pesanan,
        ringkasan=ringkasan,
        alamat_list=alamat_list,
        daftar_favorit=daftar_favorit,
        nama_form=nama_form,
        email_form=email_form,
        password_form=password_form,
        avatar_form=avatar_form,
        aktivitas_keamanan=aktivitas_keamanan,
        keamanan_info=keamanan_info,
        tab_aktif=tab_aktif,
    )


def pengaturan():
    return _render()


def ubah_nama():
    form = UbahBiodataForm(prefix="nama")
    if form.validate_on_submit():
        g.user.nama_lengkap = " ".join(form.nama_lengkap.data.split())
        g.user.telepon = form.telepon.data.strip() if form.telepon.data else None
        g.user.jenis_kelamin = form.jenis_kelamin.data if form.jenis_kelamin.data else None
        g.user.tanggal_lahir = form.tanggal_lahir.data if form.tanggal_lahir.data else None
        db.session.commit()
        log_event("BIODATA_CHANGED", user_id=g.user.id, username=g.user.username)
        flash("Biodata profil berhasil diperbarui.", "success")
        if request.referrer and "profil" in request.referrer:
            return redirect(url_for("akun.profil", tab="profil"))
        return redirect(url_for("akun.pengaturan"))
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
        g.user.email_terverifikasi = not email_aktif()
        db.session.commit()
        log_event("EMAIL_CHANGED", logging.WARNING, user_id=g.user.id, username=g.user.username)
        flash("Email berhasil diperbarui.", "success")
        if request.referrer and "profil" in request.referrer:
            return redirect(url_for("akun.profil", tab="keamanan"))
        return redirect(url_for("akun.pengaturan"))
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
        if request.referrer and "profil" in request.referrer:
            return redirect(url_for("akun.profil", tab="keamanan"))
        return redirect(url_for("akun.pengaturan"))
    return _render(password_form=form)
