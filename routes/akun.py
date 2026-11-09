"""Akun pengguna yang sudah login: profil, pengaturan (nama, biodata, email, kata sandi, foto), dan alamat tersimpan."""
from flask import Blueprint

from controllers import akun_controller, alamat_controller

akun_bp = Blueprint("akun", __name__)


# --- PROFIL & PENGATURAN (semua user yang login) ---
@akun_bp.route("/profil")
def profil():
    return akun_controller.profil()


@akun_bp.route("/pengaturan")
def pengaturan():
    return akun_controller.pengaturan()


@akun_bp.route("/pengaturan/nama", methods=["POST"])
@akun_bp.route("/pengaturan/biodata", methods=["POST"])
def pengaturan_nama():
    return akun_controller.ubah_nama()


@akun_bp.route("/pengaturan/email", methods=["POST"])
def pengaturan_email():
    return akun_controller.ubah_email()


@akun_bp.route("/pengaturan/password", methods=["POST"])
def pengaturan_password():
    return akun_controller.ubah_password()


@akun_bp.route("/pengaturan/foto", methods=["POST"])
def pengaturan_foto():
    return akun_controller.ubah_avatar()


@akun_bp.route("/pengaturan/foto/hapus", methods=["POST"])
def pengaturan_foto_hapus():
    return akun_controller.hapus_avatar()


# --- ALAMAT TERSIMPAN (pelanggan) ---
@akun_bp.route("/alamat")
def alamat():
    return alamat_controller.index()


@akun_bp.route("/alamat/tambah", methods=["POST"])
def alamat_tambah():
    return alamat_controller.tambah()


@akun_bp.route("/alamat/<int:alamat_id>/edit", methods=["GET", "POST"])
def alamat_edit(alamat_id):
    return alamat_controller.edit(alamat_id)


@akun_bp.route("/alamat/<int:alamat_id>/hapus", methods=["POST"])
def alamat_hapus(alamat_id):
    return alamat_controller.hapus(alamat_id)


@akun_bp.route("/alamat/<int:alamat_id>/utama", methods=["POST"])
def alamat_utama(alamat_id):
    return alamat_controller.jadikan_utama(alamat_id)
