import os

from conftest import login, read_log, produk_data, ADMIN_PASSWORD, CUSTOMER_PASSWORD
from models import db
from models.alamat import Alamat
from models.user import User

STAF_PASSWORD = "StafToko123!"


def _buat(app, username, role, password=STAF_PASSWORD, aktif=True):
    with app.app_context():
        u = User(username=username, nama_lengkap=username.title(), email=f"{username}@tokoelektronik.id",
                 role=role, aktif=aktif)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u.id


def _user(app, user_id):
    with app.app_context():
        u = db.session.get(User, user_id)
        db.session.expunge(u)
        return u


# --- RBAC ---

def test_izin_per_peran():
    admin, staf, pelanggan = (User(role=r) for r in (User.ROLE_ADMIN, User.ROLE_STAF, User.ROLE_CUSTOMER))
    assert admin.punya_izin("kelola_user") and not staf.punya_izin("kelola_user")
    assert staf.punya_izin("kelola_produk") and staf.punya_izin("kelola_pesanan")
    assert not pelanggan.punya_izin("panel") and pelanggan.punya_izin("belanja")
    assert not admin.punya_izin("belanja") and not staf.punya_izin("belanja")


def test_staf_bisa_produk_pesanan_tapi_tidak_pengguna(app, client):
    _buat(app, "staf", User.ROLE_STAF)
    login(client, "staf@tokoelektronik.id", STAF_PASSWORD)
    assert client.get("/admin").status_code == 200
    assert client.get("/admin/produk").status_code == 200
    assert client.get("/admin/pesanan").status_code == 200
    resp = client.post("/admin/produk/tambah", data=produk_data(), content_type="multipart/form-data")
    assert resp.status_code == 302 and "/admin/produk" in resp.headers["Location"]

    resp = client.get("/admin/pengguna")
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/admin")
    assert "permission=kelola_user" in read_log(app)
    assert ">Pengguna<" not in client.get("/admin").get_data(as_text=True)  # menu disembunyikan
    assert client.get("/keranjang").headers["Location"].endswith("/admin")   # staf tidak berbelanja


def test_pelanggan_tidak_bisa_masuk_panel(client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    for url in ["/admin", "/admin/produk", "/admin/pengguna"]:
        resp = client.get(url)
        assert resp.status_code == 302 and resp.headers["Location"].endswith("/")


# --- KELOLA PENGGUNA ---

def test_admin_tambah_staf_dan_ubah_peran(app, client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    resp = client.post("/admin/pengguna/tambah", data={"nama_lengkap": "Rina Staf", "email": "rina@tokoelektronik.id",
                                                     "peran": "staf", "password": STAF_PASSWORD})
    assert resp.status_code == 302
    with app.app_context():
        rina = User.query.filter_by(email="rina@tokoelektronik.id").one()
        assert rina.role == User.ROLE_STAF
        rina_id = rina.id
    assert "USER_CREATED" in read_log(app)

    client.post(f"/admin/pengguna/{rina_id}/aksi", data={"aksi": "ubah_peran", "peran": "customer"})
    assert _user(app, rina_id).role == User.ROLE_CUSTOMER
    assert "USER_ROLE_CHANGED" in read_log(app)

    html = client.get("/admin/pengguna?q=rina").get_data(as_text=True)
    assert "Rina Staf" in html and "Budi Santoso" not in html


def test_tambah_pengguna_tolak_password_lemah_dan_email_ganda(client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    html = client.post("/admin/pengguna/tambah", data={"nama_lengkap": "Lemah", "email": "budi@tokoelektronik.id",
                                                      "peran": "staf", "password": "123"}).get_data(as_text=True)
    assert "Email sudah terdaftar" in html and "Kata sandi minimal 8 karakter" in html


def test_nonaktifkan_akun_mengakhiri_sesi_dan_menolak_login(app):
    budi_hp, admin = app.test_client(), app.test_client()
    login(budi_hp, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert budi_hp.get("/profil").status_code == 200

    login(admin, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    with app.app_context():
        budi_id = User.query.filter_by(username="budi").one().id
    admin.post(f"/admin/pengguna/{budi_id}/aksi", data={"aksi": "nonaktifkan"})
    assert _user(app, budi_id).aktif is False

    assert "/login" in budi_hp.get("/profil").headers["Location"]  # sesi lama langsung berakhir
    html = login(budi_hp, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    assert html.status_code == 200 and "dinonaktifkan" in html.get_data(as_text=True)
    assert "account_disabled" in read_log(app)

    admin.post(f"/admin/pengguna/{budi_id}/aksi", data={"aksi": "aktifkan"})
    assert login(budi_hp, "budi@tokoelektronik.id", CUSTOMER_PASSWORD).status_code == 302


def test_admin_tidak_bisa_menurunkan_diri_dan_admin_terakhir_terlindungi(app, client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    with app.app_context():
        admin_id = User.query.filter_by(username="admin").one().id
    client.post(f"/admin/pengguna/{admin_id}/aksi", data={"aksi": "ubah_peran", "peran": "customer"})
    client.post(f"/admin/pengguna/{admin_id}/aksi", data={"aksi": "nonaktifkan"})
    u = _user(app, admin_id)
    assert u.role == User.ROLE_ADMIN and u.aktif

    # Admin kedua nonaktif tidak dihitung: admin satu-satunya yang aktif tetap terlindungi
    lain = _buat(app, "admin2", User.ROLE_ADMIN, aktif=False)
    client.post(f"/admin/pengguna/{lain}/aksi", data={"aksi": "aktifkan"})
    client.post(f"/admin/pengguna/{lain}/aksi", data={"aksi": "ubah_peran", "peran": "staf"})
    assert _user(app, lain).role == User.ROLE_STAF  # boleh, karena admin aktif lain masih ada


def test_buka_kunci_login(app, client):
    with app.app_context():
        budi = User.query.filter_by(username="budi").one()
        budi.register_failed_login(1, 5)
        db.session.commit()
        budi_id = budi.id
    assert _user(app, budi_id).is_locked()
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post(f"/admin/pengguna/{budi_id}/aksi", data={"aksi": "buka_kunci"})
    assert not _user(app, budi_id).is_locked()


# --- ALAMAT SAYA ---

ALAMAT = {"label": "Rumah", "nama_penerima": "Budi Santoso", "telepon": "081234567890",
          "alamat": "Jl. Ahmad Yani No. 10, RT 01/RW 02", "kota": "Kota Batam", "kode_pos": "29461"}


def test_alamat_tambah_utama_dan_dipakai_di_checkout(app, client):
    login(client, "admin@tokoelektronik.id", ADMIN_PASSWORD)
    client.post("/admin/produk/tambah", data=produk_data(), content_type="multipart/form-data")
    client.post("/logout")
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)

    client.post("/alamat/tambah", data=ALAMAT)
    client.post("/alamat/tambah", data=dict(ALAMAT, label="Kantor", alamat="Jl. Engku Putri No. 1, Batam Centre"))
    with app.app_context():
        daftar = {a.label: a for a in Alamat.query.all()}
        assert daftar["Rumah"].utama and not daftar["Kantor"].utama  # alamat pertama otomatis utama
        kantor_id = daftar["Kantor"].id

    client.post(f"/alamat/{kantor_id}/utama")
    with app.app_context():
        assert db.session.get(Alamat, kantor_id).utama
        assert Alamat.query.filter_by(utama=True).count() == 1

    client.post("/keranjang/tambah/1")
    html = client.get("/checkout").get_data(as_text=True)
    assert "Jl. Engku Putri No. 1" in html and "Rumah" in html  # alamat utama terisi, pilihan lain tampil


def test_alamat_orang_lain_tidak_bisa_diubah(app, client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    client.post("/alamat/tambah", data=ALAMAT)
    client.post("/logout")
    _buat(app, "siti", User.ROLE_CUSTOMER, password=CUSTOMER_PASSWORD)
    login(client, "siti@tokoelektronik.id", CUSTOMER_PASSWORD)
    with app.app_context():
        alamat_id = Alamat.query.one().id
    assert client.get(f"/alamat/{alamat_id}/edit").status_code == 404
    assert client.post(f"/alamat/{alamat_id}/hapus").status_code == 404
    with app.app_context():
        assert Alamat.query.count() == 1


def test_alamat_maksimal_dan_validasi(app, client):
    login(client, "budi@tokoelektronik.id", CUSTOMER_PASSWORD)
    html = client.post("/alamat/tambah", data=dict(ALAMAT, kode_pos="12")).get_data(as_text=True)
    assert "Kode pos harus 5 digit" in html
    for i in range(Alamat.MAKS_PER_USER + 1):
        client.post("/alamat/tambah", data=dict(ALAMAT, label=f"A{i}"))
    with app.app_context():
        assert Alamat.query.count() == Alamat.MAKS_PER_USER


# --- PERINTAH CLI buat-pengguna ---

def test_cli_buat_pengguna_simpan_password_di_file_privat(app, tmp_path):
    app.instance_path = str(tmp_path / "instance")
    runner = app.test_cli_runner()
    hasil = runner.invoke(args=["buat-pengguna", "--nama", "Intan Sri Diana", "--email", "Intan@Neteye.my.id",
                                "--peran", "staf"])
    assert hasil.exit_code == 0, hasil.output
    baris = open(os.path.join(app.instance_path, "akun_baru.txt"), encoding="utf-8").read().strip()
    password = baris.split(" | ")[-1]
    assert password not in hasil.output  # tidak tercetak di terminal
    with app.app_context():
        u = User.query.filter_by(email="intan@neteye.my.id").one()
        assert u.role == User.ROLE_STAF and u.check_password(password)

    gagal = runner.invoke(args=["buat-pengguna", "--nama", "Lain", "--email", "intan@neteye.my.id", "--peran", "staf"])
    assert gagal.exit_code != 0 and "sudah terdaftar" in gagal.output
    assert runner.invoke(args=["buat-pengguna", "--nama", "X", "--email", "x@y.id", "--peran", "dewa"]).exit_code != 0
