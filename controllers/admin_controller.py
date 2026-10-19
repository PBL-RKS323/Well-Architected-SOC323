from datetime import datetime

from flask import render_template, g

from helpers.security_logger import WIB
from middlewares.auth_middleware import admin_required
from models import db
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


@admin_required
def dashboard():
    stats = {
        "total_produk": Produk.query.count(),
        "total_stok": db.session.query(db.func.coalesce(db.func.sum(Produk.stok), 0)).scalar(),
        "stok_menipis": Produk.query.filter(Produk.stok <= Produk.STOK_MENIPIS).count(),
        "total_customer": User.query.filter_by(role=User.ROLE_CUSTOMER).count(),
    }
    stok_menipis = (Produk.query.filter(Produk.stok <= Produk.STOK_MENIPIS)
                    .order_by(Produk.stok.asc(), Produk.nama_produk.asc()).limit(5).all())
    produk_terbaru = Produk.query.order_by(Produk.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, stok_menipis=stok_menipis,
                           produk_terbaru=produk_terbaru, admin=g.user, sapaan=_sapaan())
