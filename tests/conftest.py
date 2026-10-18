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


@pytest.fixture
def app(tmp_path):
    class Cfg(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        SECURITY_LOG_FILE = str(tmp_path / "logs" / "security.log")

    app = create_app(Cfg)
    with app.app_context():
        db.create_all()
        admin = User(username="admin", email="admin@tokoelektronik.id", role=User.ROLE_ADMIN)
        admin.set_password(ADMIN_PASSWORD)
        customer = User(username="budi", email="budi@tokoelektronik.id", role=User.ROLE_CUSTOMER)
        customer.set_password(CUSTOMER_PASSWORD)
        db.session.add_all([admin, customer])
        db.session.commit()
    yield app


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
