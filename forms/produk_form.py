import os

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, TextAreaField, FileField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError

from models.produk import Produk

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


class FormProduk(FlaskForm):
    nama_produk = StringField("Nama Produk", validators=[
        DataRequired(message="Nama produk wajib diisi!"),
        Length(min=3, max=100, message="Nama produk harus di antara 3 hingga 100 karakter."),
    ])
    merek = SelectField("Merek", choices=[(m, m) for m in Produk.MEREK],
                        validators=[DataRequired(message="Merek wajib dipilih!")])
    kategori = SelectField("Kategori", choices=[(k, k) for k in Produk.KATEGORI],
                           validators=[DataRequired(message="Kategori wajib dipilih!")])
    harga = DecimalField("Harga (Rp)", places=2, validators=[
        DataRequired(message="Harga wajib diisi dengan angka!"),
        NumberRange(min=1000, max=999_999_999, message="Harga harus antara Rp 1.000 dan Rp 999.999.999"),
    ])
    stok = IntegerField("Stok", validators=[
        InputRequired(message="Stok wajib diisi!"),
        NumberRange(min=0, max=100_000, message="Stok harus antara 0 dan 100.000"),
    ])
    deskripsi = TextAreaField("Deskripsi", validators=[
        Length(max=1000, message="Deskripsi tidak boleh melebihi 1000 karakter."),
    ])
    gambar = FileField("Foto Produk (JPG/PNG, maks. 2 MB)")
    submit = SubmitField("Simpan")

    # Validasi lapis pertama: ekstensi nama file. Lapis kedua (isi biner) ada di helpers/image_security.py
    def validate_gambar(self, field):
        if field.data and getattr(field.data, "filename", ""):
            ext = os.path.splitext(field.data.filename)[1].lower().lstrip(".")
            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError("Ekstensi file ditolak! Hanya menerima .jpg, .jpeg, .png")
