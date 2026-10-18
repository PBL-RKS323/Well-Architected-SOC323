from flask import render_template, g

from middlewares.auth_middleware import admin_required
from models import db
from models.produk import Produk
from models.user import User


@admin_required
def dashboard():
    stats = {
        "total_produk": Produk.query.count(),
        "total_stok": db.session.query(db.func.coalesce(db.func.sum(Produk.stok), 0)).scalar(),
        "stok_habis": Produk.query.filter(Produk.stok == 0).count(),
        "total_customer": User.query.filter_by(role=User.ROLE_CUSTOMER).count(),
    }
    produk_terbaru = Produk.query.order_by(Produk.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, produk_terbaru=produk_terbaru, admin=g.user)
