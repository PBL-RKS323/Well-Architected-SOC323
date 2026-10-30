import re
import secrets

from forms.auth_form import PASSWORD_POLICY


def buat_kata_sandi_sementara():
    """Kata sandi acak 14 karakter yang memenuhi kebijakan (huruf besar, kecil, angka, simbol).
    Dipakai saat admin membuat akun lewat CLI atau mereset kata sandi pengguna."""
    while True:
        password = secrets.token_urlsafe(9) + secrets.choice("!#$%*?") + str(secrets.randbelow(10))
        if re.match(PASSWORD_POLICY, password):
            return password
