import os
import uuid

import puremagic
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_MIME_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
AVATAR_SIZE = 256  # piksel, foto profil disimpan persegi
MAX_PIXELS = 40_000_000  # tolak "decompression bomb" (file kecil yang mengembang jadi gambar raksasa)


def _cek_gambar(file_data):
    """Cek ukuran & isi biner (magic number), bukan sekadar ekstensi.
    Mengembalikan MIME asli file, atau None jika ditolak."""
    if not file_data or not getattr(file_data, "filename", ""):
        return None

    # 1. Validasi ukuran
    file_data.stream.seek(0, os.SEEK_END)
    file_size = file_data.stream.tell()
    file_data.stream.seek(0)
    if file_size == 0 or file_size > MAX_FILE_SIZE:
        return None

    # 2. Validasi isi biner
    header = file_data.stream.read(2048)
    file_data.stream.seek(0)
    try:
        actual_mime = puremagic.from_string(header, mime=True)
    except puremagic.PureError:
        return None
    return actual_mime if actual_mime in ALLOWED_MIME_TYPES else None


def upload_secure_image(file_data, target_folder):
    """Menyimpan gambar setelah lolos cek ukuran dan isi biner.

    Mengembalikan nama file baru, atau None jika file ditolak.
    """
    actual_mime = _cek_gambar(file_data)
    if actual_mime is None:
        return None

    # 3. Nama file acak dengan ekstensi sesuai isi asli, nama asli dari pengguna dibuang
    unique_filename = f"{uuid.uuid4().hex}{ALLOWED_MIME_TYPES[actual_mime]}"

    os.makedirs(target_folder, exist_ok=True)
    file_data.save(os.path.join(target_folder, unique_filename))
    return unique_filename


def simpan_avatar(file_data, target_folder):
    """Foto profil: setelah lolos cek di atas, gambar dibuka dan di-encode ulang menjadi JPEG persegi.

    Encode ulang membuang metadata EXIF (bisa berisi lokasi GPS & tipe HP pengguna) dan semua isi
    tersembunyi di dalam file (file polyglot), karena yang disimpan hanya piksel gambarnya.
    Mengembalikan nama file baru, atau None jika file ditolak.
    """
    if _cek_gambar(file_data) is None:
        return None
    try:
        with Image.open(file_data.stream) as img:
            if img.width * img.height > MAX_PIXELS:
                return None
            img.load()
            img = ImageOps.exif_transpose(img)  # foto HP tetap tegak walau EXIF-nya dibuang
            img = ImageOps.fit(img.convert("RGB"), (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        return None

    unique_filename = f"{uuid.uuid4().hex}.jpg"
    os.makedirs(target_folder, exist_ok=True)
    img.save(os.path.join(target_folder, unique_filename), "JPEG", quality=85, optimize=True)
    return unique_filename


def delete_image(filename, target_folder):
    if not filename:
        return
    # basename mencegah path traversal jika nilai di database dimanipulasi
    path = os.path.join(target_folder, os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)
