import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, RadioField, SubmitField, BooleanField
from wtforms.validators import DataRequired, InputRequired, Length, Regexp, Optional, AnyOf, ValidationError

from forms.auth_form import NAMA_POLICY
from models.pesanan import Pesanan

TELEPON_POLICY = r"^(\+62|62|0)8[0-9]{7,12}$"
RESI_POLICY = r"^[A-Za-z0-9-]{5,50}$"


def _rapikan(teks):
    return teks.strip() if teks else teks


def _hapus_spasi(teks):
    return re.sub(r"[\s-]", "", teks) if teks else teks


class CheckoutForm(FlaskForm):
    metode_pengiriman = RadioField("Metode Pengiriman", default=Pesanan.KURIR,
                                   choices=list(Pesanan.LABEL_PENGIRIMAN.items()),
                                   validators=[InputRequired(message="Pilih metode pengiriman.")])
    nama_penerima = StringField("Nama Penerima", filters=[_rapikan], validators=[
        DataRequired(message="Nama penerima wajib diisi."),
        Length(min=3, max=100, message="Nama penerima harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    telepon = StringField("Nomor HP", filters=[_hapus_spasi], validators=[
        DataRequired(message="Nomor HP wajib diisi."),
        Regexp(TELEPON_POLICY, message="Nomor HP tidak valid. Contoh: 081234567890."),
    ])
    # Alamat hanya wajib untuk pengiriman kurir (dicek di validate_* di bawah)
    alamat = TextAreaField("Alamat Lengkap", filters=[_rapikan], validators=[
        Length(max=255, message="Alamat maksimal 255 karakter.")])
    kota = StringField("Kota / Kabupaten", filters=[_rapikan], validators=[
        Length(max=60, message="Nama kota maksimal 60 karakter.")])
    kode_pos = StringField("Kode Pos", filters=[_rapikan])
    simpan_alamat = BooleanField("Simpan alamat ini ke Alamat Saya")
    catatan = StringField("Catatan untuk Penjual (opsional)", filters=[_rapikan], validators=[
        Optional(), Length(max=200, message="Catatan maksimal 200 karakter.")])
    kode_kupon = StringField("Kode Voucher (opsional)", filters=[_rapikan], validators=[
        Optional(), Length(max=30, message="Kode voucher maksimal 30 karakter.")])
    metode_pembayaran = RadioField("Metode Pembayaran", default=Pesanan.TRANSFER,
                                   choices=list(Pesanan.LABEL_PEMBAYARAN.items()),
                                   validators=[InputRequired(message="Pilih metode pembayaran.")])
    submit = SubmitField("Buat Pesanan")

    def _wajib_untuk_kurir(self, field, pesan):
        if self.metode_pengiriman.data == Pesanan.KURIR and not field.data:
            raise ValidationError(pesan)

    def validate_alamat(self, field):
        self._wajib_untuk_kurir(field, "Alamat wajib diisi untuk pengiriman kurir.")
        if field.data and len(field.data) < 10:
            raise ValidationError("Alamat terlalu singkat, tulis nama jalan, nomor, dan RT/RW.")

    def validate_kota(self, field):
        self._wajib_untuk_kurir(field, "Kota wajib diisi untuk pengiriman kurir.")

    def validate_kode_pos(self, field):
        self._wajib_untuk_kurir(field, "Kode pos wajib diisi untuk pengiriman kurir.")
        if field.data and not re.fullmatch(r"\d{5}", field.data):
            raise ValidationError("Kode pos harus 5 digit angka.")


class BuktiBayarForm(FlaskForm):
    bukti = FileField("Foto / Screenshot Bukti Transfer", validators=[
        FileRequired(message="Pilih file bukti transfer terlebih dahulu."),
        FileAllowed(["jpg", "jpeg", "png"], message="Bukti transfer harus berupa gambar JPG atau PNG."),
    ])
    submit = SubmitField("Kirim Bukti Bayar")


AKSI_ADMIN = ["terima", "tolak", "kirim", "siap_diambil", "selesai", "batal"]


class AksiPesananForm(FlaskForm):
    """Satu form untuk semua tombol aksi admin; tombol mengirim nilai `aksi`."""
    aksi = StringField(validators=[AnyOf(AKSI_ADMIN, message="Aksi tidak dikenal.")])
    alasan = StringField("Alasan", filters=[_rapikan], validators=[
        Optional(), Length(max=200, message="Alasan maksimal 200 karakter.")])
    nomor_resi = StringField("Nomor Resi", filters=[_rapikan], validators=[
        Optional(), Regexp(RESI_POLICY, message="Nomor resi 5-50 karakter (huruf, angka, tanda hubung).")])
