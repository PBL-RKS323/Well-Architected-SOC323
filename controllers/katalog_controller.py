from flask import render_template

from models.produk import Produk


def index():
    """Halaman utama: katalog produk dikelompokkan per ekosistem brand"""
    daftar_produk = Produk.query.order_by(Produk.created_at.desc()).all()

    per_merek = {merek: [] for merek in Produk.MEREK}
    for produk in daftar_produk:
        per_merek.setdefault(produk.merek, []).append(produk)
    ekosistem = [(merek, items) for merek, items in per_merek.items() if items]

    return render_template("katalog/index.html", ekosistem=ekosistem, total=len(daftar_produk))
