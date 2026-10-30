"""Halaman toko untuk publik: beranda, jelajah, detail produk, dan ulasan pembeli."""
from flask import Blueprint

from controllers import toko_controller, ulasan_controller

toko_bp = Blueprint("toko", __name__)


@toko_bp.route("/")
def beranda():
    return toko_controller.beranda()


@toko_bp.route("/jelajah")
def jelajah():
    return toko_controller.jelajah()


@toko_bp.route("/produk/<int:produk_id>")
def produk_detail(produk_id):
    return toko_controller.detail(produk_id)


# --- ULASAN (pembeli yang pesanannya sudah selesai) ---
@toko_bp.route("/produk/<int:produk_id>/ulasan", methods=["POST"])
def ulasan_simpan(produk_id):
    return ulasan_controller.simpan(produk_id)


@toko_bp.route("/produk/<int:produk_id>/ulasan/hapus", methods=["POST"])
def ulasan_hapus(produk_id):
    return ulasan_controller.hapus_milik_sendiri(produk_id)


@toko_bp.route("/kredit-foto")
def kredit_foto():
    return toko_controller.kredit_foto()
