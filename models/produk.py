from models import db, utcnow


class Produk(db.Model):
    __tablename__ = "produk"

    # Fokus toko: produk elektronik dari ekosistem brand tertentu
    MEREK = ["Apple", "Samsung", "Xiaomi"]
    KATEGORI = ["Handphone", "Laptop", "Smartwatch", "Tablet", "Audio", "Aksesoris"]
    STOK_MENIPIS = 5

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_produk = db.Column(db.String(100), nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    kategori = db.Column(db.String(30), nullable=False)
    harga = db.Column(db.Numeric(12, 2), nullable=False)
    harga_normal = db.Column(db.Numeric(12, 2), nullable=True)  # harga sebelum diskon (opsional)
    stok = db.Column(db.Integer, nullable=False, default=0)
    deskripsi = db.Column(db.Text, nullable=True)
    gambar = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @property
    def diskon_persen(self):
        """Persentase diskon dibulatkan, 0 jika tidak ada harga normal yang lebih tinggi."""
        if self.harga_normal and self.harga_normal > self.harga:
            return round((1 - self.harga / self.harga_normal) * 100)
        return 0
