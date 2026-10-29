import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _flag(name, default="0"):
    return os.getenv(name, default).strip() in ("1", "true", "True", "yes")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Koneksi DB di pool dicek dulu sebelum dipakai: jika PostgreSQL sempat restart (mis. update otomatis),
    # koneksi mati diganti baru, bukan jadi error 500 untuk pengunjung pertama.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}

    APP_NAME = os.getenv("APP_NAME", "Elektronik Store")
    # Isi 1 di server publik: tampilkan pemberitahuan bahwa ini toko demo (rekening & produk bukan asli)
    DEMO_MODE = _flag("DEMO_MODE")

    # Upload gambar produk
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # batas request, file gambar sendiri dibatasi 2 MB
    # Bukti bayar berisi data pribadi: disimpan di luar folder static, hanya bisa dibuka pemilik & admin
    BUKTI_BAYAR_FOLDER = os.getenv("BUKTI_BAYAR_FOLDER", os.path.join(BASE_DIR, "instance", "bukti_bayar"))

    # Checkout & pembayaran (data toko masih contoh, ganti lewat .env)
    ONGKIR_FLAT = int(os.getenv("ONGKIR_FLAT", "15000"))
    BATAS_BAYAR_JAM = 24  # pesanan otomatis batal jika belum dibayar
    MAKS_PESANAN_BELUM_BAYAR = 3  # mencegah stok "ditahan" dengan banyak pesanan yang tidak dibayar
    TOKO_ALAMAT = os.getenv("TOKO_ALAMAT", "Jl. Ahmad Yani, Batam Centre, Kota Batam")
    TOKO_JAM_BUKA = os.getenv("TOKO_JAM_BUKA", "Senin-Sabtu, 09.00-20.00 WIB")
    BANK_NAMA = os.getenv("BANK_NAMA", "BCA")
    BANK_NOREK = os.getenv("BANK_NOREK", "1234567890")
    BANK_ATAS_NAMA = os.getenv("BANK_ATAS_NAMA", APP_NAME)

    # Keamanan sesi
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _flag("SESSION_COOKIE_SECURE")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # hanya untuk login dengan "Ingat saya"

    # Proteksi brute force login
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 5

    TRUST_PROXY = _flag("TRUST_PROXY")
    SECURITY_LOG_FILE = os.getenv("SECURITY_LOG_FILE", os.path.join(BASE_DIR, "logs", "security.log"))

    # Email (Flask-Mail) untuk kode OTP: lupa kata sandi, verifikasi email, OTP login panel.
    # Gmail: MAIL_USERNAME = alamat Gmail pengirim, MAIL_PASSWORD = App Password 16 huruf (BUKAN kata sandi
    # Gmail). Selama kosong, fitur email/OTP otomatis nonaktif dan login tetap berjalan seperti biasa.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = (APP_NAME, MAIL_USERNAME) if MAIL_USERNAME else None

    # Kode OTP 6 digit
    OTP_BERLAKU_MENIT = 10
    OTP_MAKS_PERCOBAAN = 5      # salah 5x -> kode hangus
    OTP_JEDA_KIRIM_DETIK = 60   # jarak minimal kirim ulang
    OTP_MAKS_PER_JAM = 5        # mencegah email dibanjiri kode
    # Isi 1 agar Admin & Staf wajib memasukkan kode OTP dari email setiap login (2 langkah).
    # Pastikan email akun panel sudah email asli sebelum menyalakan ini.
    OTP_LOGIN_PANEL = _flag("OTP_LOGIN_PANEL")

    # Login dengan Google (OAuth 2.0 / OpenID Connect). Kosong = tombol Google tidak tampil.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or None
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET") or None


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "kunci-khusus-pengujian"
    # Default SQLite di memori. Isi TEST_DATABASE_URL untuk menguji di PostgreSQL (database khusus uji!)
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    # Email & Google mati secara default saat pengujian; tes email menyalakannya sendiri
    MAIL_USERNAME = MAIL_PASSWORD = MAIL_DEFAULT_SENDER = None
    MAIL_SUPPRESS_SEND = True
    OTP_LOGIN_PANEL = False
    GOOGLE_CLIENT_ID = GOOGLE_CLIENT_SECRET = None
