from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from models.user import User

# Semua simbol diterima (mis. # - _ .), tidak dibatasi ke daftar tertentu
PASSWORD_POLICY = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s]).{8,128}$"
PASSWORD_POLICY_MESSAGE = ("Kata sandi minimal 8 karakter dan harus mengandung huruf besar, huruf kecil, "
                           "angka, dan simbol (contoh: # @ ! _ -).")
NAMA_POLICY = r"^[A-Za-zÀ-ÖØ-öø-ÿ' .-]+$"
NAMA_POLICY_MESSAGE = "Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."

# --- Atribut HTML untuk validasi sisi klien (dibaca static/js/app.js) ---
# Aturan yang sama tetap dicek di server oleh validator WTForms (Regexp, EqualTo, Email).
KLIEN_EMAIL = {"type": "email", "autocomplete": "email"}
KLIEN_NAMA = {"data-pola": NAMA_POLICY, "data-pola-pesan": NAMA_POLICY_MESSAGE}
KLIEN_PASSWORD_BARU = {"data-pola": PASSWORD_POLICY, "data-pola-pesan": PASSWORD_POLICY_MESSAGE,
                       "autocomplete": "new-password"}
KLIEN_MAKS_2MB = {"accept": ".jpg,.jpeg,.png,image/jpeg,image/png", "data-maks-byte": str(2 * 1024 * 1024)}


def klien_sama_dengan(nama_field):
    return {"data-sama-dengan": nama_field, "data-sama-pesan": "Konfirmasi kata sandi tidak cocok.",
            "autocomplete": "new-password"}


def rapikan_email(teks):
    """Spasi di awal/akhir dibuang & huruf dikecilkan, agar " Intan@Gmail.com " tetap diterima
    (validator Email WTForms menolak jika ada spasi)."""
    return teks.strip().lower() if teks else teks


class RegisterForm(FlaskForm):
    nama_lengkap = StringField("Nama Lengkap", render_kw=KLIEN_NAMA, validators=[
        DataRequired(message="Nama lengkap wajib diisi."),
        Length(min=3, max=100, message="Nama lengkap harus 3-100 karakter."),
        Regexp(NAMA_POLICY, message="Nama hanya boleh berisi huruf, spasi, titik, tanda hubung, dan apostrof."),
    ])
    email = StringField("Email", render_kw=KLIEN_EMAIL, filters=[rapikan_email], validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    password = PasswordField("Kata Sandi", render_kw=KLIEN_PASSWORD_BARU, validators=[
        DataRequired(message="Kata sandi wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    confirm_password = PasswordField("Konfirmasi Kata Sandi", render_kw=klien_sama_dengan("password"), validators=[
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
    email = StringField("Email", render_kw=KLIEN_EMAIL, filters=[rapikan_email], validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    password = PasswordField("Kata Sandi", validators=[DataRequired(message="Kata sandi wajib diisi.")])
    ingat_saya = BooleanField("Ingat saya")
    submit = SubmitField("Masuk")


def _rapikan_kode(teks):
    """Spasi/tanda hubung dibuang agar kode yang disalin dari email ("123 456") tetap diterima."""
    return "".join(c for c in teks if c.isdigit()) if teks else teks


KODE_OTP_VALIDATORS = [
    DataRequired(message="Masukkan kode 6 digit dari email."),
    Regexp(r"^\d{6}$", message="Kode terdiri dari 6 angka."),
]


class LupaPasswordForm(FlaskForm):
    email = StringField("Email", render_kw=KLIEN_EMAIL, filters=[rapikan_email], validators=[
        DataRequired(message="Email wajib diisi."),
        Email(message="Format email tidak valid."),
        Length(max=100),
    ])
    submit = SubmitField("Kirim Kode")


class ResetPasswordForm(FlaskForm):
    kode = StringField("Kode dari Email", filters=[_rapikan_kode], validators=KODE_OTP_VALIDATORS)
    password_baru = PasswordField("Kata Sandi Baru", render_kw=KLIEN_PASSWORD_BARU, validators=[
        DataRequired(message="Kata sandi baru wajib diisi."),
        Length(min=8, max=128, message="Kata sandi minimal 8 karakter."),
        Regexp(PASSWORD_POLICY, message=PASSWORD_POLICY_MESSAGE),
    ])
    konfirmasi_password = PasswordField("Konfirmasi Kata Sandi Baru", render_kw=klien_sama_dengan("password_baru"), validators=[
        DataRequired(message="Konfirmasi kata sandi wajib diisi."),
        EqualTo("password_baru", message="Konfirmasi kata sandi tidak cocok."),
    ])
    submit = SubmitField("Simpan Kata Sandi Baru")


class KodeOtpForm(FlaskForm):
    kode = StringField("Kode dari Email", filters=[_rapikan_kode], validators=KODE_OTP_VALIDATORS)
    submit = SubmitField("Verifikasi")
