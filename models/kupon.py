from decimal import Decimal
from models import db, utcnow


class Kupon(db.Model):
    """Kupon promosi diskon checkout (voucher potongan belanja)."""
    __tablename__ = "kupon"

    TIPE_PERSEN = "persen"
    TIPE_NOMINAL = "nominal"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kode = db.Column(db.String(30), nullable=False, unique=True, index=True)
    deskripsi = db.Column(db.String(200), nullable=True)
    tipe = db.Column(db.String(10), nullable=False, default=TIPE_PERSEN)
    nilai = db.Column(db.Numeric(12, 2), nullable=False)  # 20.00 untuk 20% atau nominal Rp
    min_belanja = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    maks_potongan = db.Column(db.Numeric(12, 2), nullable=True)
    kuota = db.Column(db.Integer, nullable=False, default=100)
    terpakai = db.Column(db.Integer, nullable=False, default=0)
    berlaku_mulai = db.Column(db.DateTime, nullable=True)
    berlaku_sampai = db.Column(db.DateTime, nullable=True)
    aktif = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def hitung_diskon(self, subtotal):
        """Menghitung nominal potongan dari subtotal belanja (mengembalikan Decimal)."""
        sub = Decimal(str(subtotal))
        if not self.aktif:
            return Decimal("0")
        if self.kuota and self.terpakai >= self.kuota:
            return Decimal("0")
        if sub < Decimal(str(self.min_belanja or 0)):
            return Decimal("0")
        
        now = utcnow()
        if self.berlaku_mulai and now < self.berlaku_mulai:
            return Decimal("0")
        if self.berlaku_sampai and now > self.berlaku_sampai:
            return Decimal("0")

        if self.tipe == self.TIPE_PERSEN:
            potongan = (Decimal(str(self.nilai)) / Decimal("100")) * sub
            if self.maks_potongan and potongan > Decimal(str(self.maks_potongan)):
                potongan = Decimal(str(self.maks_potongan))
            return potongan.quantize(Decimal("0.01"))
        return min(Decimal(str(self.nilai)), sub)

    @classmethod
    def inisialisasi_bawaan(cls):
        """Membuat kupon standar e-shop (misal FIRSTPAY diskon 20%)."""
        if not cls.query.filter_by(kode="FIRSTPAY").first():
            kupon_baru = cls(
                kode="FIRSTPAY",
                deskripsi="Diskon 20% untuk transaksi perdana pelanggan baru",
                tipe=cls.TIPE_PERSEN,
                nilai=Decimal("20.00"),
                min_belanja=Decimal("500000"),
                maks_potongan=Decimal("1000000"),
                kuota=500,
                aktif=True
            )
            db.session.add(kupon_baru)
            db.session.commit()
