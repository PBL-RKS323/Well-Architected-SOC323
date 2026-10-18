from flask import render_template

from models.produk import Produk


def index():
    """Halaman utama: katalog produk untuk semua pengunjung"""
    daftar_produk = Produk.query.order_by(Produk.created_at.desc()).all()
    return render_template("katalog/index.html", produk_list=daftar_produk)
