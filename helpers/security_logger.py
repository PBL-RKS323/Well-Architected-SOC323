"""Log audit keamanan dalam format satu baris yang mudah di-parsing Wazuh.

Contoh baris:
2026-10-19T14:30:00+07:00 | WARNING | FAILED_LOGIN | src_ip=192.168.66.5 | email=x@y.com | reason=invalid_credentials
"""
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from flask import request, has_request_context

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
