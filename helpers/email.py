import logging
import smtplib

from flask import current_app, render_template
from flask_mail import Mail, Message

from helpers.security_logger import log_event

mail = Mail()


def email_aktif():
    """Fitur email/OTP hanya aktif jika akun pengirim sudah diisi di .env."""
    cfg = current_app.config
    return bool(cfg.get("MAIL_USERNAME") and cfg.get("MAIL_PASSWORD"))


def kirim_kode_otp(user, kode, tujuan_label):
    """Mengirim kode OTP ke email user. Mengembalikan True jika terkirim.
    Kode hanya ada di isi email, tidak di subjek (agar tidak terlihat di notifikasi layar kunci HP)."""
    data = {"user": user, "kode": kode, "judul": tujuan_label,
            "menit": current_app.config["OTP_BERLAKU_MENIT"], "app_name": current_app.config["APP_NAME"]}
    msg = Message(f"{tujuan_label} - {current_app.config['APP_NAME']}", recipients=[user.email],
                  body=render_template("email/kode_otp.txt", **data),
                  html=render_template("email/kode_otp.html", **data))
    try:
        mail.send(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:
        # Detail teknis hanya di log server, pengguna mendapat pesan umum
        log_event("EMAIL_FAILED", logging.ERROR, user_id=user.id, error=type(e).__name__)
        return False
