import io
import os

from conftest import login, read_log, png_file, produk_data, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models import db
from models.produk import Produk


def test_tamu_tidak_bisa_buka_admin(client):
    resp = client.get("/admin")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_customer_ditolak_dari_admin_dan_dicatat(client, app):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for path in ["/admin", "/admin/produk", "/admin/produk/tambah"]:
        resp = client.get(path)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/")
    log = read_log(app)
    assert "ACCESS_DENIED" in log and "path=/admin" in log


def test_dashboard_admin_dan_log_akses(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.get("/admin")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Dashboard Admin" in html and "Mode Admin" in html
    assert "ADMIN_ACCESS" in read_log(app)


def test_crud_produk_lengkap(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)

    # CREATE
    resp = client.post("/admin/produk/tambah", data=produk_data(), content_type="multipart/form-data")
    assert resp.status_code == 302
    with app.app_context():
        produk = Produk.query.one()
        produk_id, gambar = produk.id, produk.gambar
        assert gambar.endswith(".png") and "foto" not in gambar
        assert os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], gambar))

    # READ (admin & katalog publik)
    assert "Galaxy S25 Ultra" in client.get("/admin/produk").get_data(as_text=True)

    # UPDATE tanpa mengganti gambar
    resp = client.post(f"/admin/produk/{produk_id}/edit",
                       data=produk_data(nama_produk="Galaxy S25 Ultra 512GB", harga="20999000", gambar=(io.BytesIO(b""), "")),
                       content_type="multipart/form-data")
    assert resp.status_code == 302
    with app.app_context():
        produk = db.session.get(Produk, produk_id)
        assert produk.nama_produk == "Galaxy S25 Ultra 512GB"
        assert produk.gambar == gambar

    # DELETE (gambar ikut terhapus)
    resp = client.post(f"/admin/produk/{produk_id}/hapus")
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Produk, produk_id) is None
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], gambar))

    log = read_log(app)
    assert "PRODUCT_CREATE" in log and "PRODUCT_UPDATE" in log and "PRODUCT_DELETE" in log


def test_upload_file_palsu_ditolak(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    # File teks/PHP yang diberi nama .png
    data = produk_data(gambar=(io.BytesIO(b"<?php system($_GET['c']); ?>"), "shell.png"))
    resp = client.post("/admin/produk/tambah", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert "File gambar ditolak" in resp.get_data(as_text=True)
    assert "UPLOAD_REJECTED" in read_log(app)
    with app.app_context():
        assert Produk.query.count() == 0


def test_ekstensi_selain_gambar_ditolak(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/admin/produk/tambah", data=produk_data(gambar=png_file("foto.php")),
                       content_type="multipart/form-data")
    assert "Ekstensi file ditolak" in resp.get_data(as_text=True)


def test_validasi_harga_minimal(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/admin/produk/tambah", data=produk_data(harga="500"), content_type="multipart/form-data")
    assert "Harga harus antara" in resp.get_data(as_text=True)


def test_customer_tidak_bisa_hapus_produk(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(), content_type="multipart/form-data")
    client.post("/logout")

    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    with app.app_context():
        produk_id = Produk.query.one().id
    client.post(f"/admin/produk/{produk_id}/hapus")
    with app.app_context():
        assert db.session.get(Produk, produk_id) is not None
