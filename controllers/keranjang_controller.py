from flask import render_template, redirect, url_for, flash, request, g

from controllers.auth_controller import _safe_next_url
from middlewares.auth_middleware import pelanggan_required
from models import db
from models.keranjang import KeranjangItem
from models.produk import Produk


def _jumlah_dari_form(default=1):
    """Jumlah dari form dibatasi 0..MAKS agar nilai negatif / sangat besar tidak diproses."""
    try:
        jumlah = int(request.form.get("jumlah", default))
    except (TypeError, ValueError):
        return default
    return max(0, min(jumlah, KeranjangItem.MAKS_PER_PRODUK))


def _item_milik_user(item_id):
    # Item hanya bisa diubah pemiliknya (mencegah IDOR: mengubah keranjang orang lain lewat ID)
    return KeranjangItem.query.filter_by(id=item_id, user_id=g.user.id).first_or_404()


def item_user():
    return (KeranjangItem.query.filter_by(user_id=g.user.id)
            .order_by(KeranjangItem.created_at.desc()).all())


def jumlah_item(user):
    if user is None:
        return 0
    total = db.session.query(db.func.coalesce(db.func.sum(KeranjangItem.jumlah), 0)) \
        .filter(KeranjangItem.user_id == user.id).scalar()
    return int(total)


@pelanggan_required
def index():
    items = item_user()
    tersedia = [i for i in items if i.produk.stok > 0]
    ringkasan = {
        "jumlah": sum(i.jumlah for i in tersedia),
        "subtotal": sum(i.subtotal for i in tersedia),
        "hemat": sum((i.produk.harga_normal - i.produk.harga) * i.jumlah
                     for i in tersedia if i.produk.diskon_persen),
        "ada_masalah": any(i.jumlah > i.produk.stok for i in items),
    }
    ringkasan["bisa_checkout"] = bool(items) and not ringkasan["ada_masalah"]
    rekomendasi = []
    if not items:
        rekomendasi = (Produk.query.filter(Produk.stok > 0)
                       .order_by(Produk.created_at.desc()).limit(4).all())
    return render_template("toko/keranjang.html", items=items, ringkasan=ringkasan, rekomendasi=rekomendasi)


@pelanggan_required
def tambah(produk_id):
    produk = db.get_or_404(Produk, produk_id)
    kembali = _safe_next_url(request.form.get("next")) or url_for("toko.produk_detail", produk_id=produk.id)

    if produk.stok == 0:
        flash(f"Maaf, {produk.nama_produk} sedang habis.", "danger")
        return redirect(kembali)

    jumlah = max(1, _jumlah_dari_form())
    item = KeranjangItem.query.filter_by(user_id=g.user.id, produk_id=produk.id).first()
    if item is None:
        item = KeranjangItem(user_id=g.user.id, produk_id=produk.id, jumlah=0)
        db.session.add(item)
        item.produk = produk

    diminta = item.jumlah + jumlah
    item.jumlah = min(diminta, item.batas)
    db.session.commit()

    if diminta > item.jumlah:
        flash(f"Jumlah {produk.nama_produk} di keranjang dibatasi {item.jumlah} unit "
              f"(stok tersedia / maksimal {KeranjangItem.MAKS_PER_PRODUK} per pesanan).", "warning")
    else:
        flash(f"{produk.nama_produk} ditambahkan ke keranjang.", "success")

    if request.form.get("beli"):
        return redirect(url_for("belanja.checkout"))
    return redirect(kembali)


@pelanggan_required
def ubah(item_id):
    item = _item_milik_user(item_id)
    nama = item.produk.nama_produk
    jumlah = _jumlah_dari_form(default=item.jumlah)
    if jumlah == 0:
        db.session.delete(item)
        flash(f"{nama} dihapus dari keranjang.", "info")
    else:
        item.jumlah = min(jumlah, max(item.batas, 1))
    db.session.commit()
    return redirect(url_for("belanja.keranjang"))


@pelanggan_required
def hapus(item_id):
    item = _item_milik_user(item_id)
    nama = item.produk.nama_produk
    db.session.delete(item)
    db.session.commit()
    flash(f"{nama} dihapus dari keranjang.", "info")
    return redirect(url_for("belanja.keranjang"))


@pelanggan_required
def kosongkan():
    KeranjangItem.query.filter_by(user_id=g.user.id).delete()
    db.session.commit()
    flash("Keranjang dikosongkan.", "info")
    return redirect(url_for("belanja.keranjang"))
