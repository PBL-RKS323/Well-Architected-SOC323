from models import db, utcnow


class KeranjangItem(db.Model):
    __tablename__ = "keranjang_item"
    __table_args__ = (db.UniqueConstraint("user_id", "produk_id", name="uq_keranjang_user_produk"),)

    MAKS_PER_PRODUK = 5  # batas pembelian satu produk dalam satu pesanan

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    produk_id = db.Column(db.Integer, db.ForeignKey("produk.id", ondelete="CASCADE"), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    produk = db.relationship("Produk")

    @property
    def batas(self):
        """Jumlah maksimal yang boleh ada di keranjang untuk item ini."""
        return min(self.produk.stok, self.MAKS_PER_PRODUK)

    @property
    def subtotal(self):
        return self.produk.harga * self.jumlah
