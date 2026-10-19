import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _flag(name, default="0"):
    return os.getenv(name, default).strip() in ("1", "true", "True", "yes")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_NAME = os.getenv("APP_NAME", "Elektronik Store")

    # Upload gambar produk
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # batas request, file gambar sendiri dibatasi 2 MB

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


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "kunci-khusus-pengujian"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
