from models import db, utcnow


class Alamat(db.Model):
    """Alamat tersimpan milik pelanggan, dipakai untuk mengisi form checkout."""
    __tablename__ = "alamat"

    MAKS_PER_USER = 5

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = db.Column(db.String(30), nullable=False)  # contoh: Rumah, Kos, Kantor
    nama_penerima = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20), nullable=False)
    alamat = db.Column(db.String(255), nullable=False)
    kota = db.Column(db.String(60), nullable=False)
    kode_pos = db.Column(db.String(5), nullable=False)
    utama = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    @staticmethod
    def milik(user_id):
        return (Alamat.query.filter_by(user_id=user_id)
                .order_by(Alamat.utama.desc(), Alamat.created_at.asc()))

    def jadikan_utama(self):
        """Hanya satu alamat utama per pelanggan."""
        Alamat.query.filter(Alamat.user_id == self.user_id, Alamat.id != self.id).update(
            {"utama": False}, synchronize_session=False)
        self.utama = True
