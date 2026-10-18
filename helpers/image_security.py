import os
import uuid

import puremagic

ALLOWED_MIME_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def upload_secure_image(file_data, target_folder):
    """Menyimpan gambar setelah lolos cek ukuran dan isi biner.

    Mengembalikan nama file baru, atau None jika file ditolak.
    """
    if not file_data or not getattr(file_data, "filename", ""):
        return None

    # 1. Validasi ukuran
    file_data.stream.seek(0, os.SEEK_END)
    file_size = file_data.stream.tell()
    file_data.stream.seek(0)
    if file_size == 0 or file_size > MAX_FILE_SIZE:
        return None

    # 2. Validasi isi biner (magic number), bukan sekadar ekstensi
    header = file_data.stream.read(2048)
    file_data.stream.seek(0)
    try:
        actual_mime = puremagic.from_string(header, mime=True)
    except puremagic.PureError:
        return None
    if actual_mime not in ALLOWED_MIME_TYPES:
        return None

    # 3. Nama file acak dengan ekstensi sesuai isi asli, nama asli dari pengguna dibuang
    unique_filename = f"{uuid.uuid4().hex}{ALLOWED_MIME_TYPES[actual_mime]}"

    os.makedirs(target_folder, exist_ok=True)
    file_data.save(os.path.join(target_folder, unique_filename))
    return unique_filename


def delete_image(filename, target_folder):
    if not filename:
        return
    # basename mencegah path traversal jika nilai di database dimanipulasi
    path = os.path.join(target_folder, os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)
