from models import db, utcnow


class Pembayaran(db.Model):
    """Transaksi pembayaran pesanan untuk audit finansial & verifikasi admin."""
    __tablename__ = "pembayaran"

    STATUS_PENDING = "pending"
    STATUS_DIVERIFIKASI = "diverifikasi"
    STATUS_DITOLAK = "ditolak"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey("pesanan.id", ondelete="CASCADE"), nullable=False, index=True)
    metode_pembayaran = db.Column(db.String(30), nullable=False, default="transfer")
    jumlah = db.Column(db.Numeric(12, 2), nullable=False)
    bukti_bayar = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    diverifikasi_oleh = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    catatan_verifikasi = db.Column(db.String(255), nullable=True)
    waktu_bayar = db.Column(db.DateTime, nullable=False, default=utcnow)
    waktu_verifikasi = db.Column(db.DateTime, nullable=True)

    pesanan = db.relationship("Pesanan", backref=db.backref("daftar_transaksi", cascade="all, delete-orphan"))
    verifikator = db.relationship("User", foreign_keys=[diverifikasi_oleh])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
