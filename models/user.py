import hashlib
from datetime import timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from models import db, utcnow

# Hash pembanding agar waktu respons login sama saat email tidak terdaftar
# (mencegah enumerasi akun lewat perbedaan waktu)
_DUMMY_HASH = generate_password_hash("dummy-password-pembanding")


class User(db.Model):
    __tablename__ = "users"

    ROLE_ADMIN = "admin"
    ROLE_STAF = "staf"
    ROLE_CUSTOMER = "customer"
    LABEL_ROLE = {ROLE_ADMIN: "Admin", ROLE_STAF: "Staf Toko", ROLE_CUSTOMER: "Pelanggan"}

    # RBAC: hak akses ditentukan izin per peran, bukan nama peran. Kode selalu mengecek
    # punya_izin(...), jadi menambah/mengubah peran cukup di tabel ini.
    #   panel          : masuk panel /admin (dasbor)
    #   kelola_produk  : tambah, ubah, hapus produk
    #   kelola_pesanan : verifikasi pembayaran & ubah status pesanan, lihat bukti bayar
    #   kelola_user    : daftar akun, ubah peran, aktif/nonaktif, buka kunci
    #   lihat_laporan  : laporan transaksi & ekspor CSV (data keuangan seluruh toko)
    #   belanja        : keranjang, checkout, pesanan sendiri, alamat, ulasan
    IZIN = {
        ROLE_ADMIN: {"panel", "kelola_produk", "kelola_pesanan", "kelola_user", "lihat_laporan"},
        ROLE_STAF: {"panel", "kelola_produk", "kelola_pesanan"},
        ROLE_CUSTOMER: {"belanja"},
    }

    id = db.Column(db.Integer, primary_key=True)
    # username = identitas internal (dipakai di log), nama_lengkap = nama yang tampil di halaman
    username = db.Column(db.String(50), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False, default="", server_default="")
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_CUSTOMER)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    # Akun nonaktif tidak bisa login dan sesinya langsung tidak berlaku (pengganti hapus akun,
    # agar riwayat pesanan tetap utuh)
    aktif = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    # Nama file foto profil di static/uploads/avatar (sudah di-encode ulang tanpa metadata EXIF)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def sesi_token(self):
        """Sidik hash kata sandi untuk disimpan di sesi. Berubah setiap ganti kata sandi, sehingga
        sesi lama di perangkat lain otomatis tidak berlaku lagi."""
        return hashlib.sha256(self.password_hash.encode()).hexdigest()[:16]

    @staticmethod
    def check_dummy_password(password):
        check_password_hash(_DUMMY_HASH, password)

    def punya_izin(self, izin):
        return izin in self.IZIN.get(self.role, set())

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_staf_toko(self):
        """Admin atau staf: pengguna panel toko (tidak berbelanja)."""
        return self.punya_izin("panel")

    @property
    def label_role(self):
        return self.LABEL_ROLE.get(self.role, self.role)

    @property
    def display_name(self):
        return self.nama_lengkap or self.username

    @property
    def initials(self):
        parts = self.display_name.split()
        return "".join(p[0] for p in parts[:2]).upper() or "?"

    def is_locked(self):
        return self.locked_until is not None and self.locked_until > utcnow()

    def register_failed_login(self, max_attempts, lockout_minutes):
        """Menambah hitungan gagal login. Mengembalikan True jika akun baru saja dikunci."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = utcnow() + timedelta(minutes=lockout_minutes)
            self.failed_login_attempts = 0
            return True
        return False

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
