import logging
import os

from flask import render_template, redirect, url_for, flash, request, g, current_app, abort, send_from_directory
from sqlalchemy import exists

from controllers.toko_controller import _escape_like
from forms.pesanan_form import CheckoutForm, BuktiBayarForm
from helpers.image_security import upload_secure_image, delete_image
from helpers.security_logger import log_event
from middlewares.auth_middleware import pelanggan_required
from models import db, utcnow
from models.alamat import Alamat
from models.keranjang import KeranjangItem
from models.pesanan import Pesanan, PesananItem, PesananRiwayat
from models.produk import Produk
from models.ulasan import Ulasan

PER_HALAMAN = 10
TAB = {
    "semua": None,
    "aktif": Pesanan.STATUS_AKTIF,
    "selesai": [Pesanan.SELESAI],
    "dibatalkan": [Pesanan.DIBATALKAN],
}


def _pesanan_milik_user(kode):
    """Pesanan hanya bisa dibuka pemiliknya. Percobaan membuka pesanan orang lain dicatat (IDOR)."""
    pesanan = Pesanan.query.filter_by(kode=kode).first()
    if pesanan is None:
        abort(404)
    if pesanan.user_id != g.user.id:
        log_event("ACCESS_DENIED", logging.WARNING, user_id=g.user.id, username=g.user.username,
                  resource="pesanan", kode=kode)
        abort(404)  # 404, bukan 403, agar keberadaan pesanan orang lain tidak terungkap
    return pesanan


def _ongkir(metode):
    return current_app.config["ONGKIR_FLAT"] if metode == Pesanan.KURIR else 0


def _prefill_alamat(form, daftar_alamat):
    """Isi form alamat agar pelanggan tidak mengetik ulang. Urutan sumber: alamat yang dipilih (?alamat=id),
    alamat utama, lalu pesanan kurir terakhir. Mengembalikan id alamat tersimpan yang dipakai (atau None)."""
    dipilih = request.args.get("alamat", type=int)
    sumber = next((a for a in daftar_alamat if a.id == dipilih), None) or \
        next((a for a in daftar_alamat if a.utama), None) or \
        (Pesanan.query.filter_by(user_id=g.user.id, metode_pengiriman=Pesanan.KURIR)
         .order_by(Pesanan.created_at.desc()).first())
    form.nama_penerima.data = g.user.nama_lengkap or None
    if sumber is None:
        return None
    for kolom in ("nama_penerima", "telepon", "alamat", "kota", "kode_pos"):
        getattr(form, kolom).data = getattr(sumber, kolom)
    return sumber.id if isinstance(sumber, Alamat) else None


def _simpan_alamat_baru(form, daftar_alamat):
    """Checkbox "Simpan alamat ini": tambahkan ke Alamat Saya jika belum ada yang sama dan kuota belum penuh."""
    sama = any(a.alamat == form.alamat.data and a.kode_pos == form.kode_pos.data for a in daftar_alamat)
    if sama or len(daftar_alamat) >= Alamat.MAKS_PER_USER:
        return
    alamat = Alamat(user_id=g.user.id, label=f"Alamat {len(daftar_alamat) + 1}", nama_penerima=form.nama_penerima.data,
                    telepon=form.telepon.data, alamat=form.alamat.data, kota=form.kota.data,
                    kode_pos=form.kode_pos.data, utama=not daftar_alamat)
    db.session.add(alamat)


@pelanggan_required
def checkout():
    items = (KeranjangItem.query.filter_by(user_id=g.user.id)
             .order_by(KeranjangItem.created_at.desc()).all())
    if not items:
        flash("Keranjangmu masih kosong.", "info")
        return redirect(url_for("belanja.keranjang"))
    if any(i.produk.stok == 0 or i.jumlah > i.produk.stok for i in items):
        flash("Ada produk yang stoknya habis atau kurang. Perbaiki keranjang terlebih dahulu.", "warning")
        return redirect(url_for("belanja.keranjang"))

    form = CheckoutForm()
    subtotal = sum(i.subtotal for i in items)
    hemat = sum((i.produk.harga_normal - i.produk.harga) * i.jumlah for i in items if i.produk.diskon_persen)
    daftar_alamat = Alamat.milik(g.user.id).all()
    alamat_dipakai = None

    if request.method == "GET":
        alamat_dipakai = _prefill_alamat(form, daftar_alamat)

    if form.validate_on_submit():
        # Pesanan yang bukti bayarnya belum diverifikasi ikut dihitung, supaya batas ini tidak bisa
        # diakali dengan mengunggah bukti palsu agar stok tetap tertahan
        belum_lunas = Pesanan.query.filter(
            Pesanan.user_id == g.user.id,
            Pesanan.status.in_([Pesanan.MENUNGGU_PEMBAYARAN, Pesanan.MENUNGGU_VERIFIKASI])).count()
        if belum_lunas >= current_app.config["MAKS_PESANAN_BELUM_BAYAR"]:
            flash("Kamu masih punya beberapa pesanan yang belum lunas. Selesaikan atau batalkan dulu.", "warning")
            return redirect(url_for("belanja.pesanan"))

        kurir = form.metode_pengiriman.data == Pesanan.KURIR
        ongkir = _ongkir(form.metode_pengiriman.data)
        pesanan = Pesanan(
            kode=Pesanan.buat_kode(), user_id=g.user.id, status=Pesanan.MENUNGGU_PEMBAYARAN,
            metode_pengiriman=form.metode_pengiriman.data, metode_pembayaran=form.metode_pembayaran.data,
            nama_penerima=form.nama_penerima.data, telepon=form.telepon.data,
            alamat=form.alamat.data if kurir else None, kota=form.kota.data if kurir else None,
            kode_pos=form.kode_pos.data if kurir else None, catatan=form.catatan.data or None,
            subtotal=subtotal, ongkir=ongkir, total=subtotal + ongkir, batas_bayar=Pesanan.hitung_batas_bayar(),
        )
        db.session.add(pesanan)

        # Kosongkan keranjang lebih dulu. Jika jumlah baris yang terhapus kurang, berarti keranjang ini
        # sudah diproses request lain (mis. tombol diklik dua kali), jadi pesanan kedua dibatalkan.
        ids = [i.id for i in items]
        terhapus = (KeranjangItem.query.filter(KeranjangItem.id.in_(ids), KeranjangItem.user_id == g.user.id)
                    .delete(synchronize_session=False))
        if terhapus != len(ids):
            db.session.rollback()
            flash("Pesanan ini sudah dibuat. Cek di Pesanan Saya.", "info")
            return redirect(url_for("belanja.pesanan"))

        for item in items:
            produk = item.produk
            nama = produk.nama_produk
            # Kurangi stok secara atomik: hanya berhasil jika stok masih cukup saat ini juga
            # (mencegah stok minus jika dua pelanggan checkout produk terakhir bersamaan)
            berhasil = (Produk.query.filter(Produk.id == produk.id, Produk.stok >= item.jumlah)
                        .update({Produk.stok: Produk.stok - item.jumlah}, synchronize_session=False))
            if not berhasil:
                db.session.rollback()
                flash(f"Stok {nama} baru saja berubah. Periksa kembali keranjangmu.", "warning")
                return redirect(url_for("belanja.keranjang"))
            pesanan.items.append(PesananItem(produk_id=produk.id, nama_produk=produk.nama_produk,
                                             merek=produk.merek, harga=produk.harga, jumlah=item.jumlah))

        pesanan.riwayat.append(PesananRiwayat(status=Pesanan.MENUNGGU_PEMBAYARAN, oleh="pelanggan",
                                              keterangan="Pesanan dibuat"))
        if kurir and form.simpan_alamat.data:
            _simpan_alamat_baru(form, daftar_alamat)
        db.session.commit()

        log_event("ORDER_CREATE", user_id=g.user.id, kode=pesanan.kode, total=int(pesanan.total),
                  items=len(pesanan.items), shipping=pesanan.metode_pengiriman)
        return redirect(url_for("belanja.pesanan_konfirmasi", kode=pesanan.kode))

    return render_template("toko/checkout.html", form=form, items=items, subtotal=subtotal, hemat=hemat,
                           ongkir_kurir=_ongkir(Pesanan.KURIR), daftar_alamat=daftar_alamat,
                           alamat_dipakai=alamat_dipakai)


@pelanggan_required
def konfirmasi(kode):
    pesanan = _pesanan_milik_user(kode)
    return render_template("toko/pesanan_konfirmasi.html", pesanan=pesanan)


@pelanggan_required
def index():
    Pesanan.batalkan_kedaluwarsa()
    tab = request.args.get("tab", "semua")
    if tab not in TAB:
        tab = "semua"
    q = request.args.get("q", "").strip()[:50]

    dasar = Pesanan.query.filter_by(user_id=g.user.id)
    if q:
        pola = f"%{_escape_like(q)}%"
        cocok_produk = exists().where(PesananItem.pesanan_id == Pesanan.id,
                                      PesananItem.nama_produk.ilike(pola, escape="\\"))
        dasar = dasar.filter(Pesanan.kode.ilike(pola, escape="\\") | cocok_produk)

    jumlah_tab = {nama: (dasar.filter(Pesanan.status.in_(st)) if st else dasar).count() for nama, st in TAB.items()}
    query = dasar.filter(Pesanan.status.in_(TAB[tab])) if TAB[tab] else dasar
    halaman = query.order_by(Pesanan.created_at.desc()).paginate(per_page=PER_HALAMAN, error_out=False)
    return render_template("toko/pesanan.html", halaman=halaman, tab=tab, q=q, jumlah_tab=jumlah_tab)


@pelanggan_required
def detail(kode):
    Pesanan.batalkan_kedaluwarsa()
    pesanan = _pesanan_milik_user(kode)
    sudah_diulas = set()
    if pesanan.status == Pesanan.SELESAI:
        sudah_diulas = {pid for (pid,) in db.session.query(Ulasan.produk_id).filter_by(user_id=g.user.id)}
    return render_template("toko/pesanan_detail.html", pesanan=pesanan, form_bukti=BuktiBayarForm(),
                           sudah_diulas=sudah_diulas)


@pelanggan_required
def unggah_bukti(kode):
    pesanan = _pesanan_milik_user(kode)
    form = BuktiBayarForm()
    if pesanan.status != Pesanan.MENUNGGU_PEMBAYARAN:
        flash("Bukti bayar tidak bisa diunggah untuk pesanan ini.", "warning")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))

    if not form.validate_on_submit():
        for error in form.bukti.errors:
            flash(error, "danger")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))

    folder = current_app.config["BUKTI_BAYAR_FOLDER"]
    nama_file = upload_secure_image(form.bukti.data, folder)
    if not nama_file:
        log_event("UPLOAD_REJECTED", logging.WARNING, user_id=g.user.id, filename=form.bukti.data.filename,
                  context="bukti_bayar", kode=kode)
        flash("File ditolak! Pastikan file benar-benar gambar JPG/PNG dan ukurannya maksimal 2 MB.", "danger")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))

    if not pesanan.ubah_status(Pesanan.MENUNGGU_VERIFIKASI, "pelanggan", "Bukti transfer diunggah"):
        delete_image(nama_file, folder)
        flash("Status pesanan sudah berubah. Muat ulang halaman.", "warning")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))

    delete_image(pesanan.bukti_bayar, folder)  # bukti lama yang pernah ditolak
    pesanan.bukti_bayar = nama_file
    pesanan.bukti_diunggah_at = utcnow()
    pesanan.alasan_tolak = None
    db.session.commit()

    log_event("PAYMENT_PROOF_UPLOADED", user_id=g.user.id, kode=kode)
    flash("Bukti bayar terkirim. Admin akan memeriksanya segera.", "success")
    return redirect(url_for("belanja.pesanan_detail", kode=kode))


def bukti(kode):
    """Menampilkan bukti bayar hanya untuk pemilik pesanan dan peran dengan izin kelola_pesanan."""
    pesanan = Pesanan.query.filter_by(kode=kode).first_or_404()
    if pesanan.user_id != g.user.id and not g.user.punya_izin("kelola_pesanan"):
        log_event("ACCESS_DENIED", logging.WARNING, user_id=g.user.id, username=g.user.username,
                  resource="bukti_bayar", kode=kode)
        abort(404)
    if not pesanan.bukti_bayar:
        abort(404)
    response = send_from_directory(current_app.config["BUKTI_BAYAR_FOLDER"],
                                   os.path.basename(pesanan.bukti_bayar), max_age=0)
    response.headers["Cache-Control"] = "private, no-store"
    return response


@pelanggan_required
def batal(kode):
    pesanan = _pesanan_milik_user(kode)
    # Pelanggan hanya boleh membatalkan sebelum mengirim bukti bayar
    if pesanan.status != Pesanan.MENUNGGU_PEMBAYARAN or \
            not pesanan.ubah_status(Pesanan.DIBATALKAN, "pelanggan", "Dibatalkan oleh pelanggan"):
        flash("Pesanan ini tidak bisa dibatalkan lagi. Hubungi admin jika perlu bantuan.", "warning")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))
    pesanan.alasan_tolak = "Dibatalkan oleh pelanggan."
    db.session.commit()
    log_event("ORDER_CANCELLED", user_id=g.user.id, kode=kode, by="customer")
    flash("Pesanan dibatalkan dan stok dikembalikan.", "info")
    return redirect(url_for("belanja.pesanan_detail", kode=kode))


@pelanggan_required
def terima(kode):
    pesanan = _pesanan_milik_user(kode)
    if pesanan.status != Pesanan.DIKIRIM or \
            not pesanan.ubah_status(Pesanan.SELESAI, "pelanggan", "Pesanan diterima pelanggan"):
        flash("Pesanan belum bisa dikonfirmasi diterima.", "warning")
        return redirect(url_for("belanja.pesanan_detail", kode=kode))
    db.session.commit()
    log_event("ORDER_STATUS_CHANGE", user_id=g.user.id, kode=kode, status=Pesanan.SELESAI, by="customer")
    flash("Terima kasih! Pesanan ditandai selesai.", "success")
    return redirect(url_for("belanja.pesanan_detail", kode=kode))


@pelanggan_required
def beli_lagi(kode):
    pesanan = _pesanan_milik_user(kode)
    ditambah = 0
    for item in pesanan.items:
        produk = item.produk
        if produk is None or produk.stok == 0:
            continue
        isi = KeranjangItem.query.filter_by(user_id=g.user.id, produk_id=produk.id).first()
        if isi is None:
            isi = KeranjangItem(user_id=g.user.id, produk_id=produk.id, jumlah=0)
            isi.produk = produk
            db.session.add(isi)
        isi.jumlah = min(isi.jumlah + item.jumlah, isi.batas)
        ditambah += 1
    db.session.commit()
    if ditambah:
        flash(f"{ditambah} produk dari pesanan {kode} ditambahkan ke keranjang.", "success")
    else:
        flash("Produk dari pesanan ini sudah tidak tersedia.", "warning")
    return redirect(url_for("belanja.keranjang"))
