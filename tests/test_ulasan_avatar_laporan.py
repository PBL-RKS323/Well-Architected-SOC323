import csv
import io
import os
from datetime import date, timedelta

from PIL import Image
from werkzeug.datastructures import MultiDict

from conftest import login, read_log, produk_data, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from controllers.admin_laporan_controller import baca_rentang, MAKS_RENTANG_HARI
from models import db, utcnow
from models.pesanan import Pesanan, PesananItem
from models.produk import Produk
from models.ulasan import Ulasan
from models.user import User

STAF_PASSWORD = "StafToko123!"


def _id_user(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).one().id


def _produk(app, client, **ubah):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(**ubah), content_type="multipart/form-data")
    client.post("/logout")
    with app.app_context():
        return Produk.query.order_by(Produk.id.desc()).first().id


def _pesanan(app, user_id, produk_id, status=Pesanan.SELESAI, total=1000000, jumlah=1, created_at=None, **kolom):
    """Pesanan langsung di database (alur checkout sendiri sudah diuji di test_pesanan.py)."""
    with app.app_context():
        p = Pesanan(kode=Pesanan.buat_kode(), user_id=user_id, status=status, metode_pengiriman=Pesanan.KURIR,
                    nama_penerima="Budi Santoso", telepon="081234567890", subtotal=total - 15000, ongkir=15000,
                    total=total, batas_bayar=utcnow() + timedelta(hours=24), created_at=created_at or utcnow(),
                    **kolom)
        p.items.append(PesananItem(produk_id=produk_id, nama_produk="Galaxy S25 Ultra", merek="Samsung",
                                   harga=(total - 15000) // jumlah, jumlah=jumlah))
        db.session.add(p)
        db.session.commit()
        return p.id


def _staf(app):
    with app.app_context():
        u = User(username="staf", nama_lengkap="Staf Toko", email="staf@tokoelektronik.id", role=User.ROLE_STAF)
        u.set_password(STAF_PASSWORD)
        db.session.add(u)
        db.session.commit()


def _foto(fmt="JPEG", ukuran=(800, 600), exif=True):
    buf = io.BytesIO()
    img = Image.new("RGB", ukuran, (26, 104, 209))
    if exif and fmt == "JPEG":
        data_exif = Image.Exif()
        data_exif[0x010F] = "HP Rahasia"  # Make
        data_exif[0x8825] = {2: (1, 8, 0)}  # GPSInfo: lintang
        img.save(buf, fmt, exif=data_exif)
    else:
        img.save(buf, fmt)
    buf.seek(0)
    return buf


# ===== AVATAR (#9) =====

def test_upload_avatar_diencode_ulang_tanpa_exif(app, client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post("/pengaturan/foto", data={"foto-avatar": (_foto(), "selfie.jpg")},
                       content_type="multipart/form-data")
    assert resp.status_code == 302
    with app.app_context():
        nama = db.session.get(User, _id_user(app, "budi")).avatar
    path = os.path.join(app.config["UPLOAD_FOLDER"], "avatar", nama)
    with Image.open(path) as img:
        assert img.size == (256, 256) and img.format == "JPEG"
        assert not img.getexif()  # lokasi GPS & tipe HP ikut terbuang
    assert "selfie" not in nama
    assert "AVATAR_CHANGED" in read_log(app)
    assert f"uploads/avatar/{nama}" in client.get("/profil").get_data(as_text=True)

    # Ganti foto: file lama ikut dihapus
    client.post("/pengaturan/foto", data={"foto-avatar": (_foto("PNG", exif=False), "baru.png")},
                content_type="multipart/form-data")
    assert not os.path.exists(path)


def test_upload_avatar_palsu_ditolak(app, client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.post("/pengaturan/foto", data={"foto-avatar": (io.BytesIO(b"<?php system($_GET['c']); ?>"), "shell.png")},
                       content_type="multipart/form-data").get_data(as_text=True)
    assert "File ditolak" in html
    with app.app_context():
        assert db.session.get(User, _id_user(app, "budi")).avatar is None
    assert "target=avatar" in read_log(app)


def test_hapus_avatar(app, client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post("/pengaturan/foto", data={"foto-avatar": (_foto(), "a.jpg")}, content_type="multipart/form-data")
    with app.app_context():
        nama = db.session.get(User, _id_user(app, "budi")).avatar
    client.post("/pengaturan/foto/hapus")
    with app.app_context():
        assert db.session.get(User, _id_user(app, "budi")).avatar is None
    assert not os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], "avatar", nama))


# ===== ULASAN (#7, #8) =====

def test_ulasan_hanya_untuk_pembeli_pesanan_selesai(app, client):
    produk_id = _produk(app, client)
    budi = _id_user(app, "budi")
    _pesanan(app, budi, produk_id, status=Pesanan.DIKIRIM)  # belum diterima
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)

    assert "setelah membeli produk ini" in client.get(f"/produk/{produk_id}").get_data(as_text=True)
    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5", "komentar": "Mantap"})
    with app.app_context():
        assert Ulasan.query.count() == 0
    assert "REVIEW_REJECTED" in read_log(app)


def test_tulis_lalu_ubah_ulasan(app, client):
    produk_id = _produk(app, client)
    _pesanan(app, _id_user(app, "budi"), produk_id)
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)

    resp = client.post(f"/produk/{produk_id}/ulasan", data={"rating": "4", "komentar": "Baterai awet seharian."})
    assert resp.status_code == 302 and resp.headers["Location"].endswith("#ulasan")
    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5", "komentar": "Setelah update makin bagus."})
    with app.app_context():
        u = Ulasan.query.one()  # satu ulasan per pembeli, yang kedua mengubah
        assert u.rating == 5 and u.komentar == "Setelah update makin bagus."

    html = client.get(f"/produk/{produk_id}").get_data(as_text=True)
    assert "Setelah update makin bagus." in html and "(1 ulasan)" in html and "Ubah Ulasanmu" in html
    assert "REVIEW_CREATE" in read_log(app) and "REVIEW_UPDATE" in read_log(app)


def test_ulasan_xss_di_escape_dan_rating_divalidasi(app, client):
    produk_id = _produk(app, client)
    _pesanan(app, _id_user(app, "budi"), produk_id)
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)

    assert client.post(f"/produk/{produk_id}/ulasan", data={"rating": "9"}).status_code == 400
    assert client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5", "komentar": "x" * 1001}).status_code == 400
    with app.app_context():
        assert Ulasan.query.count() == 0

    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "1", "komentar": "<script>alert(1)</script>"})
    html = client.get(f"/produk/{produk_id}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_tamu_dan_admin_tidak_bisa_menulis_ulasan(app, client):
    produk_id = _produk(app, client)
    resp = client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5"})
    assert "/login" in resp.headers["Location"]
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5"})
    with app.app_context():
        assert Ulasan.query.count() == 0


def test_staf_balas_dan_hapus_ulasan_pelanggan_tidak_bisa(app, client):
    produk_id = _produk(app, client)
    _pesanan(app, _id_user(app, "budi"), produk_id)
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "2", "komentar": "Pengiriman lama."})
    with app.app_context():
        ulasan_id = Ulasan.query.one().id
    assert client.get("/admin/ulasan").status_code == 302  # pelanggan tidak masuk panel
    client.post(f"/admin/ulasan/{ulasan_id}/hapus")
    with app.app_context():
        assert Ulasan.query.count() == 1
    client.post("/logout")

    _staf(app)
    login(client, "staf@tokoelektronik.id", STAF_PASSWORD)
    assert "Pengiriman lama." in client.get("/admin/ulasan?filter=belum_dibalas").get_data(as_text=True)
    client.post(f"/admin/ulasan/{ulasan_id}/balas", data={"balasan": "Mohon maaf, kurir sedang padat."})
    assert "Mohon maaf, kurir sedang padat." in client.get(f"/produk/{produk_id}").get_data(as_text=True)
    assert "Pengiriman lama." not in client.get("/admin/ulasan?filter=belum_dibalas").get_data(as_text=True)

    client.post(f"/admin/ulasan/{ulasan_id}/hapus")
    with app.app_context():
        assert Ulasan.query.count() == 0
    log = read_log(app)
    assert "REVIEW_REPLY" in log and "by=staff" in log


def test_hapus_ulasan_sendiri_dan_ikut_terhapus_bersama_produk(app, client):
    produk_id = _produk(app, client)
    lain_id = _produk(app, client, nama_produk="iPhone 16")
    budi = _id_user(app, "budi")
    _pesanan(app, budi, produk_id)
    _pesanan(app, budi, lain_id)
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post(f"/produk/{produk_id}/ulasan", data={"rating": "5"})
    client.post(f"/produk/{lain_id}/ulasan", data={"rating": "4"})
    client.post(f"/produk/{produk_id}/ulasan/hapus")
    with app.app_context():
        assert [u.produk_id for u in Ulasan.query.all()] == [lain_id]
    client.post("/logout")

    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post(f"/admin/produk/{lain_id}/hapus")
    with app.app_context():
        assert Ulasan.query.count() == 0


def test_pesanan_selesai_menampilkan_tautan_beri_ulasan(app, client):
    produk_id = _produk(app, client)
    pesanan_id = _pesanan(app, _id_user(app, "budi"), produk_id)
    with app.app_context():
        kode = db.session.get(Pesanan, pesanan_id).kode
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert "Beri ulasan" in client.get(f"/pesanan/{kode}").get_data(as_text=True)


# ===== LAPORAN TRANSAKSI (#3) =====

def test_laporan_hanya_admin(app, client):
    _staf(app)
    login(client, "staf@tokoelektronik.id", STAF_PASSWORD)
    resp = client.get("/admin/laporan")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/admin")
    assert client.get("/admin/laporan/csv").status_code == 302
    assert "Total Pendapatan" not in client.get("/admin").get_data(as_text=True)  # staf tidak melihat keuangan
    assert "permission=lihat_laporan" in read_log(app)
    client.post("/logout")
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert client.get("/admin/laporan").headers["Location"].endswith("/")


def test_laporan_menghitung_hanya_pesanan_lunas_di_rentang(app, client):
    produk_id = _produk(app, client)
    budi = _id_user(app, "budi")
    _pesanan(app, budi, produk_id, status=Pesanan.SELESAI, total=2015000, jumlah=2)
    _pesanan(app, budi, produk_id, status=Pesanan.DIPROSES, total=1015000)
    _pesanan(app, budi, produk_id, status=Pesanan.DIBATALKAN, total=9015000)
    _pesanan(app, budi, produk_id, status=Pesanan.MENUNGGU_PEMBAYARAN, total=5015000)
    _pesanan(app, budi, produk_id, status=Pesanan.SELESAI, total=7015000, created_at=utcnow() - timedelta(days=400))

    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    html = client.get("/admin/laporan?preset=30hari").get_data(as_text=True)
    assert "Rp 3.030.000" in html            # 2.015.000 + 1.015.000 (batal, belum bayar & lama tidak dihitung)
    assert "dari 4 pesanan (50%)" in html
    assert "Rp 1.515.000" in html            # rata-rata per pesanan lunas
    assert "Galaxy S25 Ultra" in html


def test_ekspor_csv_aman_dari_formula_injection(app, client):
    produk_id = _produk(app, client)
    _pesanan(app, _id_user(app, "budi"), produk_id, kota='=HYPERLINK("http://jahat.example","klik")')
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)

    resp = client.get("/admin/laporan/csv?preset=7hari")
    assert resp.mimetype == "text/csv" and "attachment" in resp.headers["Content-Disposition"]
    assert resp.headers["Cache-Control"] == "no-store"
    teks = resp.get_data(as_text=True)
    assert teks.startswith("﻿")
    baris = list(csv.reader(io.StringIO(teks.lstrip("﻿"))))
    assert baris[0][0] == "Kode Pesanan" and len(baris) == 2
    assert baris[1][6].startswith("'=HYPERLINK")  # dianggap teks oleh Excel, bukan rumus
    assert baris[1][10] == "1000000"
    assert "REPORT_EXPORTED" in read_log(app) and "rows=1" in read_log(app)


def test_baca_rentang_tanggal(app):
    with app.test_request_context():
        dari, sampai, preset = baca_rentang(MultiDict({"dari": "2026-10-10", "sampai": "2026-10-01"}))
        assert (dari, sampai, preset) == (date(2026, 10, 1), date(2026, 10, 10), None)  # tertukar dibetulkan

        dari, sampai, _ = baca_rentang(MultiDict({"dari": "2020-01-01", "sampai": "2026-10-01"}))
        assert (sampai - dari).days == MAKS_RENTANG_HARI - 1  # dibatasi 1 tahun

        dari, sampai, preset = baca_rentang(MultiDict({"dari": "bukan-tanggal", "sampai": "2026-10-01'--"}))
        assert preset == "bulan_ini" and dari.day == 1
