import os

from models import db
from models.produk import Produk


def test_seed_katalog_mengisi_produk_dan_tidak_dobel(app):
    runner = app.test_cli_runner()
    hasil = runner.invoke(args=["seed-katalog"])
    assert "8 produk contoh ditambahkan" in hasil.output
    with app.app_context():
        assert Produk.query.count() == 8
        produk = Produk.query.filter_by(nama_produk="Galaxy Watch 7 44mm").one()
        # Foto disimpan dengan nama acak di folder upload (lewat validasi gambar yang sama)
        assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], produk.gambar))
        assert produk.gambar != "galaxy-watch-7.jpg"

    hasil = runner.invoke(args=["seed-katalog"])
    assert "0 produk contoh ditambahkan" in hasil.output
    with app.app_context():
        assert db.session.query(Produk).count() == 8


def test_halaman_kredit_foto_publik(client):
    resp = client.get("/kredit-foto")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Wikimedia Commons" in html and "CC BY-SA 4.0" in html and "Galaxy S24 Ultra" in html
    assert 'href="/kredit-foto"' in client.get("/").get_data(as_text=True)


def test_menu_bawah_tamu_tanpa_pesanan(client):
    html = client.get("/").get_data(as_text=True)
    assert ">Masuk<" in html and ">Pesanan<" not in html
    assert "Kembali ke toko" in client.get("/login").get_data(as_text=True)
