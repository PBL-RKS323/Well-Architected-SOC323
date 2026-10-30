from flask_wtf import FlaskForm
from wtforms import RadioField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, Optional

from forms.pesanan_form import _rapikan
from models.ulasan import Ulasan


class UlasanForm(FlaskForm):
    rating = RadioField("Rating", coerce=int, choices=[(n, f"{n} bintang") for n in range(1, 6)],
                        validators=[InputRequired(message="Pilih rating 1 sampai 5 bintang.")])
    komentar = TextAreaField("Komentar (opsional)", filters=[_rapikan], validators=[
        Optional(), Length(max=Ulasan.MAKS_KOMENTAR, message=f"Komentar maksimal {Ulasan.MAKS_KOMENTAR} karakter.")])
    submit = SubmitField("Kirim Ulasan")


class BalasanForm(FlaskForm):
    balasan = TextAreaField("Balasan Toko", filters=[_rapikan], validators=[
        DataRequired(message="Balasan tidak boleh kosong."),
        Length(max=Ulasan.MAKS_KOMENTAR, message=f"Balasan maksimal {Ulasan.MAKS_KOMENTAR} karakter.")])
    submit = SubmitField("Kirim Balasan")
