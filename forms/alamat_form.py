from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

from forms.auth_form import NAMA_POLICY
from forms.auth_form import KLIEN_NAMA
from forms.pesanan_form import TELEPON_POLICY, KLIEN_TELEPON, KLIEN_KODE_POS, _rapikan, _hapus_spasi


class AlamatForm(FlaskForm):
    label = StringField("Label Alamat", filters=[_rapikan], validators=[
        DataRequired(message="Label wajib diisi, contoh: Rumah, Kos, Kantor."),
        Length(max=30, message="Label maksimal 30 karakter."),
    ])
    nama_penerima = StringField("Nama Penerima", render_kw=KLIEN_NAMA, filters=[_rapikan], validators=[
        DataRequired(message="Nama penerima wajib diisi."),
        Length(min=3, max=100, message="Nama penerima harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    telepon = StringField("Nomor HP", render_kw=KLIEN_TELEPON, filters=[_hapus_spasi], validators=[
        DataRequired(message="Nomor HP wajib diisi."),
        Regexp(TELEPON_POLICY, message="Nomor HP tidak valid. Contoh: 081234567890."),
    ])
    alamat = TextAreaField("Alamat Lengkap", filters=[_rapikan], validators=[
        DataRequired(message="Alamat wajib diisi."),
        Length(min=10, max=255, message="Alamat 10-255 karakter (nama jalan, nomor, RT/RW)."),
    ])
    kota = StringField("Kota / Kabupaten", filters=[_rapikan], validators=[
        DataRequired(message="Kota wajib diisi."), Length(max=60, message="Nama kota maksimal 60 karakter."),
    ])
    kode_pos = StringField("Kode Pos", render_kw=KLIEN_KODE_POS, filters=[_rapikan], validators=[
        DataRequired(message="Kode pos wajib diisi."), Regexp(r"^\d{5}$", message="Kode pos harus 5 digit angka."),
    ])
    utama = BooleanField("Jadikan alamat utama")
    submit = SubmitField("Simpan Alamat")
