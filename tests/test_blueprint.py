"""Struktur Blueprint: semua route terkelompok per area, dan setiap halaman menu tetap bisa dibuka
oleh peran yang berhak (memastikan tidak ada url_for yang masih memakai nama endpoint lama)."""
from conftest import login, ADMIN_PASSWORD, CUSTOMER_PASSWORD

BLUEPRINT_DIHARAPKAN = {"toko", "auth", "belanja", "akun", "admin"}


def test_semua_route_berada_di_blueprint(app):
    endpoint = {r.endpoint for r in app.url_map.iter_rules()} - {"static"}
    assert set(app.blueprints) == BLUEPRINT_DIHARAPKAN
    tanpa_blueprint = [e for e in endpoint if "." not in e]
    assert tanpa_blueprint == []
    assert {e.split(".")[0] for e in endpoint} == BLUEPRINT_DIHARAPKAN


def test_path_url_tidak_berubah(app):
    """Refactor ke Blueprint tidak boleh mengubah alamat (link lama & redirect URI Google tetap berlaku)."""
    peta = {r.rule: r.endpoint for r in app.url_map.iter_rules()}
    assert peta["/"] == "toko.beranda"
    assert peta["/login"] == "auth.login"
    assert peta["/login/google/callback"] == "auth.login_google_callback"
    assert peta["/keranjang"] == "belanja.keranjang"
    assert peta["/pengaturan"] == "akun.pengaturan"
    assert peta["/admin"] == "admin.dashboard"
    assert peta["/admin/pengguna/<int:user_id>"] == "admin.pengguna_detail"


def test_halaman_tamu(client):
    for path in ["/", "/jelajah", "/login", "/register", "/lupa-password", "/kredit-foto"]:
        assert client.get(path).status_code == 200, path
    # Default deny: halaman lain wajib login
    res = client.get("/keranjang")
    assert res.status_code == 302 and "/login" in res.headers["Location"]


def test_halaman_pelanggan(client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for path in ["/", "/jelajah", "/keranjang", "/pesanan", "/profil", "/pengaturan", "/alamat"]:
        assert client.get(path).status_code == 200, path


def test_halaman_panel_admin(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    for path in ["/admin", "/admin/produk", "/admin/produk/tambah", "/admin/pesanan", "/admin/ulasan",
                 "/admin/laporan", "/admin/pengguna", "/admin/pengguna/tambah", "/profil", "/pengaturan"]:
        assert client.get(path).status_code == 200, path
