from models import db, utcnow
from models.pesanan import Pesanan, PesananItem


class Ulasan(db.Model):
    """Ulasan produk dari pembeli.

    Hanya akun yang punya pesanan SELESAI berisi produk tersebut yang boleh mengulas (mencegah ulasan
    palsu dari akun yang tidak pernah membeli). Satu ulasan per produk per akun, bisa diubah.
    Staf toko bisa membalas satu kali (balasan bisa diubah) dan menghapus ulasan yang melanggar.
    """
    __tablename__ = "ulasan"
    __table_args__ = (
        db.UniqueConstraint("produk_id", "user_id", name="uq_ulasan_produk_user"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_ulasan_rating"),
    )

    MAKS_KOMENTAR = 1000
    TAMPIL_AWAL = 5  # jumlah ulasan yang langsung tampil di halaman produk

    id = db.Column(db.Integer, primary_key=True)
    produk_id = db.Column(db.Integer, db.ForeignKey("produk.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = db.Column(db.SmallInteger, nullable=False)
    komentar = db.Column(db.Text, nullable=True)
    balasan = db.Column(db.Text, nullable=True)
    dibalas_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Ulasan ikut terhapus bersama produknya
    produk = db.relationship("Produk", backref=db.backref("daftar_ulasan", cascade="all, delete-orphan"))
    user = db.relationship("User")

    @property
    def diubah(self):
        return (self.updated_at - self.created_at).total_seconds() > 60

    @staticmethod
    def boleh_mengulas(user, produk_id):
        """True jika user pernah menyelesaikan pesanan yang berisi produk ini."""
        if user is None or not user.punya_izin("belanja"):
            return False
        return db.session.query(PesananItem.id).join(Pesanan, PesananItem.pesanan_id == Pesanan.id).filter(
            Pesanan.user_id == user.id, Pesanan.status == Pesanan.SELESAI,
            PesananItem.produk_id == produk_id).first() is not None

    @staticmethod
    def ringkasan(produk_id):
        """Rata-rata rating, jumlah ulasan, dan sebaran bintang 5..1 (untuk bar di halaman produk)."""
        baris = (db.session.query(Ulasan.rating, db.func.count(Ulasan.id))
                 .filter(Ulasan.produk_id == produk_id).group_by(Ulasan.rating).all())
        sebaran = {bintang: 0 for bintang in range(5, 0, -1)}
        for rating, jumlah in baris:
            sebaran[rating] = jumlah
        total = sum(sebaran.values())
        rata = sum(r * n for r, n in sebaran.items()) / total if total else 0
        return {"rata": round(rata, 1), "jumlah": total, "sebaran": sebaran}
