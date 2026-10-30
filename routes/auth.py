"""Autentikasi: daftar, masuk/keluar, kode OTP email, lupa kata sandi, dan masuk dengan Google."""
from flask import Blueprint

from controllers import auth_controller, otp_controller, google_controller

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    return auth_controller.register()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    return auth_controller.login()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return auth_controller.logout()


# --- KODE OTP EMAIL & LUPA KATA SANDI ---
@auth_bp.route("/verifikasi", methods=["GET", "POST"])
def verifikasi_kode():
    return otp_controller.verifikasi()


@auth_bp.route("/verifikasi/kirim-ulang", methods=["POST"])
def verifikasi_kirim_ulang():
    return otp_controller.verifikasi_kirim_ulang()


@auth_bp.route("/lupa-password", methods=["GET", "POST"])
def lupa_password():
    return otp_controller.lupa_password()


@auth_bp.route("/lupa-password/kode", methods=["GET", "POST"])
def lupa_password_kode():
    return otp_controller.lupa_password_kode()


@auth_bp.route("/lupa-password/kirim-ulang", methods=["POST"])
def lupa_password_kirim_ulang():
    return otp_controller.lupa_password_kirim_ulang()


# --- MASUK DENGAN GOOGLE ---
# Path callback jangan diubah: harus sama dengan "Authorized redirect URI" di Google Cloud Console
@auth_bp.route("/login/google")
def login_google():
    return google_controller.login()


@auth_bp.route("/login/google/callback")
def login_google_callback():
    return google_controller.callback()
