import logging

from flask import render_template, redirect, url_for, flash, request, g

from controllers.toko_controller import _escape_like
from forms.pesanan_form import AksiPesananForm
from helpers.security_logger import log_event
from middlewares.auth_middleware import admin_required
from models import db
from models.pesanan import Pesanan
from models.user import User

PER_HALAMAN = 15
TAB = {
    "semua": ("Semua", None),
    "verifikasi": ("Perlu Verifikasi", [Pesanan.MENUNGGU_VERIFIKASI]),
    "diproses": ("Perlu Dikirim", [Pesanan.DIPROSES]),
    "dikirim": ("Dikirim / Siap Diambil", [Pesanan.DIKIRIM, Pesanan.SIAP_DIAMBIL]),
    "belum_bayar": ("Belum Bayar", [Pesanan.MENUNGGU_PEMBAYARAN]),
    "selesai": ("Selesai", [Pesanan.SELESAI]),
    "dibatalkan": ("Dibatalkan", [Pesanan.DIBATALKAN]),
}

# aksi tombol -> (status tujuan, keterangan di timeline)
AKSI = {
    "terima": (Pesanan.DIPROSES, "Pembayaran diterima, pesanan diproses"),
    "tolak": (Pesanan.MENUNGGU_PEMBAYARAN, "Bukti bayar ditolak"),
    "kirim": (Pesanan.DIKIRIM, "Pesanan dikirim"),
    "siap_diambil": (Pesanan.SIAP_DIAMBIL, "Pesanan siap diambil di toko"),
    "selesai": (Pesanan.SELESAI, "Pesanan selesai"),
    "batal": (Pesanan.DIBATALKAN, "Dibatalkan oleh admin"),
}
EVENT_LOG = {"terima": "PAYMENT_VERIFIED", "tolak": "PAYMENT_REJECTED", "batal": "ORDER_CANCELLED"}


def jumlah_perlu_verifikasi():
    return Pesanan.query.filter_by(status=Pesanan.MENUNGGU_VERIFIKASI).count()


@admin_required
def index():
    Pesanan.batalkan_kedaluwarsa()
    tab = request.args.get("tab", "semua")
    if tab not in TAB:
        tab = "semua"
    q = request.args.get("q", "").strip()[:100]

    dasar = Pesanan.query.join(User, Pesanan.user_id == User.id)
    if q:
        pola = f"%{_escape_like(q)}%"
        dasar = dasar.filter(Pesanan.kode.ilike(pola, escape="\\") | User.nama_lengkap.ilike(pola, escape="\\")
                             | User.email.ilike(pola, escape="\\") | Pesanan.nama_penerima.ilike(pola, escape="\\"))

    jumlah_tab = {nama: (dasar.filter(Pesanan.status.in_(st)) if st else dasar).count()
                  for nama, (_, st) in TAB.items()}
    status = TAB[tab][1]
    query = dasar.filter(Pesanan.status.in_(status)) if status else dasar
    halaman = query.order_by(Pesanan.created_at.desc()).paginate(per_page=PER_HALAMAN, error_out=False)
    return render_template("admin/pesanan/index.html", halaman=halaman, tab=tab, tabs=TAB, q=q, jumlah_tab=jumlah_tab)


@admin_required
def detail(pesanan_id):
    pesanan = db.get_or_404(Pesanan, pesanan_id)
    return render_template("admin/pesanan/detail.html", pesanan=pesanan, form=AksiPesananForm())


@admin_required
def ubah_status(pesanan_id):
    pesanan = db.get_or_404(Pesanan, pesanan_id)
    form = AksiPesananForm()
    kembali = redirect(url_for("admin_pesanan_detail", pesanan_id=pesanan.id))

    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return kembali

    aksi = form.aksi.data
    status_baru, keterangan = AKSI[aksi]

    # Aturan tambahan di luar tabel transisi
    if aksi == "kirim" and pesanan.metode_pengiriman != Pesanan.KURIR:
        flash("Pesanan ini diambil di toko, gunakan tombol Siap Diambil.", "warning")
        return kembali
    if aksi == "siap_diambil" and pesanan.metode_pengiriman != Pesanan.AMBIL:
        flash("Pesanan ini dikirim kurir, gunakan tombol Kirim.", "warning")
        return kembali
    if aksi in ("tolak", "batal") and not form.alasan.data:
        flash("Tuliskan alasannya agar pelanggan tahu apa yang perlu dilakukan.", "warning")
        return kembali

    status_lama = pesanan.status
    if aksi == "tolak":
        keterangan = f"Bukti bayar ditolak: {form.alasan.data}"
    elif aksi == "batal":
        keterangan = f"Dibatalkan admin: {form.alasan.data}"
    elif aksi == "kirim" and form.nomor_resi.data:
        keterangan = f"Pesanan dikirim, resi {form.nomor_resi.data}"

    if not pesanan.ubah_status(status_baru, "admin", keterangan):
        log_event("ORDER_INVALID_TRANSITION", logging.WARNING, user_id=g.user.id, kode=pesanan.kode,
                  status_from=status_lama, action=aksi)
        flash(f"Aksi tidak bisa dilakukan untuk pesanan berstatus {pesanan.label_status}.", "danger")
        return kembali

    if aksi == "tolak":
        pesanan.alasan_tolak = form.alasan.data
        pesanan.batas_bayar = Pesanan.hitung_batas_bayar()  # beri waktu untuk mengunggah ulang
    elif aksi == "batal":
        pesanan.alasan_tolak = form.alasan.data
    elif aksi == "kirim":
        pesanan.nomor_resi = form.nomor_resi.data or None
    db.session.commit()

    log_event(EVENT_LOG.get(aksi, "ORDER_STATUS_CHANGE"), logging.WARNING if aksi in ("tolak", "batal") else logging.INFO,
              user_id=g.user.id, kode=pesanan.kode, status_from=status_lama, status_to=status_baru)
    flash(f"Pesanan {pesanan.kode} sekarang berstatus {pesanan.label_status}.", "success")
    return kembali
