from flask import render_template, redirect, url_for, flash, g

from forms.alamat_form import AlamatForm
from middlewares.auth_middleware import pelanggan_required
from models import db
from models.alamat import Alamat

KOLOM = ("label", "nama_penerima", "telepon", "alamat", "kota", "kode_pos")


def _alamat_milik_user(alamat_id):
    # Alamat hanya bisa diubah pemiliknya (anti IDOR)
    return Alamat.query.filter_by(id=alamat_id, user_id=g.user.id).first_or_404()


def _isi(alamat, form):
    for kolom in KOLOM:
        setattr(alamat, kolom, getattr(form, kolom).data)


@pelanggan_required
def index():
    form = AlamatForm(formdata=None)
    if not Alamat.query.filter_by(user_id=g.user.id).count():
        form.nama_penerima.data = g.user.nama_lengkap or None
    return render_template("akun/alamat.html", daftar=Alamat.milik(g.user.id).all(), form=form,
                           maks=Alamat.MAKS_PER_USER)


@pelanggan_required
def tambah():
    form = AlamatForm()
    daftar = Alamat.milik(g.user.id).all()
    if len(daftar) >= Alamat.MAKS_PER_USER:
        flash(f"Maksimal {Alamat.MAKS_PER_USER} alamat. Hapus salah satu dulu.", "warning")
        return redirect(url_for("akun.alamat"))
    if not form.validate_on_submit():
        return render_template("akun/alamat.html", daftar=daftar, form=form, maks=Alamat.MAKS_PER_USER)

    alamat = Alamat(user_id=g.user.id)
    _isi(alamat, form)
    db.session.add(alamat)
    db.session.flush()
    if form.utama.data or not daftar:  # alamat pertama otomatis jadi utama
        alamat.jadikan_utama()
    db.session.commit()
    flash(f"Alamat {alamat.label} disimpan.", "success")
    return redirect(url_for("akun.alamat"))


@pelanggan_required
def edit(alamat_id):
    alamat = _alamat_milik_user(alamat_id)
    form = AlamatForm(obj=alamat)
    if form.validate_on_submit():
        _isi(alamat, form)
        if form.utama.data:
            alamat.jadikan_utama()
        db.session.commit()
        flash(f"Alamat {alamat.label} diperbarui.", "success")
        return redirect(url_for("akun.alamat"))
    return render_template("akun/alamat_edit.html", form=form, alamat=alamat)


@pelanggan_required
def hapus(alamat_id):
    alamat = _alamat_milik_user(alamat_id)
    label, utama = alamat.label, alamat.utama
    db.session.delete(alamat)
    db.session.flush()
    if utama:  # alamat utama dihapus: alamat tersisa yang paling lama jadi utama
        pengganti = Alamat.milik(g.user.id).first()
        if pengganti:
            pengganti.jadikan_utama()
    db.session.commit()
    flash(f"Alamat {label} dihapus.", "info")
    return redirect(url_for("akun.alamat"))


@pelanggan_required
def jadikan_utama(alamat_id):
    alamat = _alamat_milik_user(alamat_id)
    alamat.jadikan_utama()
    db.session.commit()
    flash(f"{alamat.label} sekarang alamat utama.", "success")
    return redirect(url_for("akun.alamat"))
