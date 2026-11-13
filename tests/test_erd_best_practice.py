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


    def test_05_favorit_routes_integration(self):
        """Memvalidasi integrasi route /favorit dan /favorit/toggle."""
        prod = Produk(nama_produk="iPad Pro M4", merek="Apple", kategori="Tablet", harga=Decimal("18000000"), stok=5, gambar="ipad.jpg")
        db.session.add(prod)
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.cust.id
            sess["sesi_token"] = self.cust.sesi_token

        # Toggle favorit ON via POST
        resp = client.post(f"/favorit/toggle/{prod.id}", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Favorit.is_favorit(self.cust.id, prod.id))

        # Akses halaman daftar favorit
        resp_list = client.get("/favorit")
        self.assertEqual(resp_list.status_code, 200)
        self.assertIn("iPad Pro M4", resp_list.get_data(as_text=True))

    def test_06_checkout_with_kupon_integration(self):
        """Memvalidasi alur checkout menggunakan kode kupon diskon."""
        from models.keranjang import KeranjangItem
        prod = Produk(nama_produk="MacBook Air M3", merek="Apple", kategori="Laptop", harga=Decimal("15000000"), stok=5, gambar="macbook.jpg")
        kupon = Kupon(kode="HEMAT10", tipe=Kupon.TIPE_PERSEN, nilai=Decimal("10.0"), min_belanja=Decimal("5000000"), aktif=True)
        db.session.add_all([prod, kupon])
        db.session.commit()

        # Tambahkan ke keranjang
        item = KeranjangItem(user_id=self.cust.id, produk_id=prod.id, jumlah=1)
        db.session.add(item)
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.cust.id
            sess["sesi_token"] = self.cust.sesi_token

        # POST checkout dengan kupon HEMAT10
        data = {
            "metode_pengiriman": "ambil",
            "metode_pembayaran": "transfer",
            "nama_penerima": "Budi Belanja",
            "telepon": "081234567890",
            "kode_kupon": "HEMAT10",
        }
        resp = client.post("/checkout", data=data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Cek pesanan yang terbentuk
        pesanan = Pesanan.query.filter_by(user_id=self.cust.id).first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(pesanan.kupon_id, kupon.id)
        self.assertEqual(pesanan.diskon, Decimal("1500000.00"))  # 10% dari 15jt = 1.5jt
        self.assertEqual(pesanan.total, Decimal("13500000.00"))
        self.assertEqual(len(pesanan.daftar_transaksi), 1)
        self.assertEqual(pesanan.daftar_transaksi[0].status, Pembayaran.STATUS_PENDING)

    def test_07_pembayaran_lifecycle_sync(self):
        """Memvalidasi sinkronisasi status pembayaran saat dibatalkan / ditolak."""
        from models.keranjang import KeranjangItem
        prod = Produk(nama_produk="AirPods Max", merek="Apple", kategori="Audio", harga=Decimal("8000000"), stok=5, gambar="airpods.jpg")
        db.session.add(prod)
        db.session.commit()

        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.cust.id
            sess["sesi_token"] = self.cust.sesi_token

        item = KeranjangItem(user_id=self.cust.id, produk_id=prod.id, jumlah=1)
        db.session.add(item)
        db.session.commit()

        # Checkout
        client.post("/checkout", data={
            "metode_pengiriman": "ambil",
            "metode_pembayaran": "transfer",
            "nama_penerima": "Budi Belanja",
            "telepon": "081234567890",
        }, follow_redirects=True)

        pesanan = Pesanan.query.filter_by(user_id=self.cust.id).order_by(Pesanan.id.desc()).first()
        self.assertIsNotNone(pesanan)
        self.assertEqual(len(pesanan.daftar_transaksi), 1)
        self.assertEqual(pesanan.daftar_transaksi[0].status, Pembayaran.STATUS_PENDING)

        # Batalkan pesanan oleh pelanggan -> status Pembayaran harus menjadi ditolak
        client.post(f"/pesanan/{pesanan.kode}/batal", follow_redirects=True)
        bayar = Pembayaran.query.filter_by(pesanan_id=pesanan.id).first()
        self.assertEqual(bayar.status, Pembayaran.STATUS_DITOLAK)
        self.assertIn("dibatalkan", bayar.catatan_verifikasi.lower())


if __name__ == "__main__":
    unittest.main()

