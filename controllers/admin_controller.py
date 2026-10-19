from datetime import datetime

from flask import render_template, g

from helpers.security_logger import WIB
from middlewares.auth_middleware import admin_required
from models import db
from models.pesanan import Pesanan, PesananItem
from models.produk import Produk
from models.user import User


def _sapaan():
    jam = datetime.now(WIB).hour
    if jam < 11:
        return "Selamat pagi"
    if jam < 15:
        return "Selamat siang"
    if jam < 19:
        return "Selamat sore"
    return "Selamat malam"


def _produk_terlaris(limit=3):
    """Produk dengan pendapatan tertinggi dari pesanan yang sudah dibayar."""
    pendapatan = db.func.sum(PesananItem.harga * PesananItem.jumlah)
    return (db.session.query(PesananItem.nama_produk, PesananItem.merek,
                             db.func.sum(PesananItem.jumlah).label("terjual"), pendapatan.label("pendapatan"))
            .join(Pesanan, PesananItem.pesanan_id == Pesanan.id)
            .filter(Pesanan.status.in_(Pesanan.STATUS_LUNAS))
            .group_by(PesananItem.nama_produk, PesananItem.merek)
            .order_by(pendapatan.desc()).limit(limit).all())


@admin_required
def dashboard():
    Pesanan.batalkan_kedaluwarsa()
    lunas = Pesanan.query.filter(Pesanan.status.in_(Pesanan.STATUS_LUNAS))
    stats = {
        "pendapatan": db.session.query(db.func.coalesce(db.func.sum(Pesanan.total), 0))
                        .filter(Pesanan.status.in_(Pesanan.STATUS_LUNAS)).scalar(),
        "total_pesanan": Pesanan.query.filter(Pesanan.status != Pesanan.DIBATALKAN).count(),
        "pesanan_lunas": lunas.count(),
        "total_customer": User.query.filter_by(role=User.ROLE_CUSTOMER).count(),
        "total_produk": Produk.query.count(),
        "perlu_verifikasi": Pesanan.query.filter_by(status=Pesanan.MENUNGGU_VERIFIKASI).count(),
        "perlu_dikirim": Pesanan.query.filter_by(status=Pesanan.DIPROSES).count(),
        "stok_menipis": Produk.query.filter(Produk.stok <= Produk.STOK_MENIPIS).count(),
    }
    stok_menipis = (Produk.query.filter(Produk.stok <= Produk.STOK_MENIPIS)
                    .order_by(Produk.stok.asc(), Produk.nama_produk.asc()).limit(5).all())
    pesanan_terbaru = Pesanan.query.order_by(Pesanan.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, stok_menipis=stok_menipis,
                           pesanan_terbaru=pesanan_terbaru, terlaris=_produk_terlaris(),
                           admin=g.user, sapaan=_sapaan())
