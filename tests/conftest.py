import base64
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from models import db  # noqa: E402
from models.user import User  # noqa: E402

ADMIN_PASSWORD = "AdminTest123!"
CUSTOMER_PASSWORD = "Customer123!"

# Gambar PNG asli berukuran 1x1 piksel
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def buat_app(tmp_path, **tambahan):
    """Aplikasi uji dengan 2 akun awal. `tambahan` menimpa konfigurasi (mis. menyalakan email)."""
    class Cfg(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        SECURITY_LOG_FILE = str(tmp_path / "logs" / "security.log")
        BUKTI_BAYAR_FOLDER = str(tmp_path / "bukti_bayar")

    for kunci, nilai in tambahan.items():
        setattr(Cfg, kunci, nilai)
    app = create_app(Cfg)
    with app.app_context():
        db.create_all()
        admin = User(username="admin", nama_lengkap="Admin Toko", email="admin@tokoelektronik.id", role=User.ROLE_ADMIN)
        admin.set_password(ADMIN_PASSWORD)
        customer = User(username="budi", nama_lengkap="Budi Santoso", email="budi@tokoelektronik.id", role=User.ROLE_CUSTOMER)
        customer.set_password(CUSTOMER_PASSWORD)
        db.session.add_all([admin, customer])
        db.session.commit()
    return app


def tutup_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()  # wajib jika TEST_DATABASE_URL memakai PostgreSQL agar tiap tes mulai dari kosong


@pytest.fixture
def app(tmp_path):
    app = buat_app(tmp_path)
    yield app
    tutup_app(app)


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def read_log(app):
    path = app.config["SECURITY_LOG_FILE"]
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def png_file(name="foto.png"):
    return (io.BytesIO(PNG_BYTES), name)


def produk_data(**overrides):
    data = {
        "nama_produk": "Galaxy S25 Ultra",
        "merek": "Samsung",
        "kategori": "Handphone",
        "harga": "18999000",
        "stok": "10",
        "deskripsi": "HP flagship",
        "gambar": png_file(),
    }
    data.update(overrides)
    return data
