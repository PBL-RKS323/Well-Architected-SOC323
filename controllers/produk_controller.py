import logging

from flask import render_template, redirect, url_for, flash, current_app, g, request

from controllers.toko_controller import _escape_like
from forms.produk_form import FormProduk
from helpers.image_security import upload_secure_image, delete_image
from helpers.security_logger import log_event
from middlewares.auth_middleware import izin_required
from models import db
from models.keranjang import KeranjangItem
from models.pesanan import PesananItem
from models.produk import Produk


def _isi_produk(produk, form):
    produk.nama_produk = form.nama_produk.data.strip()
    produk.merek = form.merek.data.strip()
    produk.kategori = form.kategori.data
    produk.harga = form.harga.data
    produk.harga_normal = form.harga_normal.data or None
    produk.stok = form.stok.data
    produk.deskripsi = (form.deskripsi.data or "").strip()


def _tolak_upload(filename):
    log_event("UPLOAD_REJECTED", logging.WARNING, user_id=g.user.id, filename=filename)
    flash("File gambar ditolak! Pastikan file benar-benar JPG/PNG dan ukurannya maksimal 2 MB.", "danger")


@izin_required("kelola_produk")
def index():
    """[READ] Daftar produk di panel admin, bisa dicari berdasarkan nama/merek"""
    q = request.args.get("q", "").strip()[:100]
    query = Produk.query
    if q:
        pola = f"%{_escape_like(q)}%"
        query = query.filter(Produk.nama_produk.ilike(pola, escape="\\") | Produk.merek.ilike(pola, escape="\\"))
    daftar_produk = query.order_by(Produk.id.desc()).all()
    return render_template("admin/produk/index.html", produk_list=daftar_produk, q=q)


@izin_required("kelola_produk")
def create():
    """[CREATE] Form tambah produk dan penyimpanannya"""
    form = FormProduk()
    if form.validate_on_submit():
        if not form.gambar.data or not getattr(form.gambar.data, "filename", ""):
            form.gambar.errors.append("File gambar wajib diunggah untuk produk baru!")
            return render_template("admin/produk/form.html", form=form, mode="tambah")

        nama_file = upload_secure_image(form.gambar.data, current_app.config["UPLOAD_FOLDER"])
        if not nama_file:
            _tolak_upload(form.gambar.data.filename)
            return render_template("admin/produk/form.html", form=form, mode="tambah")

        produk = Produk(gambar=nama_file)
        _isi_produk(produk, form)
        db.session.add(produk)
        db.session.commit()

        log_event("PRODUCT_CREATE", user_id=g.user.id, product_id=produk.id, name=produk.nama_produk)
        flash("Produk berhasil ditambahkan!", "success")
        return redirect(url_for("admin_produk"))
    return render_template("admin/produk/form.html", form=form, mode="tambah")


@izin_required("kelola_produk")
def edit(produk_id):
    """[UPDATE] Form ubah produk dan penyimpanannya"""
    produk = db.get_or_404(Produk, produk_id)
    form = FormProduk(obj=produk)
    if form.validate_on_submit():
        if form.gambar.data and getattr(form.gambar.data, "filename", ""):
            nama_file = upload_secure_image(form.gambar.data, current_app.config["UPLOAD_FOLDER"])
            if not nama_file:
                _tolak_upload(form.gambar.data.filename)
                return render_template("admin/produk/form.html", form=form, mode="edit", produk=produk)
            delete_image(produk.gambar, current_app.config["UPLOAD_FOLDER"])
            produk.gambar = nama_file

        _isi_produk(produk, form)
        db.session.commit()

        log_event("PRODUCT_UPDATE", user_id=g.user.id, product_id=produk.id, name=produk.nama_produk)
        flash("Produk berhasil diperbarui!", "success")
        return redirect(url_for("admin_produk"))
    return render_template("admin/produk/form.html", form=form, mode="edit", produk=produk)


@izin_required("kelola_produk")
def destroy(produk_id):
    """[DELETE] Hapus produk beserta file gambarnya"""
    produk = db.get_or_404(Produk, produk_id)
    delete_image(produk.gambar, current_app.config["UPLOAD_FOLDER"])
    KeranjangItem.query.filter_by(produk_id=produk.id).delete()
    # Riwayat pesanan tetap disimpan (nama & harga sudah disalin saat checkout)
    PesananItem.query.filter_by(produk_id=produk.id).update({"produk_id": None})
    db.session.delete(produk)
    db.session.commit()

    log_event("PRODUCT_DELETE", logging.WARNING, user_id=g.user.id, product_id=produk_id, name=produk.nama_produk)
    flash("Produk berhasil dihapus!", "success")
    return redirect(url_for("admin_produk"))
