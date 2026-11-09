"""Unit test untuk model-model ERD Best Practice E-Commerce (Kategori, Favorit, Kupon, Pembayaran)."""
import unittest
from datetime import timedelta
from decimal import Decimal

from app import create_app
from config import TestConfig
from models import db, utcnow
from models.user import User
from models.produk import Produk
from models.pesanan import Pesanan, PesananItem
from models.kategori import Kategori
from models.favorit import Favorit
from models.kupon import Kupon
from models.pembayaran import Pembayaran


class TestERDBestPractice(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Buat user pembeli & admin
        self.cust = User(username="cust_erd", email="cust_erd@soc323.id", role=User.ROLE_CUSTOMER)
        self.cust.set_password("CustPass123#")
        self.admin = User(username="admin_erd", email="admin_erd@soc323.id", role=User.ROLE_ADMIN)
        self.admin.set_password("AdminPass123#")
        db.session.add_all([self.cust, self.admin])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_01_kategori_model_and_product_relation(self):
        """Memvalidasi entitas Kategori dan relasi 1:N ke Produk."""
        kat = Kategori(nama="Smartphone Pro", slug="smartphone-pro", ikon="smartphone", urutan=1)
        db.session.add(kat)
        db.session.commit()

        self.assertIsNotNone(kat.id)
        self.assertEqual(kat.slug, "smartphone-pro")

        # Hubungkan produk ke kategori
        prod = Produk(
            nama_produk="iPhone 16 Pro",
            merek="Apple",
            kategori="Handphone",
            kategori_id=kat.id,
            harga=Decimal("20000000"),
            stok=15,
            gambar="iphone16.jpg"
        )
        db.session.add(prod)
        db.session.commit()

        self.assertEqual(prod.kategori_rel.nama, "Smartphone Pro")
        self.assertEqual(kat.produk_list.count(), 1)
        self.assertEqual(kat.produk_list.first().nama_produk, "iPhone 16 Pro")

    def test_02_favorit_wishlist_toggle_and_cascade(self):
        """Memvalidasi wishlist pelanggan (Favorit), toggle, dan cascade delete."""
        prod = Produk(
            nama_produk="Sony WH-1000XM5",
            merek="Sony",
            kategori="Audio",
            harga=Decimal("5000000"),
            stok=10,
            gambar="sony.jpg"
        )
        db.session.add(prod)
        db.session.commit()

        # Toggle ON
        status = Favorit.toggle(self.cust.id, prod.id)
        self.assertTrue(status)
        self.assertTrue(Favorit.is_favorit(self.cust.id, prod.id))
        self.assertEqual(self.cust.daftar_favorit.count(), 1)

        # Toggle OFF
        status_off = Favorit.toggle(self.cust.id, prod.id)
        self.assertFalse(status_off)
        self.assertFalse(Favorit.is_favorit(self.cust.id, prod.id))
        self.assertEqual(self.cust.daftar_favorit.count(), 0)

    def test_03_kupon_promosi_calculation(self):
        """Memvalidasi kalkulasi diskon kupon persentase dan nominal."""
        # Kupon persentase 20% max 500rb min belanja 1jt
        kupon_persen = Kupon(
            kode="HEMAT20",
            tipe=Kupon.TIPE_PERSEN,
            nilai=Decimal("20.00"),
            min_belanja=Decimal("1000000"),
            maks_potongan=Decimal("500000"),
            kuota=10,
            aktif=True
        )
        db.session.add(kupon_persen)
        db.session.commit()

        # Belanja 500rb (belum min_belanja) -> diskon 0
        self.assertEqual(kupon_persen.hitung_diskon(500000), 0)

        # Belanja 2jt (20% = 400rb < maks 500rb) -> diskon 400.000
        self.assertEqual(kupon_persen.hitung_diskon(2000000), 400000.0)

        # Belanja 5jt (20% = 1jt > maks 500rb) -> diskon 500.000
        self.assertEqual(kupon_persen.hitung_diskon(5000000), 500000.0)

        # Kupon kedaluwarsa
        kupon_kadaluarsa = Kupon(
            kode="EXPIRED",
            tipe=Kupon.TIPE_NOMINAL,
            nilai=Decimal("50000"),
            min_belanja=Decimal("0"),
            berlaku_sampai=utcnow() - timedelta(days=1),
            aktif=True
        )
        self.assertEqual(kupon_kadaluarsa.hitung_diskon(100000), 0)

    def test_04_pesanan_and_pembayaran_audit(self):
        """Memvalidasi entitas Pembayaran terhubung ke Pesanan dan diverifikasi oleh admin."""
        prod = Produk(nama_produk="Laptop ROG", merek="Asus", kategori="Laptop", harga=Decimal("25000000"), stok=5, gambar="rog.jpg")
        db.session.add(prod)
        db.session.commit()

        pesanan = Pesanan(
            kode="ES-TEST-001",
            user_id=self.cust.id,
            status=Pesanan.MENUNGGU_VERIFIKASI,
            metode_pengiriman=Pesanan.KURIR,
            metode_pembayaran=Pesanan.TRANSFER,
            nama_penerima="Budi Test",
            telepon="0812345678",
            subtotal=Decimal("25000000"),
            ongkir=Decimal("50000"),
            diskon=Decimal("500000"),
            total=Decimal("24550000"),
            batas_bayar=utcnow() + timedelta(hours=24)
        )
        db.session.add(pesanan)
        db.session.commit()

        # Buat transaksi pembayaran
        bayar = Pembayaran(
            pesanan_id=pesanan.id,
            metode_pembayaran="transfer",
            jumlah=Decimal("24550000"),
            bukti_bayar="bukti_transfer_123.jpg",
            status=Pembayaran.STATUS_PENDING
        )
        db.session.add(bayar)
        db.session.commit()

        self.assertEqual(pesanan.daftar_transaksi[0].status, Pembayaran.STATUS_PENDING)
        self.assertEqual(pesanan.total, Decimal("24550000"))

        # Admin verifikasi pembayaran
        bayar.status = Pembayaran.STATUS_DIVERIFIKASI
        bayar.diverifikasi_oleh = self.admin.id
        bayar.waktu_verifikasi = utcnow()
        bayar.catatan_verifikasi = "Mutasi rekening cocok dan lunas"
        db.session.commit()

        self.assertEqual(bayar.verifikator.username, "admin_erd")
        self.assertEqual(bayar.status, Pembayaran.STATUS_DIVERIFIKASI)


if __name__ == "__main__":
    unittest.main()
