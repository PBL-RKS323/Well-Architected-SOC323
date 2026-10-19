"""Format waktu untuk tampilan. Database menyimpan UTC, halaman menampilkan WIB."""
from datetime import timezone

from helpers.security_logger import WIB

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def ke_wib(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB)


def format_tanggal(dt, jam=True):
    """Contoh: 19 Okt 2026, 14.32 WIB"""
    dt = ke_wib(dt)
    if dt is None:
        return "-"
    teks = f"{dt.day} {BULAN[dt.month - 1]} {dt.year}"
    return f"{teks}, {dt:%H.%M} WIB" if jam else teks
