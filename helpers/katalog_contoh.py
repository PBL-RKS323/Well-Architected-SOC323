"""Katalog contoh (seed/katalog.json + seed/foto/) untuk demo dan halaman kredit foto."""
import json
import os

from werkzeug.datastructures import FileStorage

from helpers.image_security import upload_secure_image
from models import db
from models.produk import Produk


def path_katalog(app):
    return os.path.join(app.root_path, "seed", "katalog.json")


def baca_katalog(app):
    with open(path_katalog(app), encoding="utf-8") as f:
        return json.load(f)["produk"]


def isi_katalog(app):
    """Tambahkan produk contoh yang belum ada (dicek dari nama). Mengembalikan jumlah produk baru."""
    folder_foto = os.path.join(app.root_path, "seed", "foto")
    dibuat = 0
    for p in baca_katalog(app):
        if Produk.query.filter_by(nama_produk=p["nama_produk"]).first():
            continue
        # Foto tetap lewat validasi yang sama dengan upload admin (ukuran, magic number, nama acak)
        with open(os.path.join(folder_foto, p["foto"]), "rb") as f:
            nama_file = upload_secure_image(FileStorage(f, filename=p["foto"]), app.config["UPLOAD_FOLDER"])
        if not nama_file:
            raise ValueError(f"Foto {p['foto']} ditolak validasi gambar.")
        db.session.add(Produk(
            nama_produk=p["nama_produk"], merek=p["merek"], kategori=p["kategori"],
            harga=p["harga"], harga_normal=p["harga_normal"], stok=p["stok"],
            deskripsi=p["deskripsi"], gambar=nama_file,
        ))
        dibuat += 1
    db.session.commit()
    return dibuat
