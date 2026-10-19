from flask import session, url_for


def safe_next_url(target):
    """Hanya izinkan redirect ke path internal (mencegah open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return None


def mulai_sesi(user, ingat):
    """Sesi baru setelah login / ganti kata sandi. Sesi lama dibuang (anti session fixation).

    `ingat` True: sesi bertahan 7 hari ("Ingat saya"). False: berakhir saat browser ditutup.
    """
    session.clear()
    session["user_id"] = user.id
    session["sesi_token"] = user.sesi_token
    session.permanent = ingat


def halaman_awal(user, next_url=None):
    """Tujuan setelah login: halaman yang diminta sebelumnya, atau panel/beranda sesuai peran."""
    return next_url or url_for("admin_dashboard" if user.is_staf_toko() else "beranda")


def samarkan_email(email):
    """budi.santoso@gmail.com -> bu**********@gmail.com (ditampilkan saat kode OTP dikirim)."""
    nama, _, domain = email.partition("@")
    return f"{nama[:2]}{'*' * max(len(nama) - 2, 1)}@{domain}"
