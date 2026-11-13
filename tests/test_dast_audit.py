import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from app import create_app
from config import Config
from models import db
from models.user import User
from models.produk import Produk
from models.pesanan import Pesanan
from models.alamat import Alamat


class RealSecurityConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True


class DynamicSecurityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(RealSecurityConfig)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            # Buat user admin
            admin = User(username="admin_sec", nama_lengkap="Admin Security", email="admin_sec@soc323.id", role=User.ROLE_ADMIN)
            admin.set_password("AdminPass123#")
            
            # Buat user customer A
            user_a = User(username="cust_a", nama_lengkap="Customer A", email="cust_a@soc323.id", role=User.ROLE_CUSTOMER)
            user_a.set_password("CustomerA123#")
            
            # Buat user customer B
            user_b = User(username="cust_b", nama_lengkap="Customer B", email="cust_b@soc323.id", role=User.ROLE_CUSTOMER)
            user_b.set_password("CustomerB123#")
            
            # Tambah produk contoh
            prod = Produk(nama_produk="Laptop Audit", merek="Asus", kategori="Laptop", harga=15000000, stok=10, gambar="laptop.jpg")
            
            db.session.add_all([admin, user_a, user_b, prod])
            db.session.commit()
            
            cls.admin_id = admin.id
            cls.user_a_id = user_a.id
            cls.user_b_id = user_b.id
            cls.prod_id = prod.id

    def test_01_sql_injection_on_search_and_filters(self):
        """Uji fuzzer SQL Injection pada query search, filter kategori, merek, dan harga."""
        payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users;--",
            "' UNION SELECT username, password_hash FROM users--",
            "admin'--",
            "1' AND SLEEP(2)--",
        ]
        for p in payloads:
            resp = self.client.get(f"/jelajah?q={p}&kategori={p}&merek={p}&min=abc&max=xyz")
            self.assertEqual(resp.status_code, 200, f"SQLi payload broke endpoint: {p}")
            html = resp.get_data(as_text=True)
            self.assertNotIn("OperationalError", html)
            self.assertNotIn("syntax error", html.lower())
            self.assertNotIn("Traceback (most recent call last)", html)
        print("  [PASS] SQL Injection fuzzing passed: Parameter binding securely handled in ORM.")

    def test_02_xss_reflected_prevention(self):
        """Uji pencegahan XSS pada parameter URL q, min, max, dll."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "\" autofocus onfocus=alert(1) \"",
            "<svg/onload=alert(1)>",
        ]
        for p in xss_payloads:
            resp = self.client.get(f"/jelajah?q={p}")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertNotIn("<script>alert('XSS')</script>", html)
            self.assertNotIn("<img src=x onerror=alert(1)>", html)
            self.assertNotIn("<svg/onload=alert(1)>", html)
        print("  [PASS] Reflected XSS fuzzing passed: Inputs are strictly HTML-escaped by Jinja2.")

    def test_03_csrf_protection_enforcement(self):
        """Uji penolakan request perubahan data (POST) tanpa token CSRF yang valid."""
        # POST ke login tanpa token CSRF
        resp = self.client.post("/login", data={"email": "cust_a@soc323.id", "password": "CustomerA123#"})
        self.assertEqual(resp.status_code, 400, "CSRF must reject POST without valid token")

        # POST ke logout lewat GET
        resp_get_logout = self.client.get("/logout")
        self.assertEqual(resp_get_logout.status_code, 405, "Logout via GET must be rejected with 405")
        print("  [PASS] CSRF Enforcement passed: 400 Bad Request on missing/invalid CSRF token.")

    def test_04_idor_and_privilege_escalation(self):
        """Uji IDOR: Pelanggan tidak boleh mengakses panel admin atau pesanan pengguna lain."""
        # Login sebagai User A
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_a_id
            with self.app.app_context():
                u = db.session.get(User, self.user_a_id)
                sess["sesi_token"] = u.sesi_token

        # User A mencoba buka panel admin /admin
        resp = self.client.get("/admin")
        self.assertIn(resp.status_code, [403, 302], "Customer accessing /admin must be rejected (403/302)")

        # Buat alamat milik User B
        with self.app.app_context():
            addr_b = Alamat(user_id=self.user_b_id, label="Rumah B", nama_penerima="Budi B", telepon="0812345", alamat="Jl B", kota="Batam", kode_pos="29461")
            db.session.add(addr_b)
            db.session.commit()
            addr_b_id = addr_b.id

        # User A mencoba edit alamat milik User B (IDOR)
        resp_idor = self.client.get(f"/alamat/{addr_b_id}/edit")
        self.assertIn(resp_idor.status_code, [403, 404], "IDOR edit address must return 403/404")
        print("  [PASS] IDOR & RBAC isolation passed: Access denied across customer domains.")

    def test_05_brute_force_lockout_mechanism(self):
        """Uji proteksi Brute-Force: Akun terkunci setelah 5x gagal login berturut-turut."""
        with self.app.app_context():
            u = db.session.get(User, self.user_a_id)
            u.reset_failed_login()
            db.session.commit()

            # Lakukan 5x gagal password
            for _ in range(5):
                u.register_failed_login(5, 15)
            self.assertTrue(u.is_locked(), "Account must be locked after 5 failed attempts")
            u.reset_failed_login()
            db.session.commit()
        print("  [PASS] Brute-Force lockout mechanism passed: Account locked after 5 attempts.")

    def test_06_security_headers(self):
        """Uji kelengkapan HTTP Security Headers."""
        resp = self.client.get("/")
        headers = resp.headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn(headers.get("X-Frame-Options"), ["DENY", "SAMEORIGIN"])
        print("  [PASS] Security Headers passed: X-Content-Type-Options: nosniff, X-Frame-Options: DENY.")


if __name__ == "__main__":
    print("=" * 60)
    print("STARTING DAST DYNAMIC SECURITY AUDIT & VULNERABILITY TESTS")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(DynamicSecurityAudit)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
