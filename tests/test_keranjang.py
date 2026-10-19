import pytest

from conftest import login, produk_data, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models import db
from models.keranjang import KeranjangItem
from models.produk import Produk
from models.user import User


@pytest.fixture
def produk_ids(client, app):
    """Dua produk: stok 10 dan stok 2, plus satu produk habis."""
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    for nama, stok in [("iPhone 16 Pro", "10"), ("Galaxy Watch 7", "2"), ("Redmi Habis", "0")]:
        client.post("/admin/produk/tambah", data=produk_data(nama_produk=nama, stok=stok),
                    content_type="multipart/form-data")
    client.post("/logout")
    with app.app_context():
        return {p.nama_produk: p.id for p in Produk.query.all()}


def _item(app, username="budi"):
    with app.app_context():
        user = User.query.filter_by(username=username).one()
        return {i.produk.nama_produk: (i.id, i.jumlah) for i in KeranjangItem.query.filter_by(user_id=user.id)}


def test_tamu_harus_login_untuk_keranjang(client, produk_ids):
    assert "/login" in client.get("/keranjang").headers["Location"]
    resp = client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    # Kartu produk untuk tamu mengarah ke login, bukan form POST
    assert "/login?next=" in client.get("/jelajah").get_data(as_text=True)


def test_kartu_produk_punya_tombol_tambah_saat_login(client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.get("/jelajah").get_data(as_text=True)
    assert f'action="/keranjang/tambah/{produk_ids["iPhone 16 Pro"]}"' in html
    assert "/login?next=" not in html


def test_keranjang_kosong(client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.get("/keranjang").get_data(as_text=True)
    assert "Keranjangmu masih kosong" in html and "Mulai Belanja" in html


def test_tambah_produk_dan_badge_jumlah(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}", data={"jumlah": "2"})
    assert resp.status_code == 302
    assert _item(app) == {"iPhone 16 Pro": (_item(app)["iPhone 16 Pro"][0], 2)}

    html = client.get("/keranjang").get_data(as_text=True)
    assert "iPhone 16 Pro" in html and "2 item" in html
    assert "Rp 37.998.000" in html  # 2 x 18.999.000
    assert "data-cart-count" in client.get("/").get_data(as_text=True)


def test_tambah_dua_kali_menjumlahkan_dan_dibatasi(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for _ in range(2):
        client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}", data={"jumlah": "3"})
    assert _item(app)["iPhone 16 Pro"][1] == KeranjangItem.MAKS_PER_PRODUK  # 6 dibatasi jadi 5

    # Stok hanya 2: tambah 5 dibatasi stok
    resp = client.post(f"/keranjang/tambah/{produk_ids['Galaxy Watch 7']}", data={"jumlah": "5"},
                       follow_redirects=True)
    assert _item(app)["Galaxy Watch 7"][1] == 2
    assert "dibatasi 2 unit" in resp.get_data(as_text=True)


def test_produk_habis_tidak_bisa_ditambah(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post(f"/keranjang/tambah/{produk_ids['Redmi Habis']}", follow_redirects=True)
    assert "sedang habis" in resp.get_data(as_text=True)
    assert _item(app) == {}


def test_jumlah_tidak_valid_aman(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    pid = produk_ids["iPhone 16 Pro"]
    client.post(f"/keranjang/tambah/{pid}", data={"jumlah": "abc"})
    assert _item(app)["iPhone 16 Pro"][1] == 1
    client.post(f"/keranjang/tambah/{pid}", data={"jumlah": "-50"})
    assert _item(app)["iPhone 16 Pro"][1] == 2  # minimal tambah 1
    item_id = _item(app)["iPhone 16 Pro"][0]
    client.post(f"/keranjang/{item_id}/ubah", data={"jumlah": "999999"})
    assert _item(app)["iPhone 16 Pro"][1] == KeranjangItem.MAKS_PER_PRODUK


def test_ubah_jumlah_dan_nol_menghapus(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}", data={"jumlah": "3"})
    item_id = _item(app)["iPhone 16 Pro"][0]
    client.post(f"/keranjang/{item_id}/ubah", data={"jumlah": "1"})
    assert _item(app)["iPhone 16 Pro"][1] == 1
    client.post(f"/keranjang/{item_id}/ubah", data={"jumlah": "0"})
    assert _item(app) == {}


def test_hapus_dan_kosongkan(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    client.post(f"/keranjang/tambah/{produk_ids['Galaxy Watch 7']}")
    client.post(f"/keranjang/{_item(app)['iPhone 16 Pro'][0]}/hapus")
    assert list(_item(app)) == ["Galaxy Watch 7"]
    client.post("/keranjang/kosongkan")
    assert _item(app) == {}


def test_tidak_bisa_ubah_keranjang_orang_lain(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    item_budi = _item(app)["iPhone 16 Pro"][0]
    client.post("/logout")

    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    assert client.post(f"/keranjang/{item_budi}/ubah", data={"jumlah": "5"}).status_code == 404
    assert client.post(f"/keranjang/{item_budi}/hapus").status_code == 404
    assert _item(app)["iPhone 16 Pro"][1] == 1


def test_beli_sekarang_ke_keranjang(client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}", data={"beli": "1"})
    assert resp.headers["Location"].endswith("/keranjang")


def test_redirect_next_hanya_internal(client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    pid = produk_ids["iPhone 16 Pro"]
    resp = client.post(f"/keranjang/tambah/{pid}", data={"next": "https://evil.example/x"})
    assert "evil.example" not in resp.headers["Location"]
    resp = client.post(f"/keranjang/tambah/{pid}", data={"next": "/jelajah?q=iphone"})
    assert resp.headers["Location"].endswith("/jelajah?q=iphone")


def test_hapus_produk_ikut_menghapus_dari_keranjang(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    client.post("/logout")
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post(f"/admin/produk/{produk_ids['iPhone 16 Pro']}/hapus")
    client.post("/logout")

    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert client.get("/keranjang").status_code == 200
    assert _item(app) == {}


def test_peringatan_stok_berkurang_setelah_masuk_keranjang(client, app, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['Galaxy Watch 7']}", data={"jumlah": "2"})
    with app.app_context():
        db.session.get(Produk, produk_ids["Galaxy Watch 7"]).stok = 1
        db.session.commit()
    assert "Stok tersisa 1" in client.get("/keranjang").get_data(as_text=True)


def test_detail_punya_form_keranjang(client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.get(f"/produk/{produk_ids['Galaxy Watch 7']}").get_data(as_text=True)
    assert "Beli Sekarang" in html and 'max="2"' in html
    html = client.get(f"/produk/{produk_ids['Redmi Habis']}").get_data(as_text=True)
    assert "Beli Sekarang" not in html
