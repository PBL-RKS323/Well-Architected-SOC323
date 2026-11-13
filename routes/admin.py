"""Panel toko (/admin). Hak akses dicek per izin peran (RBAC) di middleware & decorator controller."""
from flask import Blueprint

from controllers import (admin_controller, produk_controller, admin_pesanan_controller, ulasan_controller,
                         admin_laporan_controller, admin_pengguna_controller)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
def dashboard():
    return admin_controller.dashboard()


# --- PRODUK (izin kelola_produk) ---
@admin_bp.route("/produk")
def produk():
    return produk_controller.index()


@admin_bp.route("/produk/tambah", methods=["GET", "POST"])
def produk_tambah():
    return produk_controller.create()


@admin_bp.route("/produk/<int:produk_id>/edit", methods=["GET", "POST"])
def produk_edit(produk_id):
    return produk_controller.edit(produk_id)


@admin_bp.route("/produk/<int:produk_id>/hapus", methods=["POST"])
def produk_hapus(produk_id):
    return produk_controller.destroy(produk_id)


# --- PESANAN (izin kelola_pesanan) ---
@admin_bp.route("/pesanan")
def pesanan():
    return admin_pesanan_controller.index()


@admin_bp.route("/pesanan/<int:pesanan_id>")
def pesanan_detail(pesanan_id):
    return admin_pesanan_controller.detail(pesanan_id)


@admin_bp.route("/pesanan/<int:pesanan_id>/status", methods=["POST"])
def pesanan_status(pesanan_id):
    return admin_pesanan_controller.ubah_status(pesanan_id)


# --- ULASAN: moderasi & balasan toko (izin kelola_produk) ---
@admin_bp.route("/ulasan")
def ulasan():
    return ulasan_controller.index()


@admin_bp.route("/ulasan/<int:ulasan_id>/balas", methods=["POST"])
def ulasan_balas(ulasan_id):
    return ulasan_controller.balas(ulasan_id)


@admin_bp.route("/ulasan/<int:ulasan_id>/hapus", methods=["POST"])
def ulasan_hapus(ulasan_id):
    return ulasan_controller.hapus(ulasan_id)


# --- LAPORAN TRANSAKSI (izin lihat_laporan, hanya admin) ---
@admin_bp.route("/laporan")
def laporan():
    return admin_laporan_controller.index()


@admin_bp.route("/laporan/csv")
def laporan_csv():
    return admin_laporan_controller.ekspor_csv()


# --- KELOLA PENGGUNA (izin kelola_user, hanya admin) ---
@admin_bp.route("/pengguna")
def pengguna():
    return admin_pengguna_controller.index()


@admin_bp.route("/pengguna/tambah", methods=["GET", "POST"])
def pengguna_tambah():
    return admin_pengguna_controller.tambah()


@admin_bp.route("/pengguna/<int:user_id>")
def pengguna_detail(user_id):
    return admin_pengguna_controller.detail(user_id)


@admin_bp.route("/pengguna/<int:user_id>/aksi", methods=["POST"])
def pengguna_aksi(user_id):
    return admin_pengguna_controller.aksi(user_id)


@admin_bp.route("/pengguna/<int:user_id>/edit", methods=["POST"])
def pengguna_edit(user_id):
    return admin_pengguna_controller.edit(user_id)
