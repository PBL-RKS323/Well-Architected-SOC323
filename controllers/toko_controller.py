from flask import render_template, request
from sqlalchemy import case, or_, select

from models import db
from models.keranjang import KeranjangItem
from models.produk import Produk

PER_HALAMAN = 12
URUTAN = {
    "terbaru": ("Terbaru", Produk.created_at.desc()),
    "termurah": ("Harga terendah", Produk.harga.asc()),
    "termahal": ("Harga tertinggi", Produk.harga.desc()),
    "nama": ("Nama A-Z", Produk.nama_produk.asc()),
}


def _angka(nilai):
    """Mengubah input harga dari URL menjadi angka bulat, atau None jika tidak valid."""
    nilai = (nilai or "").replace(".", "").strip()
    if nilai.isdigit() and len(nilai) <= 10:
        return int(nilai)
    return None


def _escape_like(teks):
    """Karakter % dan _ dari pengguna diperlakukan sebagai teks biasa, bukan wildcard."""
    return teks.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def beranda():
    """Halaman utama: produk unggulan, kategori, dan produk per ekosistem brand"""
    diskon = case((Produk.harga_normal > Produk.harga, (Produk.harga_normal - Produk.harga) / Produk.harga_normal),
                  else_=0)
    unggulan = (Produk.query.filter(Produk.stok > 0)
                .order_by(diskon.desc(), Produk.created_at.desc()).first())

    ekosistem = []
    for merek in Produk.MEREK:
        items = (Produk.query.filter_by(merek=merek)
                 .order_by(Produk.created_at.desc()).limit(8).all())
        if items:
            ekosistem.append((merek, items))

    return render_template("toko/beranda.html", unggulan=unggulan, ekosistem=ekosistem,
                           kategori_list=Produk.KATEGORI)


def jelajah():
    """Semua produk dengan pencarian, filter, urutan, dan halaman"""
    q = request.args.get("q", "").strip()[:100]
    kategori = request.args.get("kategori", "")
    kategori = kategori if kategori in Produk.KATEGORI else ""
    merek = request.args.get("merek", "")
    merek = merek if merek in Produk.MEREK else ""
    harga_min = _angka(request.args.get("min"))
    harga_max = _angka(request.args.get("max"))
    urut = request.args.get("urut", "terbaru")
    urut = urut if urut in URUTAN else "terbaru"

    stmt = select(Produk)
    if q:
        pola = f"%{_escape_like(q)}%"
        stmt = stmt.where(or_(Produk.nama_produk.ilike(pola, escape="\\"),
                              Produk.merek.ilike(pola, escape="\\"),
                              Produk.kategori.ilike(pola, escape="\\"),
                              Produk.deskripsi.ilike(pola, escape="\\")))
    if kategori:
        stmt = stmt.where(Produk.kategori == kategori)
    if merek:
        stmt = stmt.where(Produk.merek == merek)
    if harga_min is not None:
        stmt = stmt.where(Produk.harga >= harga_min)
    if harga_max is not None:
        stmt = stmt.where(Produk.harga <= harga_max)
    stmt = stmt.order_by(URUTAN[urut][1], Produk.id.desc())

    halaman = db.paginate(stmt, page=request.args.get("page", 1, type=int), per_page=PER_HALAMAN,
                          error_out=False)

    filter_aktif = {"q": q, "kategori": kategori, "merek": merek, "min": harga_min, "max": harga_max}
    args_dasar = {k: v for k, v in filter_aktif.items() if v not in ("", None)}
    if urut != "terbaru":
        args_dasar["urut"] = urut
    jumlah_filter = sum(1 for k in ("kategori", "merek", "min", "max") if k in args_dasar)

    return render_template(
        "toko/jelajah.html", halaman=halaman, f=filter_aktif, urut=urut, urutan=URUTAN,
        args_dasar=args_dasar, jumlah_filter=jumlah_filter,
        kategori_list=Produk.KATEGORI, merek_list=Produk.MEREK,
    )


def detail(produk_id):
    produk = db.get_or_404(Produk, produk_id)
    terkait = (Produk.query.filter(Produk.merek == produk.merek, Produk.id != produk.id)
               .order_by(Produk.created_at.desc()).limit(4).all())
    return render_template("toko/detail.html", produk=produk, terkait=terkait,
                           maks_per_produk=KeranjangItem.MAKS_PER_PRODUK)
