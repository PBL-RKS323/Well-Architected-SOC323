from models import db, utcnow


class Kategori(db.Model):
    """Kategori produk e-commerce (normalisasi katalog produk)."""
    __tablename__ = "kategori"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(60), nullable=False, unique=True, index=True)
    ikon = db.Column(db.String(50), nullable=True, default="grid")
    deskripsi = db.Column(db.String(255), nullable=True)
    urutan = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    # Relasi 1:N ke Produk
    produk_list = db.relationship("Produk", backref="kategori_rel", lazy="dynamic",
                                  foreign_keys="Produk.kategori_id")

    @classmethod
    def inisialisasi_bawaan(cls):
        """Membuat kategori default jika tabel kosong."""
        kategori_bawaan = [
            {"nama": "Handphone", "slug": "handphone", "ikon": "smartphone", "urutan": 1},
            {"nama": "Laptop", "slug": "laptop", "ikon": "laptop", "urutan": 2},
            {"nama": "Smartwatch", "slug": "smartwatch", "ikon": "watch", "urutan": 3},
            {"nama": "Tablet", "slug": "tablet", "ikon": "tablet", "urutan": 4},
            {"nama": "Audio", "slug": "audio", "ikon": "headphones", "urutan": 5},
            {"nama": "Aksesoris", "slug": "aksesoris", "ikon": "cable", "urutan": 6},
        ]
        ditambahkan = False
        for item in kategori_bawaan:
            if not cls.query.filter_by(slug=item["slug"]).first():
                cls_obj = cls(
                    nama=item["nama"],
                    slug=item["slug"],
                    ikon=item["ikon"],
                    urutan=item["urutan"],
                    aktif=True
                )
                db.session.add(cls_obj)
                ditambahkan = True
        if ditambahkan:
            db.session.commit()
