"""Pengujian unit dan integrasi kupon diskon & validasi checkout.
Disusun oleh: Ripasha Alvarisi (QA Engineer)
"""
from decimal import Decimal
import unittest
from datetime import timedelta
from app import create_app
from config import TestConfig
from models import db, utcnow
from models.user import User
from models.produk import Produk
from models.kupon import Kupon
from models.pesanan import Pesanan
from models.keranjang import KeranjangItem
from models.pembayaran import Pembayaran


class TestKuponCheckout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Buat user customer
        self.user = User(username="qa_kupon_user", email="qa_kupon@soc323.id", role=User.ROLE_CUSTOMER)
        self.user.set_password("QaPass123#")
        db.session.add(self.user)

        # Buat produk
        self.prod = Produk(nama_produk="Kupon Phone", merek="Apple", kategori="Handphone", harga=10000000, stok=10, gambar="phone.jpg")
        db.session.add(self.prod)

        # Buat master kupon persen
        self.kupon_persen = Kupon(
            kode="QADISKON20",
            tipe=Kupon.TIPE_PERSEN,
            nilai=Decimal("20.00"),
            min_belanja=Decimal("500000"),
            maks_potongan=Decimal("2000000"),
            kuota=10,
            terpakai=0,
            aktif=True
        )
        # Buat kupon nominal
        self.kupon_nominal = Kupon(
            kode="QAPOTONGAN50K",
            tipe=Kupon.TIPE_NOMINAL,
            nilai=Decimal("50000.00"),
            min_belanja=Decimal("100000"),
            kuota=5,
            terpakai=0,
            aktif=True
        )
        # Buat kupon kedaluwarsa
        self.kupon_kadaluarsa = Kupon(
            kode="QAEXPIRED",
            tipe=Kupon.TIPE_PERSEN,
            nilai=Decimal("10.00"),
            berlaku_sampai=utcnow() - timedelta(days=1),
            aktif=True
        )
        db.session.add_all([self.kupon_persen, self.kupon_nominal, self.kupon_kadaluarsa])
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        Pesanan.query.delete()
        KeranjangItem.query.delete()
        Kupon.query.delete()
        Produk.query.delete()
        User.query.delete()
        db.session.commit()
        self.ctx.pop()

    def test_hitung_diskon_persentase(self):
        """Verifikasi perhitungan diskon kupon tipe persentase dan batas maksimal potongan."""
        subtotal = Decimal("1000000")  # 20% = 200.000
        diskon = self.kupon_persen.hitung_diskon(subtotal)
        self.assertEqual(diskon, Decimal("200000.00"))

        # Melebihi batas maksimal potongan 2.000.000
        subtotal_besar = Decimal("20000000")  # 20% = 4.000.000 -> dipotong maks 2.000.000
        diskon_maks = self.kupon_persen.hitung_diskon(subtotal_besar)
        self.assertEqual(diskon_maks, Decimal("2000000.00"))

    def test_hitung_diskon_nominal(self):
        """Verifikasi perhitungan diskon kupon tipe nominal flat."""
        subtotal = Decimal("500000")
        diskon = self.kupon_nominal.hitung_diskon(subtotal)
        self.assertEqual(diskon, Decimal("50000.00"))

    def test_kupon_di_bawah_minimal_belanja(self):
        """Kupon harus mengembalikan 0 jika subtotal tidak memenuhi syarat minimum belanja."""
        subtotal_kurang = Decimal("200000")  # min 500.000
        diskon = self.kupon_persen.hitung_diskon(subtotal_kurang)
        self.assertEqual(diskon, Decimal("0"))

    def test_kupon_kedaluwarsa_tidak_dapat_digunakan(self):
        """Kupon yang melewati tanggal berlaku_sampai tidak memberikan diskon."""
        subtotal = Decimal("1000000")
        diskon = self.kupon_kadaluarsa.hitung_diskon(subtotal)
        self.assertEqual(diskon, Decimal("0"))

    def test_api_cek_kupon_valid(self):
        """Endpoint /checkout/cek-kupon mengembalikan JSON potongan yang valid untuk pelanggan login."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["sesi_token"] = self.user.sesi_token

        resp = self.client.post("/checkout/cek-kupon", json={
            "kode": "QADISKON20",
            "subtotal": "1000000"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["potongan"], 200000.0)
        self.assertIn("Rp 200.000", data["potongan_formatted"])

    def test_api_cek_kupon_tidak_ditemukan(self):
        """Endpoint /checkout/cek-kupon mengembalikan 404 jika kode tidak ada."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["sesi_token"] = self.user.sesi_token

        resp = self.client.post("/checkout/cek-kupon", json={
            "kode": "TIDAKADA",
            "subtotal": "1000000"
        })
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertFalse(data["valid"])

    def test_kupon_dikembalikan_saat_pesanan_dibatalkan(self):
        """Memastikan kuota terpakai kupon dikembalikan ketika pesanan dibatalkan."""
        item = KeranjangItem(user_id=self.user.id, produk_id=self.prod.id, jumlah=1)
        db.session.add(item)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["sesi_token"] = self.user.sesi_token

        # Checkout dengan kupon
        self.client.post("/checkout", data={
            "metode_pengiriman": "ambil",
            "metode_pembayaran": "transfer",
            "nama_penerima": "Tester Kupon",
            "telepon": "081234567890",
            "kode_kupon": "QADISKON20"
        }, follow_redirects=True)

        k = Kupon.query.filter_by(kode="QADISKON20").first()
        self.assertEqual(k.terpakai, 1)

        pesanan = Pesanan.query.filter_by(user_id=self.user.id).first()
        self.assertIsNotNone(pesanan)

        # Batalkan pesanan
        self.client.post(f"/pesanan/{pesanan.kode}/batal", follow_redirects=True)

        k_setelah = Kupon.query.filter_by(kode="QADISKON20").first()
        self.assertEqual(k_setelah.terpakai, 0)

    def test_kupon_tidak_dapat_dipakai_dua_kali_oleh_user_sama(self):
        """Memastikan satu pelanggan tidak bisa memakai kupon promo berulang kali."""
        item = KeranjangItem(user_id=self.user.id, produk_id=self.prod.id, jumlah=1)
        db.session.add(item)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["sesi_token"] = self.user.sesi_token

        # Checkout pertama berhasil
        self.client.post("/checkout", data={
            "metode_pengiriman": "ambil",
            "metode_pembayaran": "transfer",
            "nama_penerima": "Tester Kupon",
            "telepon": "081234567890",
            "kode_kupon": "QADISKON20"
        }, follow_redirects=True)

        # Cek kupon lewat API untuk pesanan berikutnya -> harus ditolak karena sudah dipakai
        resp = self.client.post("/checkout/cek-kupon", json={
            "kode": "QADISKON20",
            "subtotal": "1000000"
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["valid"])
        self.assertIn("1 kali per akun", data["pesan"])
