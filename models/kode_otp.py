import hashlib
import hmac
import secrets
from datetime import timedelta

from flask import current_app

from models import db, utcnow


class OtpTerlaluSering(Exception):
    """Kode diminta terlalu cepat / terlalu banyak. `detik` = sisa waktu tunggu."""

    def __init__(self, detik):
        super().__init__(detik)
        self.detik = detik


class KodeOtp(db.Model):
    """Kode 6 digit yang dikirim ke email.

    Yang disimpan hanya HMAC-SHA256 dari kode (kunci = SECRET_KEY), jadi isi tabel yang bocor tidak bisa
    dipakai. Kode berlaku 10 menit, hangus setelah 5 kali salah, dan hanya kode terbaru yang berlaku.
    """
    __tablename__ = "kode_otp"

    RESET_PASSWORD = "reset_password"
    VERIFIKASI_EMAIL = "verifikasi_email"
    LOGIN = "login"
    JUDUL = {
        RESET_PASSWORD: "Atur ulang kata sandi",
        VERIFIKASI_EMAIL: "Verifikasi email",
        LOGIN: "Masuk ke panel toko",
    }

    # Hasil pemeriksaan kode
    OK, SALAH, KEDALUWARSA, HANGUS = "ok", "salah", "kedaluwarsa", "hangus"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tujuan = db.Column(db.String(30), nullable=False)
    kode_hash = db.Column(db.String(64), nullable=False)
    kedaluwarsa = db.Column(db.DateTime, nullable=False)
    percobaan = db.Column(db.Integer, nullable=False, default=0)
    dipakai_at = db.Column(db.DateTime, nullable=True)  # terisi saat dipakai atau digantikan kode baru
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    @staticmethod
    def _hash(user_id, tujuan, kode):
        kunci = current_app.config["SECRET_KEY"].encode()
        return hmac.new(kunci, f"{user_id}:{tujuan}:{kode}".encode(), hashlib.sha256).hexdigest()

    @classmethod
    def _milik(cls, user, tujuan):
        return cls.query.filter_by(user_id=user.id, tujuan=tujuan)

    @classmethod
    def buat(cls, user, tujuan):
        """Membuat kode baru (kode lama untuk tujuan yang sama langsung tidak berlaku).
        Mengembalikan kode asli untuk dikirim lewat email; yang disimpan hanya hash-nya."""
        cfg = current_app.config
        sekarang = utcnow()
        terakhir = cls._milik(user, tujuan).order_by(cls.created_at.desc()).first()
        if terakhir:
            jeda = (sekarang - terakhir.created_at).total_seconds()
            if jeda < cfg["OTP_JEDA_KIRIM_DETIK"]:
                raise OtpTerlaluSering(int(cfg["OTP_JEDA_KIRIM_DETIK"] - jeda) + 1)
        sejam = cls._milik(user, tujuan).filter(cls.created_at > sekarang - timedelta(hours=1)).count()
        if sejam >= cfg["OTP_MAKS_PER_JAM"]:
            raise OtpTerlaluSering(3600)

        cls._milik(user, tujuan).filter(cls.dipakai_at.is_(None)).update({"dipakai_at": sekarang})
        kode = f"{secrets.randbelow(10 ** 6):06d}"
        db.session.add(cls(user_id=user.id, tujuan=tujuan, kode_hash=cls._hash(user.id, tujuan, kode),
                           kedaluwarsa=sekarang + timedelta(minutes=cfg["OTP_BERLAKU_MENIT"])))
        return kode

    @classmethod
    def periksa(cls, user, tujuan, kode):
        """Mencocokkan kode dengan kode terbaru yang masih berlaku. Pemanggil yang melakukan commit."""
        otp = (cls._milik(user, tujuan).filter(cls.dipakai_at.is_(None), cls.kedaluwarsa > utcnow())
               .order_by(cls.created_at.desc()).first())
        if otp is None:
            return cls.KEDALUWARSA
        if otp.percobaan >= current_app.config["OTP_MAKS_PERCOBAAN"]:
            return cls.HANGUS
        if hmac.compare_digest(otp.kode_hash, cls._hash(user.id, tujuan, (kode or "").strip())):
            otp.dipakai_at = utcnow()
            return cls.OK
        otp.percobaan += 1
        if otp.percobaan >= current_app.config["OTP_MAKS_PERCOBAAN"]:
            otp.dipakai_at = utcnow()
            return cls.HANGUS
        return cls.SALAH
