from conftest import login, read_log, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models.user import User


def test_password_dengan_simbol_pagar_diterima(client, app):
    resp = client.post("/register", data={
        "username": "andi", "email": "andi@tokoelektronik.id",
        "password": "Admin123#", "confirm_password": "Admin123#",
    })
    assert resp.status_code == 302


def test_pengaturan_wajib_login(client):
    resp = client.get("/pengaturan")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_halaman_pengaturan_tampil(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    html = client.get("/pengaturan").get_data(as_text=True)
    assert "Ubah Email" in html and "Ubah Kata Sandi" in html


def test_ubah_email_berhasil(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/pengaturan/email", data={
        "email-email_baru": "Bos@TokoElektronik.id", "email-password_sekarang": ADMIN_PASSWORD,
    })
    assert resp.status_code == 302
    with app.app_context():
        assert User.query.filter_by(username="admin").first().email == "bos@tokoelektronik.id"
    assert "EMAIL_CHANGED" in read_log(app)

    # Login berikutnya memakai email baru
    client.post("/logout")
    assert login(client, "bos@tokoelektronik.id", ADMIN_PASSWORD).headers["Location"].endswith("/admin")


def test_ubah_email_ditolak_jika_password_salah(client, app):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/pengaturan/email", data={
        "email-email_baru": "lain@tokoelektronik.id", "email-password_sekarang": "Salah123#",
    })
    assert "Kata sandi saat ini salah" in resp.get_data(as_text=True)
    with app.app_context():
        assert User.query.filter_by(username="admin").first().email == "admin@tokoelektronik.id"
    assert "CREDENTIAL_CHANGE_FAILED" in read_log(app)


def test_ubah_email_ke_email_milik_orang_lain_ditolak(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/pengaturan/email", data={
        "email-email_baru": "budi@tokoelektronik.id", "email-password_sekarang": ADMIN_PASSWORD,
    })
    assert "sudah dipakai akun lain" in resp.get_data(as_text=True)


def test_ubah_password_berhasil(client, app):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post("/pengaturan/password", data={
        "pw-password_sekarang": CUSTOMER_PASSWORD,
        "pw-password_baru": "BaruLagi99#", "pw-konfirmasi_password": "BaruLagi99#",
    })
    assert resp.status_code == 302
    assert "PASSWORD_CHANGED" in read_log(app)

    client.post("/logout")
    assert "Email atau kata sandi salah" in login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD).get_data(as_text=True)
    assert login(client, "budi@tokoelektronik.id", "BaruLagi99#").status_code == 302


def test_ubah_password_ditolak_jika_lemah_atau_sama(client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post("/pengaturan/password", data={
        "pw-password_sekarang": CUSTOMER_PASSWORD,
        "pw-password_baru": "lemah", "pw-konfirmasi_password": "lemah",
    })
    assert "minimal 8 karakter" in resp.get_data(as_text=True)

    resp = client.post("/pengaturan/password", data={
        "pw-password_sekarang": CUSTOMER_PASSWORD,
        "pw-password_baru": CUSTOMER_PASSWORD, "pw-konfirmasi_password": CUSTOMER_PASSWORD,
    })
    assert "tidak boleh sama" in resp.get_data(as_text=True)


def test_ubah_password_ditolak_jika_password_lama_salah(client, app):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    resp = client.post("/pengaturan/password", data={
        "pw-password_sekarang": "Salah123#",
        "pw-password_baru": "BaruLagi99#", "pw-konfirmasi_password": "BaruLagi99#",
    })
    assert "Kata sandi saat ini salah" in resp.get_data(as_text=True)
