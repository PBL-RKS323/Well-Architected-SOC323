# Panduan Komponen Desain Antarmuka
Disusun oleh: **Intan Sri Diana** (Desain UI/UX)
Proyek: PBL Rekayasa Keamanan Siber (RKS 323), Politeknik Negeri Batam

---

## 1. Palet Warna e-shop. & Aksesibilitas

Seluruh palet warna dikonfigurasikan melalui browser engine **Tailwind CSS v4** (`@theme`) dan telah terverifikasi memenuhi standar rasio kontras **WCAG 2.1 level AA**:

- **Brand Coral (`#F05537`)**: Warna aksi utama e-shop (tombol CTA, badge diskon, active indicator, logo).
- **Brand Coral Dark (`#D94426`)**: Keadaan hover dan interaksi aktif untuk memberikan feedback taktil visual.
- **Brand Soft Peach (`#FFF2EE`)**: Latar belakang chip kategori, highlight kupon, dan badge penawaran.
- **Ink Primary (`#1A1D20`)**: Warna teks utama berlatar putih dengan tingkat keterbacaan tinggi.
- **Muted Slate (`#71777D`)**: Warna label form, teks sekunder, spesifikasi, dan metadata tanggal.
- **Soft Light (`#F8F9FA`)**: Latar belakang halaman untuk kesan modern, bersih, dan meminimalkan silau mata.

---

## 2. Tipografi & Skala Hirarki

- **Heading & Logo**: Menggunakan font **Plus Jakarta Sans** (bobot 700 & 800) untuk memberikan kesan modern, dinamis, dan tegas pada judul produk serta header halaman.
- **Body, Form & Spesifikasi**: Menggunakan font **Inter** (bobot 400, 500, 600) untuk menjamin legibilitas optimal pada deskripsi panjang, checkout, dan rincian transaksi.

---

## 3. Komponen Antarmuka e-shop Utama

1. **Top Utility Bar & Brand Navbar**:
   - Menampilkan kontak layanan bantuan, garansi resmi 100%, navigasi cepat, dan pencarian kategori cerdas.
2. **Kartu Produk Dinamis**:
   - Rasio gambar `aspect-square` dengan hover zoom halus (`scale-105`).
   - Tombol wishlist/favorit berbentuk floating heart di pojok kanan atas.
   - Badge persentase diskon (`-X%`) berlatar coral kontras.
   - Tombol floating tambah keranjang bulat di pojok kartu.
3. **Komponen Kupon & Voucher Checkout**:
   - Input voucher terintegrasi dengan validasi asinkronus (AJAX) dan badge diskon interaktif.
4. **Halaman Profil Terpadu & Keamanan**:
   - Layout 4-tab intuitif: Biodata Pengguna, Riwayat Pesanan dengan visual stepper 5 tahap, Alamat Pengiriman, dan Pusat Keamanan Akun (Password Strength Meter real-time + Security Log).
5. **Footer Partner 16 Badge**:
   - Grid terstruktur 5 kolom yang menampilkan badge resmi metode pembayaran instan (BCA, Mandiri, BRI, BNI, QRIS, GoPay, OVO, DANA) dan mitra logistik tepercaya (JNE, SiCepat, J&T, Paxel, POS Indonesia, Anteraja, Ninja Xpress, Wahana).
