from models import db, utcnow


class Favorit(db.Model):
    """Daftar produk favorit/wishlist yang disimpan oleh pelanggan."""
    __tablename__ = "favorit"
    __table_args__ = (
        db.UniqueConstraint("user_id", "produk_id", name="uq_favorit_user_produk"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    produk_id = db.Column(db.Integer, db.ForeignKey("produk.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", backref=db.backref("daftar_favorit", cascade="all, delete-orphan", lazy="dynamic"))
    produk = db.relationship("Produk", backref=db.backref("daftar_peminat", cascade="all, delete-orphan", lazy="dynamic"))

    @classmethod
    def toggle(cls, user_id, produk_id):
        """Menambahkan atau menghapus produk dari wishlist."""
        ada = cls.query.filter_by(user_id=user_id, produk_id=produk_id).first()
        if ada:
            db.session.delete(ada)
            db.session.commit()
            return False  # Dihapus dari favorit
        baru = cls(user_id=user_id, produk_id=produk_id)
        db.session.add(baru)
        db.session.commit()
        return True  # Ditambahkan ke favorit

    @classmethod
    def is_favorit(cls, user_id, produk_id):
        """Mengecek apakah produk difavoritkan oleh user."""
        if not user_id:
            return False
        return cls.query.filter_by(user_id=user_id, produk_id=produk_id).first() is not None
