"""Detail produk: spesifikasi, garansi, hemat, breadcrumb, dan tab informasi produk."""
from decimal import Decimal

from conftest import login, produk_data, ADMIN_PASSWORD
from models import db
from models.produk import Produk

SPEK = "  Prosesor: Intel Core i5-1235U  \n\nRAM: 16GB DDR4\nPenyimpanan: SSD 512GB\nBonus tas laptop\n"


def _tambah(client, **data):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    return client.post("/admin/produk/tambah", data=produk_data(**data), content_type="multipart/form-data")


def _produk(app, nama="Galaxy S25 Ultra"):
    with app.app_context():
        return db.session.query(Produk).filter_by(nama_produk=nama).one()


def test_spesifikasi_dirapikan_dan_diurai(client, app):
    _tambah(client, nama_produk="ThinkPad T14 Gen 3", merek="Lenovo", kategori="Laptop",
            spesifikasi=SPEK, garansi="  Garansi resmi Lenovo 1 tahun ")
    p = _produk(app, "ThinkPad T14 Gen 3")
    # Spasi di tepi & baris kosong dibuang saat disimpan
    assert p.spesifikasi == "Prosesor: Intel Core i5-1235U\nRAM: 16GB DDR4\nPenyimpanan: SSD 512GB\nBonus tas laptop"
    assert p.garansi == "Garansi resmi Lenovo 1 tahun"
    assert p.daftar_spesifikasi == [("Prosesor", "Intel Core i5-1235U"), ("RAM", "16GB DDR4"),
                                    ("Penyimpanan", "SSD 512GB"), ("", "Bonus tas laptop")]
    assert p.ringkasan_spesifikasi == "Intel Core i5-1235U · 16GB DDR4 · SSD 512GB"


def test_spesifikasi_kosong_disimpan_null(client, app):
    _tambah(client, spesifikasi="\n  \n", garansi="")
    p = _produk(app)
    assert p.spesifikasi is None and p.garansi is None
    assert p.daftar_spesifikasi == [] and p.ringkasan_spesifikasi == ""


def test_spesifikasi_terlalu_panjang_ditolak(client, app):
    resp = _tambah(client, spesifikasi="\n".join(f"Baris {i}: nilai" for i in range(31)))
    assert "maksimal 30 baris" in resp.get_data(as_text=True)
    resp = _tambah(client, spesifikasi="Catatan: " + "x" * 150)
    assert "maksimal 150 karakter" in resp.get_data(as_text=True)
    with app.app_context():
        assert db.session.query(Produk).count() == 0


def test_hemat_hanya_saat_diskon():
    assert Produk(harga=Decimal(900), harga_normal=Decimal(1000)).hemat == Decimal(100)
    assert Produk(harga=Decimal(900), harga_normal=None).hemat == 0


def test_halaman_detail_menampilkan_info_lengkap(client, app):
    _tambah(client, harga="15000000", harga_normal="17000000", spesifikasi=SPEK, garansi="Garansi resmi 1 tahun")
    p = _produk(app)
    client.post("/logout")
    html = client.get(f"/produk/{p.id}").get_data(as_text=True)
    assert 'aria-label="Breadcrumb"' in html and 'href="/jelajah?kategori=Handphone"' in html
    assert "Intel Core i5-1235U · 16GB DDR4 · SSD 512GB" in html          # ringkasan di bawah nama
    assert "Hemat Rp 2.000.000" in html
    assert 'role="tablist"' in html and 'id="panel-spesifikasi"' in html
    assert ">Penyimpanan</th>" in html and "SSD 512GB" in html             # tabel spesifikasi
    assert "Garansi resmi 1 tahun" in html


def test_spesifikasi_di_escape(client, app):
    """Isi spesifikasi berasal dari input admin; tetap di-escape agar tidak bisa menyisipkan script (XSS)."""
    _tambah(client, spesifikasi="Catatan: <script>alert(1)</script>")
    html = client.get(f"/produk/{_produk(app).id}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_detail_tanpa_spesifikasi_tetap_rapi(client, app):
    _tambah(client)
    html = client.get(f"/produk/{_produk(app).id}").get_data(as_text=True)
    assert "Spesifikasi lengkap belum diisi" in html
    assert ">Merek</th>" in html and "Garansi mengikuti ketentuan resmi Samsung" in html
    assert "Hemat" not in html


def test_seed_melengkapi_spesifikasi_tanpa_menimpa_isian_admin(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["seed-katalog"])
    with app.app_context():
        watch = Produk.query.filter_by(nama_produk="Galaxy Watch 7 44mm").one()
        assert "Chip: Exynos W1000" in watch.spesifikasi and watch.garansi
        # Simulasi data lama sebelum fitur ini: spesifikasi kosong, dan satu produk sudah diisi admin
        Produk.query.update({"spesifikasi": None, "garansi": None})
        watch.spesifikasi = "Warna: Hijau"
        db.session.commit()

    hasil = runner.invoke(args=["seed-katalog"])
    assert "0 produk contoh ditambahkan, 0 foto diperbarui, 17 produk dilengkapi" in hasil.output
    with app.app_context():
        assert Produk.query.filter_by(nama_produk="Galaxy Watch 7 44mm").one().spesifikasi == "Warna: Hijau"
        assert Produk.query.filter(Produk.spesifikasi.is_(None)).count() == 0
