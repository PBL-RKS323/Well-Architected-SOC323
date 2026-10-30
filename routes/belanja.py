"""Belanja pelanggan: keranjang, checkout, dan pesanan (wajib login, hanya pesanan milik sendiri)."""
from flask import Blueprint

from controllers import keranjang_controller, pesanan_controller

belanja_bp = Blueprint("belanja", __name__)


# --- KERANJANG ---
@belanja_bp.route("/keranjang")
def keranjang():
    return keranjang_controller.index()


@belanja_bp.route("/keranjang/tambah/<int:produk_id>", methods=["POST"])
def keranjang_tambah(produk_id):
    return keranjang_controller.tambah(produk_id)


@belanja_bp.route("/keranjang/<int:item_id>/ubah", methods=["POST"])
def keranjang_ubah(item_id):
    return keranjang_controller.ubah(item_id)


@belanja_bp.route("/keranjang/<int:item_id>/hapus", methods=["POST"])
def keranjang_hapus(item_id):
    return keranjang_controller.hapus(item_id)


@belanja_bp.route("/keranjang/kosongkan", methods=["POST"])
def keranjang_kosongkan():
    return keranjang_controller.kosongkan()


# --- CHECKOUT & PESANAN ---
@belanja_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    return pesanan_controller.checkout()


@belanja_bp.route("/pesanan")
def pesanan():
    return pesanan_controller.index()


@belanja_bp.route("/pesanan/<kode>")
def pesanan_detail(kode):
    return pesanan_controller.detail(kode)


@belanja_bp.route("/pesanan/<kode>/konfirmasi")
def pesanan_konfirmasi(kode):
    return pesanan_controller.konfirmasi(kode)


@belanja_bp.route("/pesanan/<kode>/bayar", methods=["POST"])
def pesanan_bayar(kode):
    return pesanan_controller.unggah_bukti(kode)


@belanja_bp.route("/pesanan/<kode>/bukti")
def pesanan_bukti(kode):
    return pesanan_controller.bukti(kode)


@belanja_bp.route("/pesanan/<kode>/batal", methods=["POST"])
def pesanan_batal(kode):
    return pesanan_controller.batal(kode)


@belanja_bp.route("/pesanan/<kode>/terima", methods=["POST"])
def pesanan_terima(kode):
    return pesanan_controller.terima(kode)


@belanja_bp.route("/pesanan/<kode>/beli-lagi", methods=["POST"])
def pesanan_beli_lagi(kode):
    return pesanan_controller.beli_lagi(kode)
