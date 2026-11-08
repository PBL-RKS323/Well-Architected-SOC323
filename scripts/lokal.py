"""Satu paket untuk laptop Windows: dipanggil oleh setup.bat (sekali) dan jalankan.bat (setiap demo).

Database bawaan adalah PostgreSQL portabel: zip resmi EnterpriseDB (tanpa installer, tanpa hak admin)
yang disimpan di folder .lokal/ proyek ini dan hanya menerima koneksi dari laptop ini (127.0.0.1).
Pilihan lain: PostgreSQL/MySQL yang sudah terpasang, atau SQLite untuk latihan.

    python scripts/lokal.py setup      -> .env, database, tabel (migrasi), produk contoh, akun admin
    python scripts/lokal.py jalankan   -> nyalakan PostgreSQL portabel + aplikasi, buka browser
"""
import getpass
import os
import secrets
import subprocess
import sys
import threading
import urllib.request
import webbrowser
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
PY = sys.executable

LOKAL = ROOT / ".lokal"
PGSQL = LOKAL / "pgsql"
PGDATA = LOKAL / "pgdata"
PG_LOG = LOKAL / "postgres.log"
PG_SUPER_PW = LOKAL / "kata_sandi_postgres.txt"
PG_VERSI = "17.6-1"
PG_URL = f"https://get.enterprisedb.com/postgresql/postgresql-{PG_VERSI}-windows-x64-binaries.zip"
PG_PORT = 5433  # bukan 5432, agar tidak bentrok dengan PostgreSQL lain yang mungkin sudah terpasang
DB_NAMA, DB_USER = "db_ecommerce", "ecommerce_user"
URL_APLIKASI = "http://127.0.0.1:5000"


def info(pesan):
    print(f"  - {pesan}", flush=True)


# ------------------------------------------------------------------ .env
def baca_env():
    data = {}
    if ENV.exists():
        for baris in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in baris and not baris.lstrip().startswith("#"):
                kunci, nilai = baris.split("=", 1)
                data[kunci.strip()] = nilai.strip()
    return data


def tulis_env(database_url, portabel):
    hasil = []
    for baris in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if baris.startswith("SECRET_KEY="):
            baris = "SECRET_KEY=" + secrets.token_hex(32)
        elif baris.startswith("DATABASE_URL="):
            baris = "DATABASE_URL=" + database_url
        hasil.append(baris)
    hasil += ["", "# Dibuat setup.bat. 1 = PostgreSQL portabel di folder .lokal/ dinyalakan otomatis oleh jalankan.bat",
              f"DB_PORTABEL={1 if portabel else 0}"]
    ENV.write_text("\n".join(hasil) + "\n", encoding="utf-8")


def pilih_database():
    print("\nPilih database:")
    print("  [1] PostgreSQL portabel: otomatis, tanpa instal apa pun (DIREKOMENDASIKAN untuk demo)")
    print("  [2] PostgreSQL / MySQL yang sudah terpasang di laptop ini (isi DATABASE_URL sendiri)")
    print("  [3] SQLite: hanya untuk latihan, TIDAK memenuhi syarat 'wajib MySQL/MariaDB/PostgreSQL'")
    while True:
        pilihan = input("Pilihan [1]: ").strip() or "1"
        if pilihan in ("1", "2", "3"):
            return pilihan


# ------------------------------------------------------------------ PostgreSQL portabel
def pg(nama):
    return str(PGSQL / "bin" / f"{nama}.exe")


def unduh_postgres():
    if (PGSQL / "bin" / "postgres.exe").exists():
        return
    LOKAL.mkdir(exist_ok=True)
    zip_path = LOKAL / f"postgresql-{PG_VERSI}-windows-x64-binaries.zip"
    if not zip_path.exists():
        info(f"Mengunduh PostgreSQL {PG_VERSI} portabel (sekitar 330 MB, hanya sekali)...")
        info(f"Internet lambat? Unduh {PG_URL} di tempat lain, taruh di folder .lokal, lalu ulangi setup.bat")
        sementara = zip_path.with_suffix(".part")
        with urllib.request.urlopen(PG_URL, timeout=60) as respons, open(sementara, "wb") as f:
            total, dapat = int(respons.headers.get("Content-Length", 0)), 0
            while potongan := respons.read(1 << 20):
                f.write(potongan)
                dapat += len(potongan)
                if total:
                    print(f"\r    {dapat >> 20} / {total >> 20} MB", end="", flush=True)
        print()
        sementara.replace(zip_path)
    info("Mengekstrak PostgreSQL (tanpa pgAdmin & dokumentasi)...")
    lewati = ("pgsql/pgAdmin 4/", "pgsql/doc/", "pgsql/StackBuilder/", "pgsql/symbols/", "pgsql/include/")
    with zipfile.ZipFile(zip_path) as z:
        for anggota in z.infolist():
            if not anggota.filename.startswith(lewati):
                z.extract(anggota, LOKAL)
    zip_path.unlink()


def kata_sandi_super():
    """Kata sandi superuser 'postgres' (hanya untuk mengelola database lokal, mis. lewat pgAdmin)."""
    if not PG_SUPER_PW.exists():
        PG_SUPER_PW.write_text(secrets.token_urlsafe(18), encoding="utf-8")
    return PG_SUPER_PW.read_text(encoding="utf-8").strip()


def init_postgres(pw_super):
    if (PGDATA / "PG_VERSION").exists():
        return
    info("Membuat cluster database di .lokal/pgdata ...")
    pwfile = LOKAL / "pw.tmp"
    pwfile.write_text(pw_super, encoding="utf-8")
    try:
        subprocess.run([pg("initdb"), "-D", str(PGDATA), "-U", "postgres", "-E", "UTF8", "--locale=C",
                        "--auth=scram-sha-256", f"--pwfile={pwfile}"], check=True, stdout=subprocess.DEVNULL)
    finally:
        pwfile.unlink(missing_ok=True)


def postgres_menyala():
    return subprocess.run([pg("pg_ctl"), "status", "-D", str(PGDATA)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def nyalakan_postgres():
    """Mengembalikan True jika dinyalakan oleh panggilan ini (berarti nanti dimatikan lagi)."""
    if postgres_menyala():
        return False
    info(f"Menyalakan PostgreSQL di 127.0.0.1:{PG_PORT} ...")
    subprocess.run([pg("pg_ctl"), "start", "-D", str(PGDATA), "-l", str(PG_LOG), "-w",
                    "-o", f"-p {PG_PORT} -c listen_addresses=127.0.0.1"], check=True, stdout=subprocess.DEVNULL)
    return True


def matikan_postgres():
    info("Mematikan PostgreSQL...")
    subprocess.run([pg("pg_ctl"), "stop", "-D", str(PGDATA), "-m", "fast", "-w"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def siapkan_database(pw_super, pw_app):
    """User aplikasi dibuat terpisah dari superuser (bukan superuser, hanya pemilik database toko)."""
    env = {**os.environ, "PGPASSWORD": pw_super}

    def sql(perintah):
        return subprocess.run([pg("psql"), "-h", "127.0.0.1", "-p", str(PG_PORT), "-U", "postgres", "-d", "postgres",
                               "-v", "ON_ERROR_STOP=1", "-tAc", perintah],
                              env=env, check=True, capture_output=True, text=True).stdout.strip()

    if not sql(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}'"):
        sql(f"CREATE ROLE {DB_USER} LOGIN PASSWORD '{pw_app}'")
        info(f"User database '{DB_USER}' dibuat.")
    if not sql(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAMA}'"):
        sql(f"CREATE DATABASE {DB_NAMA} OWNER {DB_USER} ENCODING 'UTF8'")
        info(f"Database '{DB_NAMA}' dibuat.")


# ------------------------------------------------------------------ Flask
def flask(*argumen):
    subprocess.run([PY, "-m", "flask", *argumen], cwd=ROOT, check=True)


_CEK_ADMIN = """
from app import create_app
from models.user import User
app = create_app()
with app.app_context():
    raise SystemExit(0 if User.query.filter_by(role=User.ROLE_ADMIN).first() else 1)
"""

# Kata sandi dikirim lewat stdin (bukan argumen perintah) agar tidak terlihat di daftar proses
_BUAT_ADMIN = """
import sys
from app import create_app
username, nama, email = sys.argv[1:4]
password = sys.stdin.readline().rstrip("\\n")
hasil = create_app().test_cli_runner().invoke(args=["seed-admin", "--username", username, "--nama", nama,
                                                   "--email", email, "--password", password])
print(hasil.output.strip())
raise SystemExit(hasil.exit_code)
"""


def ada_admin():
    return subprocess.run([PY, "-c", _CEK_ADMIN], cwd=ROOT).returncode == 0


def baca_sandi(label):
    return getpass.getpass(label) if sys.stdin.isatty() else input(label)


def buat_admin():
    print("\nBuat akun admin toko.")
    print("Kata sandi: min. 8 karakter, ada huruf besar, huruf kecil, angka, dan simbol (mis. Toko#2026).")
    for _ in range(3):
        username = input("Username admin : ").strip()
        nama = input("Nama lengkap   : ").strip()
        email = input("Email          : ").strip()
        sandi = baca_sandi("Kata sandi     : ")
        if sandi != baca_sandi("Ulangi sandi   : "):
            print("  Kata sandi tidak sama, ulangi.\n")
            continue
        hasil = subprocess.run([PY, "-c", _BUAT_ADMIN, username, nama, email], cwd=ROOT,
                               input=sandi + "\n", text=True)
        if hasil.returncode == 0:
            return
        print("  Ulangi.\n")
    raise SystemExit("Akun admin belum dibuat. Jalankan setup.bat lagi.")


# ------------------------------------------------------------------ perintah
def setup():
    env = baca_env()
    if env.get("SECRET_KEY") and "ganti-dengan" not in env["SECRET_KEY"] and env.get("DATABASE_URL"):
        info(".env sudah ada, dipakai apa adanya (hapus file .env jika ingin memilih database ulang).")
    else:
        pilihan = pilih_database()
        if pilihan == "1":
            url = f"postgresql+psycopg2://{DB_USER}:{secrets.token_urlsafe(18)}@127.0.0.1:{PG_PORT}/{DB_NAMA}"
        elif pilihan == "2":
            print("Contoh: postgresql+psycopg2://user:sandi@127.0.0.1:5432/db_ecommerce")
            print("        mysql+pymysql://root:sandi@127.0.0.1:3306/db_ecommerce (database harus sudah dibuat)")
            url = input("DATABASE_URL: ").strip()
        else:
            url = "sqlite:///toko_lokal.db"
        tulis_env(url, portabel=pilihan == "1")
        info(".env dibuat dengan SECRET_KEY acak.")
        env = baca_env()

    dinyalakan = False
    try:
        if env.get("DB_PORTABEL") == "1":
            unduh_postgres()
            pw_super = kata_sandi_super()
            init_postgres(pw_super)
            dinyalakan = nyalakan_postgres()
            siapkan_database(pw_super, urlsplit(env["DATABASE_URL"]).password)
        info("Membuat / memperbarui tabel (flask db upgrade)...")
        flask("db", "upgrade")
        info("Mengisi produk contoh (flask seed-katalog)...")
        flask("seed-katalog")
        if ada_admin():
            info("Akun admin sudah ada.")
        else:
            buat_admin()
    finally:
        if dinyalakan:
            matikan_postgres()


def jalankan():
    env = baca_env()
    if not env.get("DATABASE_URL"):
        raise SystemExit("File .env belum ada. Jalankan setup.bat dulu.")
    dinyalakan = False
    try:
        if env.get("DB_PORTABEL") == "1":
            dinyalakan = nyalakan_postgres()
        flask("db", "upgrade")  # menerapkan migrasi baru jika kode baru saja di-update (git pull)
        threading.Timer(3, webbrowser.open, args=[URL_APLIKASI]).start()
        print(f"\n  Aplikasi berjalan di {URL_APLIKASI}  -  tekan Ctrl+C untuk berhenti.\n", flush=True)
        subprocess.run([PY, "-m", "flask", "run"], cwd=ROOT)
    except KeyboardInterrupt:
        pass
    finally:
        if dinyalakan:
            matikan_postgres()


if __name__ == "__main__":
    perintah = sys.argv[1] if len(sys.argv) > 1 else ""
    if perintah == "setup":
        setup()
    elif perintah == "jalankan":
        jalankan()
    else:
        raise SystemExit("Pemakaian: python scripts/lokal.py setup|jalankan")
