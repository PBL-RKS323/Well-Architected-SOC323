from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from models.user import User

PASSWORD_POLICY = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$"
PASSWORD_POLICY_MESSAGE = ("Kata sandi harus mengandung minimal 1 huruf besar, 1 huruf kecil, "
                           "1 angka, dan 1 karakter spesial (@$!%*?&).")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(message="Username wajib diisi."),
        Length(min=4, max=50, message="Username harus 4-50 karakter."),
        Regexp(r"^[A-Za-z0-9_.]+$", message="Username hanya boleh huruf, angka, titik, dan garis bawah."),
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
    submit = SubmitField("Daftar")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username sudah digunakan!")

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
    submit = SubmitField("Masuk")
