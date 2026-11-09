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
        """Menghitung nominal potongan dari subtotal belanja."""
        if not self.aktif:
            return 0
        if self.kuota and self.terpakai >= self.kuota:
            return 0
        if subtotal < self.min_belanja:
            return 0
        
        now = utcnow()
        if self.berlaku_mulai and now < self.berlaku_mulai:
            return 0
        if self.berlaku_sampai and now > self.berlaku_sampai:
            return 0

        if self.tipe == self.TIPE_PERSEN:
            potongan = (float(self.nilai) / 100.0) * float(subtotal)
            if self.maks_potongan and potongan > float(self.maks_potongan):
                potongan = float(self.maks_potongan)
            return round(potongan, 2)
        return min(float(self.nilai), float(subtotal))

    @classmethod
    def inisialisasi_bawaan(cls):
        """Membuat kupon standar e-shop (misal FIRSTPAY diskon 20%)."""
        if not cls.query.filter_by(kode="FIRSTPAY").first():
            kupon_baru = cls(
                kode="FIRSTPAY",
                deskripsi="Diskon 20% untuk transaksi perdana pelanggan baru",
                tipe=cls.TIPE_PERSEN,
                nilai=20.0,
                min_belanja=500000,
                maks_potongan=1000000,
                kuota=500,
                aktif=True
            )
            db.session.add(kupon_baru)
            db.session.commit()
