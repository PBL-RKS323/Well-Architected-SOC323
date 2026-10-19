import logging

from flask import render_template, redirect, url_for, flash, request, g
from sqlalchemy.exc import IntegrityError

from controllers import toko_controller
from forms.ulasan_form import UlasanForm, BalasanForm
from helpers.security_logger import log_event
from middlewares.auth_middleware import izin_required, pelanggan_required
from models import db, utcnow
from models.produk import Produk
from models.ulasan import Ulasan

PER_HALAMAN = 20
FILTER = {"semua": "Semua", "belum_dibalas": "Belum dibalas", "rendah": "Rating 1-2"}


# --- PELANGGAN ---

@pelanggan_required
def simpan(produk_id):
    """Tambah atau ubah ulasan sendiri. Hanya untuk pembeli yang pesanannya sudah selesai."""
    produk = db.get_or_404(Produk, produk_id)
    tujuan = url_for("produk_detail", produk_id=produk.id, _anchor="ulasan")
    if not Ulasan.boleh_mengulas(g.user, produk.id):
        log_event("REVIEW_REJECTED", logging.WARNING, user_id=g.user.id, product_id=produk.id,
                  reason="not_purchased")
        flash("Ulasan bisa diberikan setelah pesanan berisi produk ini selesai.", "warning")
        return redirect(tujuan)

    form = UlasanForm()
    if not form.validate_on_submit():
        return toko_controller.detail(produk.id, ulasan_form=form), 400

    ulasan = Ulasan.query.filter_by(produk_id=produk.id, user_id=g.user.id).first()
    baru = ulasan is None
    if baru:
        ulasan = Ulasan(produk_id=produk.id, user_id=g.user.id)
        db.session.add(ulasan)
    ulasan.rating = form.rating.data
    ulasan.komentar = form.komentar.data or None
    try:
        db.session.commit()
    except IntegrityError:  # dua kiriman bersamaan: ulasan pertama yang dipakai
        db.session.rollback()
        flash("Ulasanmu sudah tersimpan.", "info")
        return redirect(tujuan)

    log_event("REVIEW_CREATE" if baru else "REVIEW_UPDATE", user_id=g.user.id, product_id=produk.id,
              review_id=ulasan.id, rating=ulasan.rating)
    flash("Terima kasih, ulasanmu sudah tampil." if baru else "Ulasan berhasil diperbarui.", "success")
    return redirect(tujuan)


@pelanggan_required
def hapus_milik_sendiri(produk_id):
    ulasan = Ulasan.query.filter_by(produk_id=produk_id, user_id=g.user.id).first_or_404()
    db.session.delete(ulasan)
    db.session.commit()
    log_event("REVIEW_DELETE", user_id=g.user.id, product_id=produk_id, review_id=ulasan.id, by="owner")
    flash("Ulasan dihapus.", "success")
    return redirect(url_for("produk_detail", produk_id=produk_id, _anchor="ulasan"))


# --- STAF TOKO (moderasi & balasan) ---

@izin_required("kelola_produk")
def index():
    filter_ = request.args.get("filter", "semua")
    if filter_ not in FILTER:
        filter_ = "semua"
    query = Ulasan.query
    if filter_ == "belum_dibalas":
        query = query.filter(Ulasan.balasan.is_(None))
    elif filter_ == "rendah":
        query = query.filter(Ulasan.rating <= 2)
    halaman = query.order_by(Ulasan.created_at.desc()).paginate(per_page=PER_HALAMAN, error_out=False)
    return render_template("admin/ulasan/index.html", halaman=halaman, filter_aktif=filter_, filters=FILTER,
                           belum_dibalas=Ulasan.query.filter(Ulasan.balasan.is_(None)).count())


def _kembali():
    """Kembali ke halaman daftar ulasan dengan filter & halaman yang sama (hanya path internal)."""
    return redirect(url_for("admin_ulasan", filter=request.form.get("filter") or None,
                            page=request.form.get("page", type=int)))


@izin_required("kelola_produk")
def balas(ulasan_id):
    ulasan = db.get_or_404(Ulasan, ulasan_id)
    form = BalasanForm()
    if form.validate_on_submit():
        ulasan.balasan = form.balasan.data
        ulasan.dibalas_at = utcnow()
        db.session.commit()
        log_event("REVIEW_REPLY", user_id=g.user.id, review_id=ulasan.id, product_id=ulasan.produk_id)
        flash("Balasan tersimpan dan tampil di halaman produk.", "success")
    else:
        flash(next(iter(form.balasan.errors), "Balasan tidak valid."), "danger")
    return _kembali()


@izin_required("kelola_produk")
def hapus(ulasan_id):
    ulasan = db.get_or_404(Ulasan, ulasan_id)
    db.session.delete(ulasan)
    db.session.commit()
    log_event("REVIEW_DELETE", logging.WARNING, user_id=g.user.id, review_id=ulasan_id,
              product_id=ulasan.produk_id, review_owner=ulasan.user_id, by="staff")
    flash("Ulasan dihapus.", "success")
    return _kembali()
