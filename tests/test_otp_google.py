import re
from datetime import timedelta

import pytest
from authlib.integrations.base_client.errors import OAuthError

from conftest import buat_app, tutup_app, login, read_log, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from controllers.google_controller import oauth
from helpers.email import mail
from models import db, utcnow
from models.kode_otp import KodeOtp
from models.user import User

EMAIL_AKTIF = {"MAIL_USERNAME": "toko.pbl@gmail.com", "MAIL_PASSWORD": "app-password-uji",
               "MAIL_DEFAULT_SENDER": ("Elektronik Store", "toko.pbl@gmail.com")}
PASSWORD_BARU = "SandiBaru123!"


@pytest.fixture
def app_email(tmp_path):
    app = buat_app(tmp_path, **EMAIL_AKTIF)
    yield app
    tutup_app(app)


@pytest.fixture
def kotak_masuk(app_email):
    """Email yang 'terkirim' selama tes (MAIL_SUPPRESS_SEND: tidak ada email sungguhan)."""
    with mail.record_messages() as terkirim:
        yield terkirim


def _kode(msg):
    return re.search(r"\b(\d{6})\b", msg.body).group(1)


def _mundurkan_otp(app, detik=120):
    """Lewati jeda kirim ulang 60 detik tanpa menunggu."""
    with app.app_context():
        for otp in KodeOtp.query.all():
            otp.created_at -= timedelta(seconds=detik)
        db.session.commit()


def _user(app, email):
    with app.app_context():
        u = User.query.filter_by(email=email).one()
        db.session.expunge(u)
        return u


# ===== LUPA KATA SANDI =====

def test_lupa_password_lewat_kode_email(app_email, kotak_masuk):
    c = app_email.test_client()
    resp = c.post("/lupa-password", data={"email": "budi@tokoelektronik.id"})
    assert resp.headers["Location"].endswith("/lupa-password/kode")
    assert len(kotak_masuk) == 1 and kotak_masuk[0].recipients == ["budi@tokoelektronik.id"]
    kode = _kode(kotak_masuk[0])
    assert kode not in kotak_masuk[0].subject  # kode tidak tampil di notifikasi layar kunci

    salah = "000000" if kode != "000000" else "111111"
    html = c.post("/lupa-password/kode", data={"kode": salah, "password_baru": PASSWORD_BARU,
                                               "konfirmasi_password": PASSWORD_BARU}).get_data(as_text=True)
    assert "Kode salah atau sudah kedaluwarsa" in html
    resp = c.post("/lupa-password/kode", data={"kode": f"{kode[:3]} {kode[3:]}", "password_baru": PASSWORD_BARU,
                                               "konfirmasi_password": PASSWORD_BARU})
    assert resp.headers["Location"].endswith("/login")
    assert _user(app_email, "budi@tokoelektronik.id").check_password(PASSWORD_BARU)
    assert login(app_email.test_client(), "budi@tokoelektronik.id", PASSWORD_BARU).status_code == 302

    log = read_log(app_email)
    assert "PASSWORD_RESET_OTP" in log and kode not in log  # kode tidak pernah masuk log
    with app_email.app_context():
        assert all(len(o.kode_hash) == 64 and o.kode_hash != kode for o in KodeOtp.query.all())


def test_lupa_password_email_tidak_terdaftar_jawabannya_sama(app_email, kotak_masuk):
    c = app_email.test_client()
    terdaftar = c.post("/lupa-password", data={"email": "budi@tokoelektronik.id"}, follow_redirects=True)
    c2 = app_email.test_client()
    asing = c2.post("/lupa-password", data={"email": "orang@lain.id"}, follow_redirects=True)
    pesan = "Jika email tersebut terdaftar"
    assert pesan in terdaftar.get_data(as_text=True) and pesan in asing.get_data(as_text=True)
    assert len(kotak_masuk) == 1  # hanya email terdaftar yang benar-benar dikirimi kode
    assert "known=0" in read_log(app_email)


def test_kode_hangus_setelah_lima_kali_salah(app_email, kotak_masuk):
    c = app_email.test_client()
    c.post("/lupa-password", data={"email": "budi@tokoelektronik.id"})
    kode = _kode(kotak_masuk[0])
    salah = "000000" if kode != "000000" else "111111"
    data = {"password_baru": PASSWORD_BARU, "konfirmasi_password": PASSWORD_BARU}
    for _ in range(4):
        c.post("/lupa-password/kode", data=dict(data, kode=salah))
    resp = c.post("/lupa-password/kode", data=dict(data, kode=salah))
    assert resp.headers["Location"].endswith("/lupa-password")
    c.post("/lupa-password/kode", data=dict(data, kode=kode))  # kode benar pun sudah tidak berlaku
    assert _user(app_email, "budi@tokoelektronik.id").check_password(CUSTOMER_PASSWORD)
    assert "OTP_LOCKED" in read_log(app_email)


def test_kirim_ulang_dibatasi_dan_kode_lama_tidak_berlaku(app_email, kotak_masuk):
    c = app_email.test_client()
    c.post("/lupa-password", data={"email": "budi@tokoelektronik.id"})
    c.post("/lupa-password/kirim-ulang")
    assert len(kotak_masuk) == 1  # < 60 detik: tidak dikirim lagi
    assert "OTP_THROTTLED" in read_log(app_email)

    _mundurkan_otp(app_email)
    c.post("/lupa-password/kirim-ulang")
    assert len(kotak_masuk) == 2
    lama, baru = _kode(kotak_masuk[0]), _kode(kotak_masuk[1])
    data = {"password_baru": PASSWORD_BARU, "konfirmasi_password": PASSWORD_BARU}
    if lama != baru:
        c.post("/lupa-password/kode", data=dict(data, kode=lama))
        assert _user(app_email, "budi@tokoelektronik.id").check_password(CUSTOMER_PASSWORD)
    c.post("/lupa-password/kode", data=dict(data, kode=baru))
    assert _user(app_email, "budi@tokoelektronik.id").check_password(PASSWORD_BARU)


def test_kode_kedaluwarsa_setelah_10_menit(app_email, kotak_masuk):
    c = app_email.test_client()
    c.post("/lupa-password", data={"email": "budi@tokoelektronik.id"})
    with app_email.app_context():
        otp = KodeOtp.query.one()
        otp.kedaluwarsa = utcnow() - timedelta(seconds=1)
        db.session.commit()
    c.post("/lupa-password/kode", data={"kode": _kode(kotak_masuk[0]), "password_baru": PASSWORD_BARU,
                                        "konfirmasi_password": PASSWORD_BARU})
    assert _user(app_email, "budi@tokoelektronik.id").check_password(CUSTOMER_PASSWORD)


def test_tanpa_konfigurasi_email_lupa_password_menyarankan_hubungi_admin(client):
    html = client.get("/lupa-password").get_data(as_text=True)
    assert "belum diaktifkan" in html
    assert client.post("/lupa-password", data={"email": "budi@tokoelektronik.id"}).status_code == 200


# ===== VERIFIKASI EMAIL SAAT DAFTAR =====

DAFTAR = {"nama_lengkap": "Siti Aminah", "email": "siti@gmail.com", "password": "SitiAman123!",
          "confirm_password": "SitiAman123!", "setuju": "y"}


def test_daftar_wajib_verifikasi_email(app_email, kotak_masuk):
    c = app_email.test_client()
    resp = c.post("/register", data=DAFTAR)
    assert resp.headers["Location"].endswith("/verifikasi")
    assert kotak_masuk[0].recipients == ["siti@gmail.com"]
    assert not _user(app_email, "siti@gmail.com").email_terverifikasi
    assert "/login" in c.get("/profil").headers["Location"]  # belum login sebelum kode dimasukkan

    # Keluar lalu login lagi: tetap diminta kode (kode baru dikirim setelah jeda)
    _mundurkan_otp(app_email)
    c2 = app_email.test_client()
    assert login(c2, "siti@gmail.com", "SitiAman123!").headers["Location"].endswith("/verifikasi")
    resp = c2.post("/verifikasi", data={"kode": _kode(kotak_masuk[-1])})
    assert resp.status_code == 302 and c2.get("/profil").status_code == 200
    assert _user(app_email, "siti@gmail.com").email_terverifikasi
    assert "EMAIL_VERIFIED" in read_log(app_email) and "method=password+otp" in read_log(app_email)


def test_tanpa_email_daftar_langsung_aktif(client, app):
    client.post("/register", data=DAFTAR)
    assert _user(app, "siti@gmail.com").email_terverifikasi
    assert login(client, "siti@gmail.com", "SitiAman123!").headers["Location"].endswith("/")


# ===== OTP LOGIN AKUN PANEL =====

def test_otp_login_admin_jika_dinyalakan(tmp_path):
    app = buat_app(tmp_path, OTP_LOGIN_PANEL=True, **EMAIL_AKTIF)
    try:
        with mail.record_messages() as kotak:
            c = app.test_client()
            resp = login(c, "admin@tokoelektronik.id", ADMIN_PASSWORD)
            assert resp.headers["Location"].endswith("/verifikasi")
            assert c.get("/admin").status_code == 302  # kata sandi benar saja belum cukup
            resp = c.post("/verifikasi", data={"kode": _kode(kotak[0])})
            assert resp.headers["Location"].endswith("/admin")
            assert c.get("/admin").status_code == 200

            # Pelanggan tidak terkena OTP login
            assert login(app.test_client(), "budi@tokoelektronik.id", CUSTOMER_PASSWORD).headers["Location"].endswith("/")
    finally:
        tutup_app(app)


# ===== LOGIN GOOGLE =====

GOOGLE = {"GOOGLE_CLIENT_ID": "id-uji.apps.googleusercontent.com", "GOOGLE_CLIENT_SECRET": "rahasia-uji"}


@pytest.fixture
def app_google(tmp_path):
    app = buat_app(tmp_path, **GOOGLE)
    yield app
    tutup_app(app)


def _google_mengembalikan(monkeypatch, info=None, error=None):
    def palsu(**kwargs):
        if error:
            raise OAuthError(error=error)
        return {"access_token": "x", "userinfo": info}
    monkeypatch.setattr(oauth.google, "authorize_access_token", palsu)


def test_login_google_membuat_akun_pelanggan(app_google, monkeypatch):
    _google_mengembalikan(monkeypatch, {"sub": "g-123", "email": "Rina.Putri@gmail.com", "email_verified": True,
                                        "name": "Rina Putri 🌸"})
    c = app_google.test_client()
    assert "Masuk dengan Google" in c.get("/login").get_data(as_text=True)
    resp = c.get("/login/google/callback")
    assert resp.status_code == 302 and c.get("/profil").status_code == 200
    u = _user(app_google, "rina.putri@gmail.com")
    assert u.role == User.ROLE_CUSTOMER and u.google_sub == "g-123" and u.nama_lengkap == "Rina Putri"
    assert "method=google" in read_log(app_google)

    # Masuk kedua kali dengan akun Google yang sama: tidak membuat akun baru
    app_google.test_client().get("/login/google/callback")
    with app_google.app_context():
        assert User.query.filter_by(google_sub="g-123").count() == 1


def test_login_google_menyambung_akun_pelanggan_dengan_email_sama(app_google, monkeypatch):
    _google_mengembalikan(monkeypatch, {"sub": "g-budi", "email": "budi@tokoelektronik.id", "email_verified": True})
    c = app_google.test_client()
    c.get("/login/google/callback")
    assert c.get("/keranjang").status_code == 200
    assert _user(app_google, "budi@tokoelektronik.id").google_sub == "g-budi"


def test_login_google_tidak_bisa_masuk_ke_akun_admin(app_google, monkeypatch):
    _google_mengembalikan(monkeypatch, {"sub": "g-adm", "email": "admin@tokoelektronik.id", "email_verified": True})
    c = app_google.test_client()
    c.get("/login/google/callback")
    assert c.get("/admin").status_code == 302
    assert _user(app_google, "admin@tokoelektronik.id").google_sub is None
    assert "reason=panel_account" in read_log(app_google)


def test_login_google_ditolak_jika_email_belum_terverifikasi_atau_dibatalkan(app_google, monkeypatch):
    _google_mengembalikan(monkeypatch, {"sub": "g-x", "email": "x@gmail.com", "email_verified": False})
    c = app_google.test_client()
    c.get("/login/google/callback")
    assert c.get("/profil").status_code == 302

    _google_mengembalikan(monkeypatch, error="access_denied")
    resp = c.get("/login/google/callback", follow_redirects=True)
    assert "dibatalkan" in resp.get_data(as_text=True)
    with app_google.app_context():
        assert User.query.filter_by(email="x@gmail.com").count() == 0


def test_google_nonaktif_tanpa_konfigurasi(client):
    assert client.get("/login/google").status_code == 404
    assert "Masuk dengan Google" not in client.get("/login").get_data(as_text=True)
