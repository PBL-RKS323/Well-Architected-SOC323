"""Controller favorit / wishlist pelanggan."""
from flask import render_template, redirect, url_for, flash, request, g, jsonify, abort
from middlewares.auth_middleware import pelanggan_required
from models import db
from models.favorit import Favorit
from models.produk import Produk


@pelanggan_required
def index():
    """Halaman daftar produk favorit / wishlist pelanggan."""
    favorit_items = g.user.daftar_favorit.order_by(Favorit.created_at.desc()).all()
    produk_list = [item.produk for item in favorit_items if item.produk is not None]
    return render_template("toko/favorit.html", produk_list=produk_list)


@pelanggan_required
def toggle(produk_id):
    """Menambah atau menghapus produk dari wishlist."""
    produk = db.session.get(Produk, produk_id)
    if produk is None:
        abort(404)
    is_added = Favorit.toggle(g.user.id, produk.id)
    pesan = (
        f"{produk.nama_produk} berhasil ditambahkan ke Favorit."
        if is_added
        else f"{produk.nama_produk} dihapus dari Favorit."
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "success": True,
            "favorit": is_added,
            "message": pesan,
            "count": g.user.daftar_favorit.count(),
        })

    flash(pesan, "success" if is_added else "info")
    next_url = request.form.get("next") or request.referrer or url_for("toko.produk_detail", produk_id=produk.id)
    return redirect(next_url)
