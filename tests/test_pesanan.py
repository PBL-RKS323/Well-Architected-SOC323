import io
import os
from datetime import timedelta

import pytest

from conftest import login, produk_data, read_log, PNG_BYTES, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models import db, utcnow
from models.keranjang import KeranjangItem
from models.pesanan import Pesanan
from models.produk import Produk
from models.user import User

ALAMAT = {
    "metode_pengiriman": "kurir",
    "nama_penerima": "Budi Santoso",
    "telepon": "0812-3456-7890",
    "alamat": "Jl. Ahmad Yani No. 10, RT 01/RW 02, Batam Centre",
    "kota": "Kota Batam",
    "kode_pos": "29461",
    "catatan": "",
    "metode_pembayaran": "transfer",
}


@pytest.fixture
def produk_ids(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    for nama, harga, stok in [("iPhone 16 Pro", "20000000", "10"), ("Galaxy Buds 3", "1500000", "2")]:
        client.post("/admin/produk/tambah", data=produk_data(nama_produk=nama, harga=harga, stok=stok),
                    content_type="multipart/form-data")
    client.post("/logout")
    with app.app_context():
        return {p.nama_produk: p.id for p in Produk.query.all()}


@pytest.fixture
def pelanggan(client, produk_ids):
    """Budi login dengan 2 iPhone + 1 Galaxy Buds di keranjang."""
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}", data={"jumlah": "2"})
    client.post(f"/keranjang/tambah/{produk_ids['Galaxy Buds 3']}", data={"jumlah": "1"})
    return client


def _checkout(client, **ubah):
    data = dict(ALAMAT)
    data.update(ubah)
    return client.post("/checkout", data=data)


def _pesanan(app, kode=None):
    with app.app_context():
        q = Pesanan.query
        p = q.filter_by(kode=kode).one() if kode else q.order_by(Pesanan.id.desc()).first()
        db.session.expunge(p) if p else None
        return p


def _stok(app, produk_id):
    with app.app_context():
        return db.session.get(Produk, produk_id).stok


def _buat_pesanan(app, client, **ubah):
    resp = _checkout(client, **ubah)
    assert resp.status_code == 302 and "/konfirmasi" in resp.headers["Location"]
    return _pesanan(app)


def _unggah_bukti(client, kode, data=PNG_BYTES, nama="bukti.png"):
    return client.post(f"/pesanan/{kode}/bayar", data={"bukti": (io.BytesIO(data), nama)},
                       content_type="multipart/form-data")


def _aksi_admin(client, pesanan_id, aksi, **extra):
    return client.post(f"/admin/pesanan/{pesanan_id}/status", data={"aksi": aksi, **extra})


def _jadi_admin(client):
    client.post("/logout")
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)


# --- CHECKOUT ---

def test_checkout_wajib_login(client):
    resp = client.get("/checkout")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    assert "/login" in client.get("/pesanan").headers["Location"]


def test_checkout_keranjang_kosong_kembali_ke_keranjang(client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.get("/checkout")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/keranjang")


def test_halaman_checkout_tampil_dengan_ringkasan(pelanggan):
    html = pelanggan.get("/checkout").get_data(as_text=True)
    assert "Checkout" in html and "Ambil di toko" in html
    assert "Rp\u00a041.500.000" in html  # subtotal 2 x 20jt + 1,5jt
    assert "Rp\u00a015.000" in html      # ongkir flat
    assert 'href="/checkout"' in pelanggan.get("/keranjang").get_data(as_text=True)


def test_checkout_kurir_wajib_alamat(app, pelanggan):
    html = _checkout(pelanggan, alamat="", kota="", kode_pos="abc").get_data(as_text=True)
    assert "Alamat wajib diisi" in html and "Kota wajib diisi" in html and "Kode pos harus 5 digit" in html
    assert _pesanan(app) is None


def test_checkout_nomor_hp_divalidasi(app, pelanggan):
    html = _checkout(pelanggan, telepon="12345").get_data(as_text=True)
    assert "Nomor HP tidak valid" in html
    assert _pesanan(app) is None


def test_checkout_kurir_membuat_pesanan(app, pelanggan, produk_ids):
    p = _buat_pesanan(app, pelanggan)
    assert p.status == Pesanan.MENUNGGU_PEMBAYARAN
    assert p.subtotal == 41500000 and p.ongkir == 15000 and p.total == 41515000
    assert p.telepon == "081234567890"  # spasi & tanda hubung dibuang
    assert p.kode.startswith("ES-")
    # Stok berkurang dan keranjang kosong
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 8
    assert _stok(app, produk_ids["Galaxy Buds 3"]) == 1
    with app.app_context():
        assert KeranjangItem.query.count() == 0
    assert f"ORDER_CREATE" in read_log(app) and p.kode in read_log(app)

    html = pelanggan.get(f"/pesanan/{p.kode}/konfirmasi").get_data(as_text=True)
    assert "Pesanan Berhasil Dibuat" in html and p.kode in html and "Rp\u00a041.515.000" in html


def test_checkout_ambil_di_toko_tanpa_ongkir_dan_alamat(app, pelanggan):
    p = _buat_pesanan(app, pelanggan, metode_pengiriman="ambil", alamat="", kota="", kode_pos="")
    assert p.metode_pengiriman == "ambil" and p.ongkir == 0 and p.total == 41500000
    assert p.alamat is None


def test_checkout_harga_dari_database_bukan_dari_form(app, pelanggan):
    p = _buat_pesanan(app, pelanggan, harga="1", total="1", subtotal="1", ongkir="0")
    assert p.total == 41515000


def test_checkout_dikirim_dua_kali_hanya_satu_pesanan(app, pelanggan, produk_ids):
    _buat_pesanan(app, pelanggan)
    resp = _checkout(pelanggan)  # klik kedua: keranjang sudah kosong
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/keranjang")
    with app.app_context():
        assert Pesanan.query.count() == 1
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 8  # stok hanya terpotong sekali


def test_batas_pesanan_menghitung_yang_menunggu_verifikasi(app, client, produk_ids):
    """Batas tidak bisa diakali dengan mengunggah bukti palsu agar status pindah ke verifikasi."""
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for _ in range(app.config["MAKS_PESANAN_BELUM_BAYAR"]):
        client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
        p = _buat_pesanan(app, client)
        _unggah_bukti(client, p.kode)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    resp = _checkout(client)
    assert resp.headers["Location"].endswith("/pesanan")
    with app.app_context():
        assert Pesanan.query.count() == app.config["MAKS_PESANAN_BELUM_BAYAR"]


def test_checkout_ditolak_jika_stok_berubah(app, pelanggan, produk_ids):
    with app.app_context():
        db.session.get(Produk, produk_ids["iPhone 16 Pro"]).stok = 1  # stok turun setelah masuk keranjang
        db.session.commit()
    resp = _checkout(pelanggan)
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/keranjang")
    assert _pesanan(app) is None
    assert _stok(app, produk_ids["Galaxy Buds 3"]) == 2  # tidak ada stok yang terpotong


def test_batas_pesanan_belum_dibayar(app, client, produk_ids):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for _ in range(app.config["MAKS_PESANAN_BELUM_BAYAR"]):
        client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
        _buat_pesanan(app, client)
    client.post(f"/keranjang/tambah/{produk_ids['iPhone 16 Pro']}")
    resp = _checkout(client)
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/pesanan")
    with app.app_context():
        assert Pesanan.query.count() == app.config["MAKS_PESANAN_BELUM_BAYAR"]


# --- PESANAN SAYA ---

def test_pesanan_saya_daftar_cari_dan_tab(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    html = pelanggan.get("/pesanan").get_data(as_text=True)
    assert p.kode in html and "Menunggu Pembayaran" in html
    assert p.kode in pelanggan.get("/pesanan?q=galaxy").get_data(as_text=True)
    assert p.kode not in pelanggan.get("/pesanan?q=macbook").get_data(as_text=True)
    assert p.kode not in pelanggan.get("/pesanan?tab=selesai").get_data(as_text=True)
    assert pelanggan.get("/pesanan?tab=ngawur&q=%25").status_code == 200


def test_pesanan_orang_lain_tidak_bisa_dibuka(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    pelanggan.post("/logout")
    pelanggan.post("/register", data={"nama_lengkap": "Siti Aminah", "email": "siti@tokoelektronik.id",
                                      "password": "Siti12345!", "confirm_password": "Siti12345!", "setuju": "y"})
    login(pelanggan, "siti@tokoelektronik.id", "Siti12345!")
    for url in [f"/pesanan/{p.kode}", f"/pesanan/{p.kode}/konfirmasi", f"/pesanan/{p.kode}/bukti"]:
        assert pelanggan.get(url).status_code == 404
    assert pelanggan.post(f"/pesanan/{p.kode}/batal").status_code == 404
    assert _unggah_bukti(pelanggan, p.kode).status_code == 404
    assert _pesanan(app, p.kode).status == Pesanan.MENUNGGU_PEMBAYARAN
    assert "ACCESS_DENIED" in read_log(app) and "resource=pesanan" in read_log(app)
    assert p.kode not in pelanggan.get("/pesanan").get_data(as_text=True)


def test_pelanggan_batalkan_pesanan_stok_kembali(app, pelanggan, produk_ids):
    p = _buat_pesanan(app, pelanggan)
    pelanggan.post(f"/pesanan/{p.kode}/batal")
    assert _pesanan(app, p.kode).status == Pesanan.DIBATALKAN
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 10
    assert _stok(app, produk_ids["Galaxy Buds 3"]) == 2
    # Membatalkan dua kali tidak mengembalikan stok dua kali
    pelanggan.post(f"/pesanan/{p.kode}/batal")
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 10


def test_pesanan_kedaluwarsa_batal_otomatis(app, pelanggan, produk_ids):
    p = _buat_pesanan(app, pelanggan)
    with app.app_context():
        db.session.get(Pesanan, p.id).batas_bayar = utcnow() - timedelta(minutes=1)
        db.session.commit()
    html = pelanggan.get("/pesanan").get_data(as_text=True)
    assert "Dibatalkan" in html
    assert _pesanan(app, p.kode).status == Pesanan.DIBATALKAN
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 10


# --- BUKTI BAYAR ---

def test_unggah_bukti_bayar_disimpan_privat(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode)
    p = _pesanan(app, p.kode)
    assert p.status == Pesanan.MENUNGGU_VERIFIKASI and p.bukti_bayar
    # File ada di folder privat, bukan di static/uploads
    assert os.path.isfile(os.path.join(app.config["BUKTI_BAYAR_FOLDER"], p.bukti_bayar))
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], p.bukti_bayar))
    assert pelanggan.get(f"/static/uploads/{p.bukti_bayar}").status_code == 404
    resp = pelanggan.get(f"/pesanan/{p.kode}/bukti")
    assert resp.status_code == 200 and resp.data == PNG_BYTES
    assert "no-store" in resp.headers["Cache-Control"]
    assert "PAYMENT_PROOF_UPLOADED" in read_log(app)
    # Setelah terkirim, pelanggan tidak bisa membatalkan sendiri
    pelanggan.post(f"/pesanan/{p.kode}/batal")
    assert _pesanan(app, p.kode).status == Pesanan.MENUNGGU_VERIFIKASI


def test_unggah_bukti_berbahaya_ditolak(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode, data=b"<?php system($_GET['c']); ?>", nama="bukti.png")
    _unggah_bukti(pelanggan, p.kode, data=PNG_BYTES, nama="shell.php")
    p = _pesanan(app, p.kode)
    assert p.status == Pesanan.MENUNGGU_PEMBAYARAN and p.bukti_bayar is None
    assert "UPLOAD_REJECTED" in read_log(app)


# --- ADMIN ---

def test_customer_tidak_bisa_akses_admin_pesanan(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    assert pelanggan.get("/admin/pesanan").status_code == 302
    _aksi_admin(pelanggan, p.id, "batal", alasan="iseng")
    assert _pesanan(app, p.kode).status == Pesanan.MENUNGGU_PEMBAYARAN
    assert "ACCESS_DENIED" in read_log(app)


def test_admin_verifikasi_lalu_kirim_lalu_pelanggan_terima(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode)
    _jadi_admin(pelanggan)

    html = pelanggan.get("/admin/pesanan?tab=verifikasi").get_data(as_text=True)
    assert p.kode in html
    assert pelanggan.get(f"/pesanan/{p.kode}/bukti").status_code == 200  # admin boleh melihat bukti

    _aksi_admin(pelanggan, p.id, "terima")
    assert _pesanan(app, p.kode).status == Pesanan.DIPROSES
    _aksi_admin(pelanggan, p.id, "kirim", nomor_resi="JNE1234567890")
    p = _pesanan(app, p.kode)
    assert p.status == Pesanan.DIKIRIM and p.nomor_resi == "JNE1234567890"
    assert "PAYMENT_VERIFIED" in read_log(app)

    pelanggan.post("/logout")
    login(pelanggan, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = pelanggan.get(f"/pesanan/{p.kode}").get_data(as_text=True)
    assert "JNE1234567890" in html and "Pesanan Sudah Diterima" in html
    pelanggan.post(f"/pesanan/{p.kode}/terima")
    assert _pesanan(app, p.kode).status == Pesanan.SELESAI


def test_resi_dibuat_otomatis_jika_kosong(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode)
    _jadi_admin(pelanggan)
    _aksi_admin(pelanggan, p.id, "terima")
    _aksi_admin(pelanggan, p.id, "kirim")  # tanpa nomor resi
    resi = _pesanan(app, p.kode).nomor_resi
    assert resi.startswith("JJN") and len(resi) == 13 and resi[3:].isdigit()


def test_admin_tolak_bukti_wajib_alasan_dan_pelanggan_unggah_ulang(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode)
    _jadi_admin(pelanggan)

    _aksi_admin(pelanggan, p.id, "tolak")  # tanpa alasan
    assert _pesanan(app, p.kode).status == Pesanan.MENUNGGU_VERIFIKASI
    _aksi_admin(pelanggan, p.id, "tolak", alasan="Nominal transfer tidak sesuai")
    p = _pesanan(app, p.kode)
    assert p.status == Pesanan.MENUNGGU_PEMBAYARAN and p.alasan_tolak == "Nominal transfer tidak sesuai"
    assert "PAYMENT_REJECTED" in read_log(app)

    pelanggan.post("/logout")
    login(pelanggan, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert "Nominal transfer tidak sesuai" in pelanggan.get(f"/pesanan/{p.kode}").get_data(as_text=True)
    lama = p.bukti_bayar
    _unggah_bukti(pelanggan, p.kode)
    p = _pesanan(app, p.kode)
    assert p.status == Pesanan.MENUNGGU_VERIFIKASI and p.bukti_bayar != lama and p.alasan_tolak is None
    assert not os.path.exists(os.path.join(app.config["BUKTI_BAYAR_FOLDER"], lama))  # bukti lama dihapus


def test_admin_transisi_tidak_sah_ditolak(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    _jadi_admin(pelanggan)
    for aksi in ["terima", "kirim", "selesai", "hapus_semua"]:
        _aksi_admin(pelanggan, p.id, aksi)
        assert _pesanan(app, p.kode).status == Pesanan.MENUNGGU_PEMBAYARAN
    assert "ORDER_INVALID_TRANSITION" in read_log(app)


def test_admin_ambil_di_toko_pakai_siap_diambil(app, pelanggan):
    p = _buat_pesanan(app, pelanggan, metode_pengiriman="ambil", alamat="", kota="", kode_pos="")
    _unggah_bukti(pelanggan, p.kode)
    _jadi_admin(pelanggan)
    _aksi_admin(pelanggan, p.id, "terima")
    _aksi_admin(pelanggan, p.id, "kirim")  # salah tombol untuk pesanan ambil di toko
    assert _pesanan(app, p.kode).status == Pesanan.DIPROSES
    _aksi_admin(pelanggan, p.id, "siap_diambil")
    assert _pesanan(app, p.kode).status == Pesanan.SIAP_DIAMBIL
    _aksi_admin(pelanggan, p.id, "selesai")
    assert _pesanan(app, p.kode).status == Pesanan.SELESAI


def test_admin_batalkan_pesanan_stok_kembali(app, pelanggan, produk_ids):
    p = _buat_pesanan(app, pelanggan)
    _unggah_bukti(pelanggan, p.kode)
    _jadi_admin(pelanggan)
    _aksi_admin(pelanggan, p.id, "terima")
    _aksi_admin(pelanggan, p.id, "batal", alasan="Barang rusak di gudang")
    assert _pesanan(app, p.kode).status == Pesanan.DIBATALKAN
    assert _stok(app, produk_ids["iPhone 16 Pro"]) == 10
    assert "ORDER_CANCELLED" in read_log(app)


def test_dashboard_pendapatan_hanya_dari_pesanan_lunas(app, pelanggan, produk_ids):
    p1 = _buat_pesanan(app, pelanggan)  # tetap belum dibayar
    pelanggan.post(f"/keranjang/tambah/{produk_ids['Galaxy Buds 3']}")
    p2 = _buat_pesanan(app, pelanggan, metode_pengiriman="ambil", alamat="", kota="", kode_pos="")
    _unggah_bukti(pelanggan, p2.kode)
    _jadi_admin(pelanggan)
    _aksi_admin(pelanggan, p2.id, "terima")

    html = pelanggan.get("/admin").get_data(as_text=True)
    assert "Rp\u00a01.500.000" in html          # pendapatan = pesanan lunas saja
    assert "Rp\u00a041.515.000" in html          # p1 tampil di Pesanan Terbaru
    assert p1.kode in html and p2.kode in html
    assert "Galaxy Buds 3" in html          # produk terlaris


def test_produk_dihapus_riwayat_pesanan_tetap_ada(app, pelanggan, produk_ids):
    p = _buat_pesanan(app, pelanggan)
    _jadi_admin(pelanggan)
    pelanggan.post(f"/admin/produk/{produk_ids['Galaxy Buds 3']}/hapus")
    html = pelanggan.get(f"/admin/pesanan/{p.id}").get_data(as_text=True)
    assert "Galaxy Buds 3" in html and "produk sudah dihapus" in html


def test_beli_lagi_menambah_ke_keranjang(app, pelanggan):
    p = _buat_pesanan(app, pelanggan)
    pelanggan.post(f"/pesanan/{p.kode}/batal")
    pelanggan.post(f"/pesanan/{p.kode}/beli-lagi")
    with app.app_context():
        user = User.query.filter_by(username="budi").one()
        isi = {i.produk.nama_produk: i.jumlah for i in KeranjangItem.query.filter_by(user_id=user.id)}
    assert isi == {"iPhone 16 Pro": 2, "Galaxy Buds 3": 1}
