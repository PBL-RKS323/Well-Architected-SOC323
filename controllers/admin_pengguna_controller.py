import logging

from flask import render_template, redirect, url_for, flash, request, g, make_response

from controllers.auth_controller import _buat_username
from controllers.toko_controller import _escape_like
from forms.pengguna_form import TambahPenggunaForm, AksiPenggunaForm, EditPenggunaForm
from helpers.kata_sandi import buat_kata_sandi_sementara
from helpers.security_logger import log_event
from middlewares.auth_middleware import izin_required
from models import db
from models.pesanan import Pesanan
from models.user import User

PER_HALAMAN = 20
TAB = {
    "semua": "Semua",
    User.ROLE_CUSTOMER: "Pelanggan",
    User.ROLE_STAF: "Staf",
    User.ROLE_ADMIN: "Admin",
    "nonaktif": "Nonaktif",
}


def _filter_tab(query, tab):
    if tab == "nonaktif":
        return query.filter(User.aktif.is_(False))
    if tab in User.LABEL_ROLE:
        return query.filter(User.role == tab)
    return query


@izin_required("kelola_user")
def index():
    tab = request.args.get("tab", "semua")
    if tab not in TAB:
        tab = "semua"
    q = request.args.get("q", "").strip()[:100]

    dasar = User.query
    if q:
        pola = f"%{_escape_like(q)}%"
        dasar = dasar.filter(User.nama_lengkap.ilike(pola, escape="\\") | User.email.ilike(pola, escape="\\")
                             | User.username.ilike(pola, escape="\\"))
    jumlah_tab = {nama: _filter_tab(dasar, nama).count() for nama in TAB}
    halaman = (_filter_tab(dasar, tab).order_by(User.created_at.desc())
               .paginate(per_page=PER_HALAMAN, error_out=False))
    return render_template("admin/pengguna/index.html", halaman=halaman, tab=tab, tabs=TAB, q=q,
                           jumlah_tab=jumlah_tab)


@izin_required("kelola_user")
def tambah():
    form = TambahPenggunaForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User(username=_buat_username(email), nama_lengkap=" ".join(form.nama_lengkap.data.split()),
                    email=email, role=form.peran.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_event("USER_CREATED", logging.WARNING, user_id=g.user.id, target_id=user.id,
                  target=user.username, role=user.role)
        flash(f"Akun {user.display_name} ({user.label_role}) berhasil dibuat.", "success")
        return redirect(url_for("admin_pengguna_detail", user_id=user.id))
    return render_template("admin/pengguna/tambah.html", form=form)


def _render_detail(user, data_form=None, password_baru=None):
    pesanan = Pesanan.query.filter_by(user_id=user.id)
    ringkasan = {
        "jumlah_pesanan": pesanan.count(),
        "total_belanja": db.session.query(db.func.coalesce(db.func.sum(Pesanan.total), 0))
                           .filter(Pesanan.user_id == user.id, Pesanan.status.in_(Pesanan.STATUS_LUNAS)).scalar(),
    }
    data_form = data_form or EditPenggunaForm(prefix="data", formdata=None, user_id=user.id,
                                              nama_lengkap=user.nama_lengkap, email=user.email)
    respons = make_response(render_template(
        "admin/pengguna/detail.html", user=user, form=AksiPenggunaForm(peran=user.role), data_form=data_form,
        password_baru=password_baru, ringkasan=ringkasan,
        pesanan_terbaru=pesanan.order_by(Pesanan.created_at.desc()).limit(5).all()))
    if password_baru:
        respons.headers["Cache-Control"] = "no-store"  # halaman berisi kata sandi tidak boleh disimpan browser
    return respons


@izin_required("kelola_user")
def detail(user_id):
    return _render_detail(db.get_or_404(User, user_id))


@izin_required("kelola_user")
def edit(user_id):
    """Ubah nama/email akun lain. Akun sendiri lewat Pengaturan (ganti email wajib konfirmasi kata sandi)."""
    user = db.get_or_404(User, user_id)
    if user.id == g.user.id:
        flash("Ubah data akunmu sendiri lewat halaman Pengaturan.", "warning")
        return redirect(url_for("pengaturan"))
    form = EditPenggunaForm(prefix="data", user_id=user.id)
    if not form.validate_on_submit():
        return _render_detail(user, data_form=form)

    nama = " ".join(form.nama_lengkap.data.split())
    email = form.email.data.strip().lower()
    berubah = [kolom for kolom, lama, baru in [("nama", user.nama_lengkap, nama), ("email", user.email, email)]
               if lama != baru]
    if berubah:
        user.nama_lengkap, user.email = nama, email
        db.session.commit()
        log_event("USER_UPDATED", logging.WARNING, user_id=g.user.id, target_id=user.id, target=user.username,
                  fields=",".join(berubah))
        flash(f"Data akun {user.display_name} diperbarui.", "success")
    return redirect(url_for("admin_pengguna_detail", user_id=user.id))


def _admin_aktif_lain(user):
    return User.query.filter(User.role == User.ROLE_ADMIN, User.aktif.is_(True), User.id != user.id).count()


@izin_required("kelola_user")
def aksi(user_id):
    user = db.get_or_404(User, user_id)
    form = AksiPenggunaForm()
    kembali = redirect(url_for("admin_pengguna_detail", user_id=user.id))
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return kembali

    aksi_ = form.aksi.data
    # Pengaman: admin tidak bisa menurunkan perannya / menonaktifkan dirinya sendiri, dan minimal harus
    # selalu ada satu admin aktif (mencegah panel terkunci tanpa admin).
    mengurangi_admin = user.role == User.ROLE_ADMIN and (
        aksi_ == "nonaktifkan" or (aksi_ == "ubah_peran" and form.peran.data != User.ROLE_ADMIN))
    if aksi_ in ("ubah_peran", "nonaktifkan", "reset_password") and user.id == g.user.id:
        flash("Kamu tidak bisa mengubah peran, menonaktifkan, atau mereset kata sandi akunmu sendiri "
              "(ganti kata sandi lewat Pengaturan).", "warning")
        return kembali
    if mengurangi_admin and _admin_aktif_lain(user) == 0:
        flash("Harus ada minimal satu admin aktif.", "warning")
        return kembali

    if aksi_ == "ubah_peran":
        if form.peran.data == user.role:
            return kembali
        lama, user.role = user.role, form.peran.data
        db.session.commit()
        log_event("USER_ROLE_CHANGED", logging.WARNING, user_id=g.user.id, target_id=user.id,
                  target=user.username, role_from=lama, role_to=user.role)
        flash(f"Peran {user.display_name} diubah menjadi {user.label_role}.", "success")
    elif aksi_ == "nonaktifkan":
        user.aktif = False
        db.session.commit()
        log_event("USER_DEACTIVATED", logging.WARNING, user_id=g.user.id, target_id=user.id, target=user.username)
        flash(f"Akun {user.display_name} dinonaktifkan. Sesi yang sedang berjalan langsung berakhir.", "success")
    elif aksi_ == "aktifkan":
        user.aktif = True
        db.session.commit()
        log_event("USER_ACTIVATED", logging.WARNING, user_id=g.user.id, target_id=user.id, target=user.username)
        flash(f"Akun {user.display_name} diaktifkan kembali.", "success")
    elif aksi_ == "buka_kunci":
        user.reset_failed_login()
        db.session.commit()
        log_event("USER_UNLOCKED", user_id=g.user.id, target_id=user.id, target=user.username)
        flash(f"Kunci login {user.display_name} dibuka.", "success")
    elif aksi_ == "reset_password":
        # Kata sandi sementara acak ditampilkan SEKALI di halaman ini (tidak lewat flash/sesi, tidak disimpan).
        # Sesi lama pemilik akun otomatis berakhir karena sesi_token ikut berubah.
        password = buat_kata_sandi_sementara()
        user.set_password(password)
        user.reset_failed_login()
        db.session.commit()
        log_event("USER_PASSWORD_RESET", logging.WARNING, user_id=g.user.id, target_id=user.id, target=user.username)
        return _render_detail(user, password_baru=password)
    return kembali
