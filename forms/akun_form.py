from flask import g
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from forms.auth_form import PASSWORD_POLICY, PASSWORD_POLICY_MESSAGE, NAMA_POLICY
from models.user import User


class UbahNamaForm(FlaskForm):
    nama_lengkap = StringField("Nama Lengkap", validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    submit = SubmitField("Simpan Nama")


class UbahEmailForm(FlaskForm):
    email_baru = StringField("Email Baru", validators=[
        DataRequired(message="Email baru wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    password_sekarang = PasswordField("Kata Sandi Saat Ini", validators=[
        DataRequired(message="Masukkan kata sandi saat ini untuk konfirmasi."),
    ])
    submit = SubmitField("Simpan Email")

    def validate_email_baru(self, field):
        email = field.data.strip().lower()
        if email == g.user.email:
            raise ValidationError("Email baru sama dengan email saat ini.")
        if User.query.filter(User.email == email, User.id != g.user.id).first():
            raise ValidationError("Email sudah dipakai akun lain!")


class UbahPasswordForm(FlaskForm):
    password_sekarang = PasswordField("Kata Sandi Saat Ini", validators=[
        DataRequired(message="Kata sandi saat ini wajib diisi."),
    ])
    password_baru = PasswordField("Kata Sandi Baru", validators=[
        DataRequired(message="Kata sandi baru wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    konfirmasi_password = PasswordField("Konfirmasi Kata Sandi Baru", validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo("password_baru", message="Konfirmasi kata sandi tidak cocok."),
    ])
    submit = SubmitField("Simpan Kata Sandi")
