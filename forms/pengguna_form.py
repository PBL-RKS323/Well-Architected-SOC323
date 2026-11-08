from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, AnyOf, Optional, ValidationError

from forms.auth_form import (PASSWORD_POLICY, PASSWORD_POLICY_MESSAGE, NAMA_POLICY, rapikan_email, KLIEN_EMAIL,
                             KLIEN_NAMA, KLIEN_PASSWORD_BARU, KLIEN_MAKS_2MB, klien_sama_dengan)
from models.user import User

PILIHAN_PERAN = list(User.LABEL_ROLE.items())


class TambahPenggunaForm(FlaskForm):
    """Admin membuat akun (biasanya staf/admin). Pelanggan mendaftar sendiri lewat /register."""
    nama_lengkap = StringField("Nama Lengkap", render_kw=KLIEN_NAMA, validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    email = StringField("Email", render_kw=KLIEN_EMAIL, filters=[rapikan_email], validators=[
        DataRequired(message="Email wajib diisi."), Email(message="Format email tidak valid."), Length(max=100),
    ])
    peran = SelectField("Peran", choices=PILIHAN_PERAN, default=User.ROLE_STAF)
    password = PasswordField("Kata Sandi Awal", render_kw=KLIEN_PASSWORD_BARU, validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    submit = SubmitField("Buat Akun")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email sudah terdaftar!")


class EditPenggunaForm(FlaskForm):
    """Admin membetulkan nama/email akun orang lain (mis. salah ketik saat dibuat)."""
    nama_lengkap = StringField("Nama Lengkap", render_kw=KLIEN_NAMA, validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    email = StringField("Email", render_kw=KLIEN_EMAIL, filters=[rapikan_email], validators=[
        DataRequired(message="Email wajib diisi."), Email(message="Format email tidak valid."), Length(max=100),
    ])
    submit = SubmitField("Simpan Data")

    def __init__(self, *args, user_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, field):
        if User.query.filter(User.email == field.data.strip().lower(), User.id != self.user_id).first():
            raise ValidationError("Email sudah dipakai akun lain!")


AKSI_PENGGUNA = ["ubah_peran", "nonaktifkan", "aktifkan", "buka_kunci", "reset_password"]


class AksiPenggunaForm(FlaskForm):
    """Satu form untuk semua tombol aksi di halaman detail pengguna; tombol mengirim nilai `aksi`."""
    aksi = StringField(validators=[AnyOf(AKSI_PENGGUNA, message="Aksi tidak dikenal.")])
    peran = SelectField("Peran", choices=PILIHAN_PERAN, validators=[Optional()])
