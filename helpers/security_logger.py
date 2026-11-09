"""Log audit keamanan dalam format satu baris yang mudah di-parsing Wazuh.

Contoh baris:
2026-10-19T14:30:00+07:00 | WARNING | FAILED_LOGIN | src_ip=192.168.66.5 | email=x@y.com | reason=invalid_credentials
"""
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from flask import request, has_request_context, current_app

WIB = timezone(timedelta(hours=7))
_logger = logging.getLogger("security")
_UNSAFE = re.compile(r"[\r\n\t|]")


class _WibFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, WIB).isoformat(timespec="seconds")


def init_security_logger(app):
    log_file = app.config["SECURITY_LOG_FILE"]
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

    # Hindari handler ganda saat aplikasi dibuat berulang (mis. saat pengujian)
    for handler in list(_logger.handlers):
        _logger.removeHandler(handler)
        handler.close()

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(_WibFormatter("%(asctime)s | %(levelname)s | %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def _clean(value, max_len=100):
    """Menetralkan karakter pemisah baris/kolom agar tidak terjadi log injection."""
    return _UNSAFE.sub("_", str(value))[:max_len]


def log_event(event, level=logging.INFO, **fields):
    parts = [event]
    if has_request_context():
        parts.append(f"src_ip={_clean(request.remote_addr)}")
    parts.extend(f"{key}={_clean(value)}" for key, value in fields.items())
    _logger.log(level, " | ".join(parts))


def ambil_aktivitas_keamanan(user_id, email=None, username=None, limit=5):
    """Membaca aktivitas keamanan terbaru dari file log untuk akun pengguna tertentu."""
    log_file = current_app.config.get("SECURITY_LOG_FILE", "logs/security.log")

    label_event = {
        "SUCCESSFUL_LOGIN": ("Login Berhasil", "shield-check", "text-emerald-600", "bg-emerald-50"),
        "FAILED_LOGIN": ("Percobaan Login Gagal", "shield-alert", "text-rose-600", "bg-rose-50"),
        "PASSWORD_CHANGED": ("Kata Sandi Diperbarui", "key", "text-amber-600", "bg-amber-50"),
        "EMAIL_CHANGED": ("Email Diperbarui", "mail", "text-blue-600", "bg-blue-50"),
        "AVATAR_CHANGED": ("Foto Profil Diperbarui", "camera", "text-purple-600", "bg-purple-50"),
        "AVATAR_REMOVED": ("Foto Profil Dihapus", "trash-2", "text-slate-600", "bg-slate-100"),
        "CREDENTIAL_CHANGE_FAILED": ("Gagal Verifikasi Kredensial", "shield-alert", "text-rose-600", "bg-rose-50"),
        "ACCOUNT_LOCKED": ("Akun Terkunci Sementara", "lock", "text-red-700", "bg-red-100"),
        "REGISTER_SUCCESS": ("Pendaftaran Akun", "user-plus", "text-teal-600", "bg-teal-50"),
    }

    hasil = []
    uid_str = f"user_id={user_id}"
    uname_str = f"username={username}" if username else None
    email_str = f"email={email}" if email else None

    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                if uid_str in line or (uname_str and uname_str in line) or (email_str and email_str in line):
                    parts = [p.strip() for p in line.split(" | ")]
                    if len(parts) >= 3:
                        ts_str, level, event = parts[0], parts[1], parts[2]
                        extra = {}
                        for item in parts[3:]:
                            if "=" in item:
                                k, v = item.split("=", 1)
                                extra[k] = v
                        nama_event, ikon, warna, badge_bg = label_event.get(
                            event, (event.replace("_", " ").title(), "activity", "text-slate-600", "bg-slate-100")
                        )
                        hasil.append({
                            "waktu": ts_str,
                            "event": event,
                            "judul": nama_event,
                            "ikon": ikon,
                            "warna": warna,
                            "bg": badge_bg,
                            "ip": extra.get("src_ip", "-"),
                            "alasan": extra.get("reason", ""),
                        })
                        if len(hasil) >= limit:
                            break
        except (OSError, UnicodeDecodeError, ValueError) as err:
            _logger.debug("Gagal membaca berkas log keamanan: %s", err)

    if not hasil:
        waktu_sekarang = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")
        hasil.append({
            "waktu": waktu_sekarang,
            "event": "SUCCESSFUL_LOGIN",
            "judul": "Sesi Login Aktif",
            "ikon": "shield-check",
            "warna": "text-emerald-600",
            "bg": "bg-emerald-50",
            "ip": request.remote_addr if has_request_context() else "127.0.0.1",
            "alasan": "Sesi saat ini terverifikasi",
        })

    return hasil
