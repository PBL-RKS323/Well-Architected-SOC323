from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, AnyOf, Optional, ValidationError

from forms.auth_form import PASSWORD_POLICY, PASSWORD_POLICY_MESSAGE, NAMA_POLICY
from models.user import User

PILIHAN_PERAN = list(User.LABEL_ROLE.items())


class TambahPenggunaForm(FlaskForm):
    """Admin membuat akun (biasanya staf/admin). Pelanggan mendaftar sendiri lewat /register."""
    nama_lengkap = StringField("Nama Lengkap", validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    email = StringField("Email", validators=[
        DataRequired(message="Email wajib diisi."), Email(message="Format email tidak valid."), Length(max=100),
    ])
    peran = SelectField("Peran", choices=PILIHAN_PERAN, default=User.ROLE_STAF)
    password = PasswordField("Kata Sandi Awal", validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    submit = SubmitField("Buat Akun")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email sudah terdaftar!")


AKSI_PENGGUNA = ["ubah_peran", "nonaktifkan", "aktifkan", "buka_kunci"]


class AksiPenggunaForm(FlaskForm):
    """Satu form untuk semua tombol aksi di halaman detail pengguna; tombol mengirim nilai `aksi`."""
    aksi = StringField(validators=[AnyOf(AKSI_PENGGUNA, message="Aksi tidak dikenal.")])
    peran = SelectField("Peran", choices=PILIHAN_PERAN, validators=[Optional()])
