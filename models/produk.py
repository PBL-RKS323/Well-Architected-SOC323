from models import db, utcnow


class Produk(db.Model):
    __tablename__ = "produk"

    # Merek elektronik yang dijual toko (handphone, laptop, dll). Hanya merek yang punya produk
    # yang muncul di beranda; daftar ini juga mengisi pilihan di form & filter jelajah.
    MEREK = ["Apple", "Samsung", "Xiaomi", "Lenovo", "Asus", "Dell", "HP", "Acer"]
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
    # Satu spesifikasi per baris dengan format "Nama: Nilai", mis. "Prosesor: Apple M4"
    spesifikasi = db.Column(db.Text, nullable=True)
    garansi = db.Column(db.String(100), nullable=True)  # mis. "Garansi resmi 1 tahun"
    gambar = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @property
    def diskon_persen(self):
        """Persentase diskon dibulatkan, 0 jika tidak ada harga normal yang lebih tinggi."""
        if self.harga_normal and self.harga_normal > self.harga:
            return round((1 - self.harga / self.harga_normal) * 100)
        return 0

    @property
    def hemat(self):
        """Selisih harga normal dan harga jual (0 jika tidak diskon)."""
        return self.harga_normal - self.harga if self.diskon_persen else 0

    @property
    def daftar_spesifikasi(self):
        """Baris "Nama: Nilai" menjadi pasangan (nama, nilai) untuk tabel. Baris tanpa titik dua
        tetap ditampilkan dengan nama kosong."""
        hasil = []
        for baris in (self.spesifikasi or "").splitlines():
            baris = baris.strip()
            if not baris:
                continue
            nama, pemisah, nilai = baris.partition(":")
            hasil.append((nama.strip(), nilai.strip()) if pemisah and nilai.strip() else ("", baris))
        return hasil

    @property
    def ringkasan_spesifikasi(self):
        """3 nilai spesifikasi pertama untuk baris singkat di bawah nama, mis. "Apple M4 · 16GB · 512GB"."""
        return " · ".join(nilai for _, nilai in self.daftar_spesifikasi[:3])
