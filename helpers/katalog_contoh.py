"""Katalog contoh (seed/katalog.json + seed/foto/) untuk demo dan halaman kredit foto."""
import json
import os

from werkzeug.datastructures import FileStorage

from helpers.image_security import upload_secure_image, delete_image
from models import db
from models.produk import Produk


def path_katalog(app):
    return os.path.join(app.root_path, "seed", "katalog.json")


def baca_katalog(app):
    with open(path_katalog(app), encoding="utf-8") as f:
        return json.load(f)["produk"]


def _simpan_foto(app, nama_foto):
    """Foto tetap lewat validasi yang sama dengan upload admin (ukuran, magic number, nama acak)."""
    path = os.path.join(app.root_path, "seed", "foto", nama_foto)
    with open(path, "rb") as f:
        nama_file = upload_secure_image(FileStorage(f, filename=nama_foto), app.config["UPLOAD_FOLDER"])
    if not nama_file:
        raise ValueError(f"Foto {nama_foto} ditolak validasi gambar.")
    return nama_file


def isi_katalog(app, perbarui_foto=False):
    """Tambahkan produk contoh yang belum ada (dicek dari nama).

    perbarui_foto=True: foto produk contoh yang sudah ada diganti dengan versi terbaru di seed/foto
    (data lain seperti harga & stok yang mungkin sudah diubah admin tidak disentuh).
    Produk contoh lama yang spesifikasi/garansinya masih kosong ikut dilengkapi; isian admin tidak ditimpa.
    Mengembalikan (jumlah produk baru, jumlah foto diperbarui, jumlah produk yang dilengkapi).
    """
    dibuat = diperbarui = dilengkapi = 0
    from models.kategori import Kategori
    from models.kupon import Kupon
    Kategori.inisialisasi_bawaan()
    Kupon.inisialisasi_bawaan()
    for p in baca_katalog(app):
        spesifikasi = "\n".join(p.get("spesifikasi", [])) or None
        produk = Produk.query.filter_by(nama_produk=p["nama_produk"]).first()
        if produk is not None:
            if perbarui_foto:
                lama = produk.gambar
                produk.gambar = _simpan_foto(app, p["foto"])
                delete_image(lama, app.config["UPLOAD_FOLDER"])
                diperbarui += 1
            if (not produk.spesifikasi and spesifikasi) or (not produk.garansi and p.get("garansi")):
                produk.spesifikasi = produk.spesifikasi or spesifikasi
                produk.garansi = produk.garansi or p.get("garansi")
                dilengkapi += 1
            continue
        db.session.add(Produk(
            nama_produk=p["nama_produk"], merek=p["merek"], kategori=p["kategori"],
            harga=p["harga"], harga_normal=p["harga_normal"], stok=p["stok"],
            deskripsi=p["deskripsi"], spesifikasi=spesifikasi, garansi=p.get("garansi"),
            gambar=_simpan_foto(app, p["foto"]),
        ))
        dibuat += 1
    db.session.commit()
    return dibuat, diperbarui, dilengkapi
