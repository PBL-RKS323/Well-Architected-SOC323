from conftest import login, produk_data, ADMIN_PASSWORD
from app import create_app
from config import TestConfig


def test_katalog_publik_kosong(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Belum ada produk" in resp.get_data(as_text=True)


def test_katalog_menampilkan_produk_dan_rupiah(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(), content_type="multipart/form-data")
    client.post("/logout")

    html = client.get("/").get_data(as_text=True)
    assert "Galaxy S25 Ultra" in html
    assert "Rp 18.999.000" in html


def test_katalog_dikelompokkan_per_ekosistem(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(nama_produk="iPhone 16", merek="Apple"),
                content_type="multipart/form-data")
    client.post("/admin/produk/tambah", data=produk_data(nama_produk="Redmi Note 14", merek="Xiaomi"),
                content_type="multipart/form-data")

    html = client.get("/").get_data(as_text=True)
    assert "Ekosistem Apple" in html and "Ekosistem Xiaomi" in html
    assert "Ekosistem Samsung" not in html  # brand tanpa produk tidak ditampilkan
    assert html.index("Ekosistem Apple") < html.index("iPhone 16") < html.index("Ekosistem Xiaomi")


def test_merek_di_luar_daftar_ditolak(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/admin/produk/tambah", data=produk_data(merek="Merek Palsu"),
                       content_type="multipart/form-data")
    assert resp.status_code == 200
    assert "Not a valid choice" in resp.get_data(as_text=True) or "pilihan" in resp.get_data(as_text=True)


def test_kolom_password_punya_tombol_mata(client):
    html = client.get("/login").get_data(as_text=True)
    assert "data-toggle-password" in html


def test_xss_di_nama_produk_di_escape(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(nama_produk="<script>alert(1)</script>"),
                content_type="multipart/form-data")
    html = client.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in resp.headers  # belum HTTPS (pengembangan lokal)


def test_hsts_dan_banner_demo_di_produksi(tmp_path):
    class Cfg(TestConfig):
        SESSION_COOKIE_SECURE = True
        DEMO_MODE = True
        SECURITY_LOG_FILE = str(tmp_path / "security.log")

    resp = create_app(Cfg).test_client().get("/static/js/app.js")
    assert resp.headers["Strict-Transport-Security"] == "max-age=31536000"
    app = create_app(Cfg)
    with app.app_context():
        from models import db
        db.create_all()
        assert "Toko demo tugas kuliah" in app.test_client().get("/login").get_data(as_text=True)


def test_csrf_aktif_di_konfigurasi_normal(tmp_path):
    class Cfg(TestConfig):
        WTF_CSRF_ENABLED = True
        SECURITY_LOG_FILE = str(tmp_path / "security.log")

    app = create_app(Cfg)
    with app.app_context():
        from models import db
        db.create_all()
    resp = app.test_client().post("/login", data={"email": "a@tokoelektronik.id", "password": "x"})
    assert resp.status_code == 400
    with open(Cfg.SECURITY_LOG_FILE, encoding="utf-8") as f:
        assert "CSRF_FAILURE" in f.read()


def test_404_memakai_halaman_error(client):
    resp = client.get("/tidak-ada")
    assert resp.status_code == 404
