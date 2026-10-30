"""Pemetaan URL ke controller, dikelompokkan per Blueprint (satu Blueprint = satu area aplikasi).

Nama endpoint memakai awalan Blueprint, misalnya url_for("auth.login") atau url_for("admin.produk").
Logika tetap di controllers/ (MVC); file di sini hanya berisi daftar route.
"""
from routes.toko import toko_bp
from routes.auth import auth_bp
from routes.belanja import belanja_bp
from routes.akun import akun_bp
from routes.admin import admin_bp

BLUEPRINTS = (toko_bp, auth_bp, belanja_bp, akun_bp, admin_bp)


def register_blueprints(app):
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
