"""Pengujian QA untuk verifikasi komponen footer partner dan katalog toko.
Dikelola oleh tim Quality Assurance (Ripasha).
"""


def test_beranda_memuat_partner_pembayaran_dan_pengiriman(client):
    """Memastikan bagian footer merender badge partner pembayaran dan pengiriman dengan benar."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Verifikasi metode pembayaran
    assert "Metode Pembayaran" in html
    assert "BCA" in html
    assert "Mandiri" in html
    assert "QRIS" in html

    # Verifikasi jasa pengiriman
    assert "Jasa Pengiriman" in html
    assert "SPX Express" in html
    assert "J&amp;T Express" in html
    assert "JNE" in html


def test_katalog_publik_aksesibilitas(client):
    """Memastikan halaman jelajah dan katalog merespons dengan status 200 tanpa galat."""
    resp = client.get("/jelajah")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Kategori" in html
    assert "Merek" in html
