import re

from conftest import login, read_log, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models.user import User


def test_register_berhasil_sebagai_customer(client, app):
    resp = client.post("/register", data={
        "username": "siti_01", "email": "Siti@TokoElektronik.id",
        "password": "Rahasia123!", "confirm_password": "Rahasia123!",
    })
    assert resp.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="siti_01").first()
        assert user.role == User.ROLE_CUSTOMER
        assert user.email == "siti@tokoelektronik.id"
        assert user.password_hash != "Rahasia123!"
    assert "REGISTER_SUCCESS" in read_log(app)


def test_register_menolak_password_lemah(client, app):
    resp = client.post("/register", data={
        "username": "lemah", "email": "lemah@tokoelektronik.id",
        "password": "password", "confirm_password": "password",
    })
    assert resp.status_code == 200
    assert "huruf besar" in resp.get_data(as_text=True)
    with app.app_context():
        assert User.query.filter_by(username="lemah").first() is None


def test_register_menolak_email_duplikat(client):
    resp = client.post("/register", data={
        "username": "budi2", "email": "budi@tokoelektronik.id",
        "password": "Rahasia123!", "confirm_password": "Rahasia123!",
    })
    assert "Email sudah terdaftar" in resp.get_data(as_text=True)


def test_login_sukses_dicatat_di_log(client, app):
    resp = login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    log = read_log(app)
    assert "SUCCESSFUL_LOGIN" in log and "username=budi" in log
    # Format waktu ISO 8601 zona WIB
    assert re.search(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+07:00 \| INFO \| SUCCESSFUL_LOGIN", log, re.M)


def test_login_gagal_dicatat_dan_pesan_generik(client, app):
    resp = login(client, "budi@tokoelektronik.id", "SalahBanget1!")
    assert "Email atau kata sandi salah" in resp.get_data(as_text=True)
    resp = login(client, "tidakada@tokoelektronik.id", "SalahBanget1!")
    assert "Email atau kata sandi salah" in resp.get_data(as_text=True)
    log = read_log(app)
    assert "FAILED_LOGIN" in log
    assert "reason=invalid_password" in log and "reason=unknown_email" in log


def test_akun_terkunci_setelah_5_kali_gagal(client, app):
    for _ in range(5):
        login(client, "budi@tokoelektronik.id", "SalahBanget1!")
    assert "ACCOUNT_LOCKED" in read_log(app)

    # Password benar pun ditolak selama akun terkunci
    resp = login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert "dikunci sementara" in resp.get_data(as_text=True)
    assert "LOGIN_BLOCKED" in read_log(app)


def test_log_injection_dinetralkan(client, app):
    login(client, "x@tokoelektronik.id", "a")  # memicu validasi saja
    client.post("/login", data={"email": "evil@tokoelektronik.id\nFAKE_EVENT", "password": "x"})
    for line in read_log(app).splitlines():
        assert line[:4].isdigit(), "Setiap baris log harus diawali timestamp"


def test_logout_hanya_lewat_post(client, app):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert client.get("/logout").status_code == 405
    resp = client.post("/logout")
    assert resp.status_code == 302
    assert "LOGOUT" in read_log(app)


def test_redirect_next_tidak_bisa_ke_situs_luar(client):
    resp = client.post("/login?next=//evil.example", data={"email": "budi@tokoelektronik.id", "password": CUSTOMER_PASSWORD})
    assert "evil.example" not in resp.headers["Location"]


def test_admin_diarahkan_ke_dashboard(client):
    resp = login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    assert resp.headers["Location"].endswith("/admin")
