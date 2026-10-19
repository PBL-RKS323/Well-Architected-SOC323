from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from models.user import User

# Semua simbol diterima (mis. # - _ .), tidak dibatasi ke daftar tertentu
PASSWORD_POLICY = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s]).{8,128}$"
PASSWORD_POLICY_MESSAGE = ("Kata sandi minimal 8 karakter dan harus mengandung huruf besar, huruf kecil, "
                           "angka, dan simbol (contoh: # @ ! _ -).")
NAMA_POLICY = r"^[A-Za-zÀ-ÖØ-öø-ÿ' .-]+$"


class RegisterForm(FlaskForm):
    nama_lengkap = StringField("Nama Lengkap", validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    email = StringField("Email", validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    password = PasswordField("Kata Sandi", validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    confirm_password = PasswordField("Konfirmasi Kata Sandi", validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo("password", message="Konfirmasi kata sandi tidak cocok."),
    ])
    setuju = BooleanField("Saya setuju dengan Syarat & Ketentuan serta Kebijakan Privasi", validators=[
        DataRequired(message="Anda harus menyetujui syarat & ketentuan."),
    ])
    submit = SubmitField("Buat Akun")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email sudah terdaftar!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    password = PasswordField("Kata Sandi", validators=[DataRequired(message="Kata sandi wajib diisi.")])
    ingat_saya = BooleanField("Ingat saya")
    submit = SubmitField("Masuk")
