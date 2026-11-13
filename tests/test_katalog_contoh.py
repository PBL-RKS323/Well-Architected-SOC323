import os

from models import db
from models.produk import Produk

JUMLAH = 17  # produk di seed/katalog.json


def test_seed_katalog_mengisi_produk_dan_tidak_dobel(app):
    runner = app.test_cli_runner()
    hasil = runner.invoke(args=["seed-katalog"])
    assert f"{JUMLAH} produk contoh ditambahkan" in hasil.output
    with app.app_context():
        assert Produk.query.count() == JUMLAH
        assert {p.kategori for p in Produk.query} == set(Produk.KATEGORI)  # semua kategori terisi
        produk = Produk.query.filter_by(nama_produk="Galaksi Watch 7 44mm").one()
        # Foto disimpan dengan nama acak di folder upload (lewat validasi gambar yang sama)
        assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], produk.gambar))
        assert produk.gambar != "galaxy-watch-7.jpg"

    hasil = runner.invoke(args=["seed-katalog"])
    assert "0 produk contoh ditambahkan, 0 foto diperbarui" in hasil.output
    with app.app_context():
        assert db.session.query(Produk).count() == JUMLAH


def test_seed_katalog_perbarui_foto_tanpa_mengubah_harga(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["seed-katalog"])
    with app.app_context():
        produk = Produk.query.filter_by(nama_produk="Galaksi Watch 7 44mm").one()
        foto_lama, produk.harga = produk.gambar, 1  # admin mengubah harga
        db.session.commit()

    hasil = runner.invoke(args=["seed-katalog", "--perbarui-foto"])
    assert f"0 produk contoh ditambahkan, {JUMLAH} foto diperbarui" in hasil.output
    with app.app_context():
        produk = Produk.query.filter_by(nama_produk="Galaksi Watch 7 44mm").one()
        assert produk.gambar != foto_lama and produk.harga == 1
        assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], foto_lama))  # foto lama dihapus


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
