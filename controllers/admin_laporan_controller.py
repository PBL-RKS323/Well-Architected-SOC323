import csv
import io
import logging
from datetime import date, datetime, time, timedelta, timezone

from flask import render_template, request, Response, g
from sqlalchemy.orm import selectinload

from helpers.security_logger import WIB, log_event
from helpers.waktu import ke_wib, BULAN
from middlewares.auth_middleware import izin_required
from models import db
from models.pesanan import Pesanan, PesananItem

PER_HALAMAN = 20
MAKS_RENTANG_HARI = 366
MAKS_BARIS_CSV = 20000
PRESET = {
    "7hari": "7 hari terakhir",
    "30hari": "30 hari terakhir",
    "bulan_ini": "Bulan ini",
    "bulan_lalu": "Bulan lalu",
    "tahun_ini": "Tahun ini",
}


def _hari_ini():
    return datetime.now(WIB).date()


def _rentang_preset(kode, hari_ini):
    if kode == "7hari":
        return hari_ini - timedelta(days=6), hari_ini
    if kode == "30hari":
        return hari_ini - timedelta(days=29), hari_ini
    if kode == "bulan_lalu":
        akhir = hari_ini.replace(day=1) - timedelta(days=1)
        return akhir.replace(day=1), akhir
    if kode == "tahun_ini":
        return hari_ini.replace(month=1, day=1), hari_ini
    return hari_ini.replace(day=1), hari_ini  # bulan_ini


def _tanggal(teks):
    try:
        return date.fromisoformat((teks or "").strip()[:10])
    except ValueError:
        return None


def baca_rentang(args):
    """Rentang tanggal laporan (WIB) dari query string: dari & sampai, atau preset.
    Input tidak valid kembali ke "bulan ini"; rentang dibatasi 1 tahun agar query tetap ringan."""
    hari_ini = _hari_ini()
    dari, sampai = _tanggal(args.get("dari")), _tanggal(args.get("sampai"))
    if dari and sampai:
        if dari > sampai:
            dari, sampai = sampai, dari
        if (sampai - dari).days >= MAKS_RENTANG_HARI:
            dari = sampai - timedelta(days=MAKS_RENTANG_HARI - 1)
        return dari, sampai, None
    preset = args.get("preset")
    preset = preset if preset in PRESET else "bulan_ini"
    return (*_rentang_preset(preset, hari_ini), preset)


def _awal_hari_utc(tgl):
    """Pukul 00.00 WIB pada tanggal itu, dalam UTC (kolom created_at disimpan UTC)."""
    return datetime.combine(tgl, time.min, tzinfo=WIB).astimezone(timezone.utc).replace(tzinfo=None)


def _pesanan_rentang(dari, sampai):
    return Pesanan.query.filter(Pesanan.created_at >= _awal_hari_utc(dari),
                                Pesanan.created_at < _awal_hari_utc(sampai + timedelta(days=1)))


def _tren(baris_lunas, dari, sampai):
    """Pendapatan per hari (atau per bulan jika rentang > 62 hari) untuk grafik batang.
    Dikelompokkan di Python agar sama di SQLite & PostgreSQL (fungsi tanggal SQL berbeda-beda)."""
    per_bulan = (sampai - dari).days > 62
    kunci = (lambda d: (d.year, d.month)) if per_bulan else (lambda d: d)
    nilai = {}
    for created_at, total in baris_lunas:
        k = kunci(ke_wib(created_at).date())
        nilai[k] = nilai.get(k, 0) + int(total)

    titik, d = [], dari
    while d <= sampai:
        k = kunci(d)
        if not titik or titik[-1]["kunci"] != k:
            label = f"{BULAN[d.month - 1]} {d.year % 100:02d}" if per_bulan else f"{d.day} {BULAN[d.month - 1]}"
            titik.append({"kunci": k, "label": label, "nilai": nilai.get(k, 0)})
        d += timedelta(days=1)
    tertinggi = max((t["nilai"] for t in titik), default=0)
    for t in titik:
        t["persen"] = round(t["nilai"] / tertinggi * 100) if tertinggi else 0
    return {"titik": titik, "per_bulan": per_bulan, "tertinggi": tertinggi}


def hitung_laporan(dari, sampai):
    semua = _pesanan_rentang(dari, sampai)
    lunas = semua.filter(Pesanan.status.in_(Pesanan.STATUS_LUNAS))
    jumlah = dict(db.session.query(Pesanan.status, db.func.count(Pesanan.id))
                  .filter(Pesanan.id.in_(semua.with_entities(Pesanan.id)))
                  .group_by(Pesanan.status).all())
    baris_lunas = lunas.with_entities(Pesanan.created_at, Pesanan.total).all()
    pendapatan = sum(int(t) for _, t in baris_lunas)
    jumlah_lunas = len(baris_lunas)

    id_lunas = lunas.with_entities(Pesanan.id)
    nilai_item = db.func.sum(PesananItem.harga * PesananItem.jumlah)
    terlaris = (db.session.query(PesananItem.nama_produk, PesananItem.merek,
                                 db.func.sum(PesananItem.jumlah).label("terjual"), nilai_item.label("pendapatan"))
                .filter(PesananItem.pesanan_id.in_(id_lunas))
                .group_by(PesananItem.nama_produk, PesananItem.merek)
                .order_by(nilai_item.desc()).limit(5).all())
    per_merek = (db.session.query(PesananItem.merek, nilai_item.label("pendapatan"))
                 .filter(PesananItem.pesanan_id.in_(id_lunas))
                 .group_by(PesananItem.merek).order_by(nilai_item.desc()).all())
    per_pengiriman = dict(lunas.with_entities(Pesanan.metode_pengiriman, db.func.count(Pesanan.id))
                          .group_by(Pesanan.metode_pengiriman).all())
    barang_terjual = (db.session.query(db.func.coalesce(db.func.sum(PesananItem.jumlah), 0))
                      .filter(PesananItem.pesanan_id.in_(id_lunas)).scalar())
    ongkir = (lunas.with_entities(db.func.coalesce(db.func.sum(Pesanan.ongkir), 0)).scalar())

    total_pesanan = sum(jumlah.values())
    return {
        "pendapatan": pendapatan,
        "penjualan_produk": pendapatan - int(ongkir),
        "ongkir": int(ongkir),
        "total_pesanan": total_pesanan,
        "pesanan_lunas": jumlah_lunas,
        "rata_rata": pendapatan // jumlah_lunas if jumlah_lunas else 0,
        "barang_terjual": int(barang_terjual),
        "dibatalkan": jumlah.get(Pesanan.DIBATALKAN, 0),
        "belum_bayar": jumlah.get(Pesanan.MENUNGGU_PEMBAYARAN, 0) + jumlah.get(Pesanan.MENUNGGU_VERIFIKASI, 0),
        "konversi": round(jumlah_lunas / total_pesanan * 100) if total_pesanan else 0,
        "per_status": [(s, Pesanan.LABEL_STATUS[s], jumlah.get(s, 0)) for s in Pesanan.LABEL_STATUS],
        "per_pengiriman": [(Pesanan.LABEL_PENGIRIMAN[m], per_pengiriman.get(m, 0)) for m in Pesanan.LABEL_PENGIRIMAN],
        "per_merek": per_merek,
        "terlaris": terlaris,
        "tren": _tren(baris_lunas, dari, sampai),
    }


def _status_filter(args):
    status = args.get("status", "")
    return status if status in Pesanan.LABEL_STATUS else ""


@izin_required("lihat_laporan")
def index():
    Pesanan.batalkan_kedaluwarsa()
    dari, sampai, preset = baca_rentang(request.args)
    status = _status_filter(request.args)
    transaksi = _pesanan_rentang(dari, sampai)
    if status:
        transaksi = transaksi.filter(Pesanan.status == status)
    halaman = transaksi.order_by(Pesanan.created_at.desc()).paginate(per_page=PER_HALAMAN, error_out=False)
    args_dasar = {"dari": dari.isoformat(), "sampai": sampai.isoformat()}
    return render_template("admin/laporan.html", lap=hitung_laporan(dari, sampai), halaman=halaman,
                           dari=dari, sampai=sampai, preset=preset, presets=PRESET, status=status,
                           status_label=Pesanan.LABEL_STATUS.get(status), args_dasar=args_dasar,
                           hari_ini=_hari_ini())


# Sel yang diawali karakter ini dianggap rumus oleh Excel/Sheets (CSV injection), jadi diberi awalan '
_AWALAN_RUMUS = ("=", "+", "-", "@", "\t", "\r")


def _sel(nilai):
    if isinstance(nilai, str) and nilai.startswith(_AWALAN_RUMUS):
        return "'" + nilai
    return nilai


@izin_required("lihat_laporan")
def ekspor_csv():
    dari, sampai, _ = baca_rentang(request.args)
    status = _status_filter(request.args)
    query = _pesanan_rentang(dari, sampai)
    if status:
        query = query.filter(Pesanan.status == status)
    daftar = (query.options(selectinload(Pesanan.user), selectinload(Pesanan.items))
              .order_by(Pesanan.created_at.asc()).limit(MAKS_BARIS_CSV).all())

    buf = io.StringIO()
    buf.write("﻿")  # BOM agar Excel membaca UTF-8 dengan benar
    tulis = csv.writer(buf)
    tulis.writerow(["Kode Pesanan", "Tanggal (WIB)", "Pelanggan", "Email", "Status", "Pengiriman", "Kota",
                    "Jumlah Barang", "Subtotal", "Ongkir", "Total", "Nomor Resi"])
    for p in daftar:
        tulis.writerow([_sel(v) for v in [
            p.kode, f"{ke_wib(p.created_at):%Y-%m-%d %H:%M}", p.user.display_name, p.user.email, p.label_status,
            Pesanan.LABEL_PENGIRIMAN.get(p.metode_pengiriman, p.metode_pengiriman), p.kota or "",
            p.jumlah_barang, int(p.subtotal), int(p.ongkir), int(p.total), p.nomor_resi or "",
        ]])

    # Ekspor data transaksi dicatat: berguna untuk mendeteksi pengambilan data massal oleh akun yang dibobol
    log_event("REPORT_EXPORTED", logging.WARNING, user_id=g.user.id, username=g.user.username,
              date_from=dari.isoformat(), date_to=sampai.isoformat(), status=status or "semua", rows=len(daftar))
    nama = f"laporan-transaksi-{dari:%Y%m%d}-{sampai:%Y%m%d}.csv"
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{nama}"',
                             "Cache-Control": "no-store"})
