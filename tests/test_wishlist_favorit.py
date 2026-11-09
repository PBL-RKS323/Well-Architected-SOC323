"""Pengujian unit dan integrasi fitur wishlist favorit pelanggan.
Disusun oleh: Ripasha Alvarisi (QA Engineer)
"""
import unittest
from app import create_app
from config import TestConfig
from models import db
from models.user import User
from models.produk import Produk
from models.favorit import Favorit


class TestWishlistFavorit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        self.user1 = User(username="qa_wish_1", email="wish1@soc323.id", role=User.ROLE_CUSTOMER)
        self.user1.set_password("WishPass123#")
        
        self.user2 = User(username="qa_wish_2", email="wish2@soc323.id", role=User.ROLE_CUSTOMER)
        self.user2.set_password("WishPass123#")

        self.prod = Produk(nama_produk="Laptop Wish", merek="Asus", kategori="Laptop", harga=12000000, stok=5, gambar="laptop.jpg")
        db.session.add_all([self.user1, self.user2, self.prod])
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        Favorit.query.delete()
        Produk.query.delete()
        User.query.delete()
        db.session.commit()
        self.ctx.pop()

    def test_toggle_tambah_dan_hapus_favorit(self):
        """Metode model Favorit.toggle menambahkan produk dan menghapusnya jika diklik kembali."""
        # 1. Tambah ke favorit
        added = Favorit.toggle(self.user1.id, self.prod.id)
        self.assertTrue(added)
        self.assertTrue(Favorit.is_favorit(self.user1.id, self.prod.id))

        # 2. Hapus dari favorit (klik kedua kali)
        removed = Favorit.toggle(self.user1.id, self.prod.id)
        self.assertFalse(removed)
        self.assertFalse(Favorit.is_favorit(self.user1.id, self.prod.id))

    def test_isolasi_wishlist_antar_pengguna(self):
        """Wishlist User 1 tidak boleh muncul atau tercampur di akun User 2."""
        Favorit.toggle(self.user1.id, self.prod.id)
        self.assertTrue(Favorit.is_favorit(self.user1.id, self.prod.id))
        self.assertFalse(Favorit.is_favorit(self.user2.id, self.prod.id))

    def test_halaman_favorit_pelanggan_login(self):
        """Pelanggan dapat melihat halaman daftar favorit mereka."""
        Favorit.toggle(self.user1.id, self.prod.id)

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1.id
            sess["sesi_token"] = self.user1.sesi_token

        resp = self.client.get("/favorit")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Laptop Wish", html)

    def test_toggle_ajax_mengembalikan_json(self):
        """Request AJAX ke /favorit/toggle/<id> mengembalikan JSON terstruktur."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1.id
            sess["sesi_token"] = self.user1.sesi_token

        resp = self.client.post(f"/favorit/toggle/{self.prod.id}", headers={
            "X-Requested-With": "XMLHttpRequest"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["favorit"])
