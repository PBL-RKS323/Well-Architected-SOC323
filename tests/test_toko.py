import re

from conftest import login, produk_data, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models import db
from models.produk import Produk
from models.user import User


def _tambah(client, **data):
    resp = client.post("/admin/produk/tambah", data=produk_data(**data), content_type="multipart/form-data")
    assert resp.status_code == 302, resp.get_data(as_text=True)


def _isi_katalog(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    _tambah(client, nama_produk="iPhone 16 Pro", merek="Apple", kategori="Handphone", harga="21999000")
    _tambah(client, nama_produk="MacBook Air M4", merek="Apple", kategori="Laptop", harga="18999000")
    _tambah(client, nama_produk="Redmi Note 14", merek="Xiaomi", kategori="Handphone", harga="4299000",
            harga_normal="4999000")
    _tambah(client, nama_produk="Galaxy Watch 7", merek="Samsung", kategori="Smartwatch", harga="3999000",
            deskripsi="Diskon 100% asli")
    client.post("/logout")


def _nama_di_halaman(html):
    return re.findall(r'<h3 class="[^"]*">([^<]+)</h3>', html)


def test_jelajah_menampilkan_semua_produk(client):
    _isi_katalog(client)
    html = client.get("/jelajah").get_data(as_text=True)
    assert "4 produk ditemukan" in html
    assert len(_nama_di_halaman(html)) == 4


def test_jelajah_pencarian_nama_dan_merek(client):
    _isi_katalog(client)
    assert _nama_di_halaman(client.get("/jelajah?q=macbook").get_data(as_text=True)) == ["MacBook Air M4"]
    assert len(_nama_di_halaman(client.get("/jelajah?q=apple").get_data(as_text=True))) == 2


def test_jelajah_persen_tidak_jadi_wildcard(client):
    _isi_katalog(client)
    # "%" harus dicari sebagai teks biasa: hanya produk yang deskripsinya mengandung "100%"
    html = client.get("/jelajah?q=100%25").get_data(as_text=True)
    assert _nama_di_halaman(html) == ["Galaxy Watch 7"]
    html = client.get("/jelajah?q=%25").get_data(as_text=True)
    assert _nama_di_halaman(html) == ["Galaxy Watch 7"]


def test_jelajah_filter_kategori_merek_harga(client):
    _isi_katalog(client)
    assert len(_nama_di_halaman(client.get("/jelajah?kategori=Handphone").get_data(as_text=True))) == 2
    assert _nama_di_halaman(client.get("/jelajah?kategori=Handphone&merek=Xiaomi").get_data(as_text=True)) == ["Redmi Note 14"]
    html = client.get("/jelajah?min=4000000&max=19000000").get_data(as_text=True)
    assert set(_nama_di_halaman(html)) == {"MacBook Air M4", "Redmi Note 14"}
    assert "Filter (2)" in html


def test_jelajah_filter_tidak_valid_diabaikan(client):
    _isi_katalog(client)
    html = client.get("/jelajah?kategori=<script>&merek=Nokia&min=abc&urut=hack").get_data(as_text=True)
    assert len(_nama_di_halaman(html)) == 4
    assert "<script>" not in html


def test_jelajah_urutan_harga(client):
    _isi_katalog(client)
    termurah = _nama_di_halaman(client.get("/jelajah?urut=termurah").get_data(as_text=True))
    assert termurah[0] == "Galaxy Watch 7" and termurah[-1] == "iPhone 16 Pro"
    termahal = _nama_di_halaman(client.get("/jelajah?urut=termahal").get_data(as_text=True))
    assert termahal == list(reversed(termurah))


def test_jelajah_paginasi(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    for i in range(14):
        _tambah(client, nama_produk=f"Produk Uji {i:02d}")
    html1 = client.get("/jelajah").get_data(as_text=True)
    html2 = client.get("/jelajah?page=2").get_data(as_text=True)
    assert len(_nama_di_halaman(html1)) == 12 and len(_nama_di_halaman(html2)) == 2
    assert "Selanjutnya" in html1 and "Sebelumnya" in html2
    # Halaman di luar jangkauan tidak error
    assert client.get("/jelajah?page=99").status_code == 200


def test_jelajah_kosong(client):
    html = client.get("/jelajah?q=tidakadaproduk").get_data(as_text=True)
    assert "Produk tidak ditemukan" in html


def test_detail_produk_dan_produk_terkait(client, app):
    _isi_katalog(client)
    with app.app_context():
        iphone = Produk.query.filter_by(nama_produk="iPhone 16 Pro").one()
    html = client.get(f"/produk/{iphone.id}").get_data(as_text=True)
    assert "iPhone 16 Pro" in html and "Rp 21.999.000" in html
    assert "Produk lain dari Apple" in html and "MacBook Air M4" in html
    assert "Redmi Note 14" not in html


def test_detail_produk_tidak_ada_404(client):
    assert client.get("/produk/9999").status_code == 404


def test_diskon_tampil_di_katalog_dan_detail(client, app):
    _isi_katalog(client)
    with app.app_context():
        redmi = Produk.query.filter_by(nama_produk="Redmi Note 14").one()
        assert redmi.diskon_persen == 14
    assert "-14%" in client.get("/jelajah").get_data(as_text=True)
    html = client.get(f"/produk/{redmi.id}").get_data(as_text=True)
    assert "DISKON 14%" in html and "Rp 4.999.000" in html


def test_harga_normal_harus_lebih_tinggi(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/admin/produk/tambah", data=produk_data(harga="5000000", harga_normal="4000000"),
                       content_type="multipart/form-data")
    assert "Harga normal harus lebih tinggi" in resp.get_data(as_text=True)


def test_beranda_menampilkan_produk_unggulan_diskon(client):
    _isi_katalog(client)
    html = client.get("/").get_data(as_text=True)
    assert "PROMO MINGGU INI" in html
    unggulan = html.split("PROMO MINGGU INI", 1)[1]
    assert unggulan.index("Redmi Note 14") < unggulan.index("Belanja per Kategori")


def test_halaman_profil(client):
    assert client.get("/profil").status_code == 302  # wajib login
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.get("/profil").get_data(as_text=True)
    assert "Budi Santoso" in html and "BS" in html and "Panel Admin" not in html


def test_ubah_nama(client, app):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post("/pengaturan/nama", data={"nama-nama_lengkap": "  Budi   Hartono "})
    assert resp.status_code == 302
    with app.app_context():
        assert User.query.filter_by(username="budi").one().nama_lengkap == "Budi Hartono"
    resp = client.post("/pengaturan/nama", data={"nama-nama_lengkap": "<b>x</b>"})
    assert "Nama hanya boleh" in resp.get_data(as_text=True)


def test_admin_cari_produk(client):
    _isi_katalog(client)
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    html = client.get("/admin/produk?q=galaxy").get_data(as_text=True)
    assert "Galaxy Watch 7" in html and "iPhone 16 Pro" not in html
