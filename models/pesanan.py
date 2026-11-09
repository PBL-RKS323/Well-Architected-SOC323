import secrets
from datetime import datetime, timedelta

from flask import current_app

from helpers.security_logger import WIB
from models import db, utcnow
from models.produk import Produk


class Pesanan(db.Model):
    __tablename__ = "pesanan"

    PREFIX_KODE = "ES"   # nomor pesanan: ES-YYMMDD-XXXXXX (ES = Elektronik Store)
    KODE_KURIR = "JJN"   # awalan nomor resi otomatis (kurir fiktif)

    # Status pesanan
    MENUNGGU_PEMBAYARAN = "menunggu_pembayaran"
    MENUNGGU_VERIFIKASI = "menunggu_verifikasi"
    DIPROSES = "diproses"
    DIKIRIM = "dikirim"
    SIAP_DIAMBIL = "siap_diambil"
    SELESAI = "selesai"
    DIBATALKAN = "dibatalkan"

    LABEL_STATUS = {
        MENUNGGU_PEMBAYARAN: "Menunggu Pembayaran",
        MENUNGGU_VERIFIKASI: "Menunggu Verifikasi",
        DIPROSES: "Diproses",
        DIKIRIM: "Dikirim",
        SIAP_DIAMBIL: "Siap Diambil",
        SELESAI: "Selesai",
        DIBATALKAN: "Dibatalkan",
    }
    STATUS_AKTIF = [MENUNGGU_PEMBAYARAN, MENUNGGU_VERIFIKASI, DIPROSES, DIKIRIM, SIAP_DIAMBIL]
    STATUS_LUNAS = [DIPROSES, DIKIRIM, SIAP_DIAMBIL, SELESAI]  # pembayaran sudah diterima admin

    # Perpindahan status yang sah. Status lain ditolak walau request dimanipulasi.
    TRANSISI = {
        MENUNGGU_PEMBAYARAN: {MENUNGGU_VERIFIKASI, DIBATALKAN},
        MENUNGGU_VERIFIKASI: {DIPROSES, MENUNGGU_PEMBAYARAN, DIBATALKAN},
        DIPROSES: {DIKIRIM, SIAP_DIAMBIL, DIBATALKAN},
        DIKIRIM: {SELESAI},
        SIAP_DIAMBIL: {SELESAI},
        SELESAI: set(),
        DIBATALKAN: set(),
    }

    # Metode pengiriman
    KURIR = "kurir"
    AMBIL = "ambil"
    LABEL_PENGIRIMAN = {KURIR: "Dikirim kurir", AMBIL: "Ambil di toko"}

    TRANSFER = "transfer"
    LABEL_PEMBAYARAN = {TRANSFER: "Transfer Bank"}

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default=MENUNGGU_PEMBAYARAN, index=True)

    metode_pengiriman = db.Column(db.String(10), nullable=False)
    metode_pembayaran = db.Column(db.String(20), nullable=False, default=TRANSFER)
    nama_penerima = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20), nullable=False)
    alamat = db.Column(db.String(255), nullable=True)  # kosong jika ambil di toko
    kota = db.Column(db.String(60), nullable=True)
    kode_pos = db.Column(db.String(5), nullable=True)
    catatan = db.Column(db.String(200), nullable=True)

    # Harga dihitung di server saat checkout, bukan dari input pengguna
    diskon = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    kupon_id = db.Column(db.Integer, db.ForeignKey('kupon.id', ondelete='SET NULL'), nullable=True, index=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    ongkir = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False)

    batas_bayar = db.Column(db.DateTime, nullable=False)  # diperpanjang jika bukti bayar ditolak
    bukti_bayar = db.Column(db.String(255), nullable=True)  # nama file di folder privat
    bukti_diunggah_at = db.Column(db.DateTime, nullable=True)
    alasan_tolak = db.Column(db.String(200), nullable=True)  # alasan bukti bayar ditolak / pesanan dibatalkan
    nomor_resi = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User")
    items = db.relationship("PesananItem", backref="pesanan", cascade="all, delete-orphan",
                            order_by="PesananItem.id")
    riwayat = db.relationship("PesananRiwayat", backref="pesanan", cascade="all, delete-orphan",
                              order_by="PesananRiwayat.id")

    @staticmethod
    def buat_kode():
        """Kode acak, contoh ES-261019-A1B2C3. Bagian acak mencegah kode pesanan mudah ditebak."""
        while True:
            kode = f"{Pesanan.PREFIX_KODE}-{datetime.now(WIB):%y%m%d}-{secrets.token_hex(3).upper()}"
            if not Pesanan.query.filter_by(kode=kode).first():
                return kode

    @staticmethod
    def buat_resi():
        """Nomor resi otomatis: 3 huruf kode kurir + 10 angka, contoh JJN4821093756.
        JJN adalah kurir fiktif untuk demo (bukan JNE/J&T asli)."""
        while True:
            resi = Pesanan.KODE_KURIR + "".join(str(secrets.randbelow(10)) for _ in range(10))
            if not Pesanan.query.filter_by(nomor_resi=resi).first():
                return resi

    @property
    def label_status(self):
        return self.LABEL_STATUS.get(self.status, self.status)

    @property
    def jumlah_barang(self):
        return sum(i.jumlah for i in self.items)

    @staticmethod
    def hitung_batas_bayar():
        return utcnow() + timedelta(hours=current_app.config["BATAS_BAYAR_JAM"])

    @property
    def langkah(self):
        """Urutan langkah untuk tampilan lacak pesanan, sesuai metode pengiriman."""
        akhir = [(self.DIKIRIM, "Dikirim"), (self.SELESAI, "Diterima")] if self.metode_pengiriman == self.KURIR \
            else [(self.SIAP_DIAMBIL, "Siap diambil"), (self.SELESAI, "Sudah diambil")]
        return [(self.MENUNGGU_PEMBAYARAN, "Pesanan dibuat"), (self.MENUNGGU_VERIFIKASI, "Bukti bayar dikirim"),
                (self.DIPROSES, "Pembayaran diterima")] + akhir

    def waktu_status(self, status):
        """Waktu terakhir pesanan masuk ke status tertentu (untuk timeline)."""
        for r in reversed(self.riwayat):
            if r.status == status:
                return r.created_at
        return None

    def bisa_ke(self, status_baru):
        return status_baru in self.TRANSISI.get(self.status, set())

    def ubah_status(self, status_baru, oleh, keterangan=None):
        """Pindah status jika transisinya sah dan belum didahului proses lain.

        UPDATE bersyarat (WHERE status = status lama) mencegah race condition, misalnya pelanggan
        membatalkan tepat saat admin memverifikasi sehingga stok dikembalikan dua kali.
        """
        lama = self.status
        if not self.bisa_ke(status_baru):
            return False
        berubah = (Pesanan.query.filter_by(id=self.id, status=lama)
                   .update({"status": status_baru, "updated_at": utcnow()}, synchronize_session=False))
        if not berubah:
            return False
        self.status = status_baru
        self.riwayat.append(PesananRiwayat(status=status_baru, oleh=oleh, keterangan=keterangan))
        if status_baru == self.DIBATALKAN:
            self._kembalikan_stok()
        return True

    def _kembalikan_stok(self):
        for item in self.items:
            if item.produk_id:  # produk mungkin sudah dihapus admin
                Produk.query.filter_by(id=item.produk_id).update(
                    {Produk.stok: Produk.stok + item.jumlah}, synchronize_session=False)

    @classmethod
    def batalkan_kedaluwarsa(cls):
        """Batalkan pesanan yang tidak dibayar melewati batas waktu, stoknya dikembalikan."""
        lewat = cls.query.filter(cls.status == cls.MENUNGGU_PEMBAYARAN, cls.batas_bayar < utcnow()).all()
        dibatalkan = []
        for p in lewat:
            if p.ubah_status(cls.DIBATALKAN, "sistem", "Melewati batas waktu pembayaran"):
                p.alasan_tolak = "Melewati batas waktu pembayaran."
                dibatalkan.append(p)
        if lewat:
            db.session.commit()
        return dibatalkan


class PesananItem(db.Model):
    __tablename__ = "pesanan_item"

    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey("pesanan.id", ondelete="CASCADE"), nullable=False, index=True)
    # SET NULL: riwayat pesanan tetap ada walau produknya dihapus dari katalog
    produk_id = db.Column(db.Integer, db.ForeignKey("produk.id", ondelete="SET NULL"), nullable=True)
    # Salinan data produk saat checkout (harga produk bisa berubah setelahnya)
    nama_produk = db.Column(db.String(100), nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    harga = db.Column(db.Numeric(12, 2), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)

    produk = db.relationship("Produk")

    @property
    def subtotal(self):
        return self.harga * self.jumlah


class PesananRiwayat(db.Model):
    __tablename__ = "pesanan_riwayat"

    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey("pesanan.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False)
    oleh = db.Column(db.String(20), nullable=False)  # pelanggan / admin / sistem
    keterangan = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
