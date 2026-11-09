# Panduan Komponen Desain Antarmuka

Dokumentasi ini merangkum sistem desain dan keputusan tata letak antarmuka pengguna (UI/UX) untuk aplikasi web e-commerce Elektronik Store PBL RKS 323.

## 1. Palet Warna & Aksesibilitas

Seluruh warna telah diuji terhadap rasio kontras WCAG 2.1 level AA (minimal 4.5:1 untuk teks normal):
- **Brand (`#1A68D1`)**: Warna aksi utama (tombol CTA, navigasi aktif, link penting).
- **Brand Dark (`#1553A8`)**: Keadaan hover pada tombol aksi untuk memberikan umpan balik visual yang jelas.
- **Brand Soft (`#EAF2FD`)**: Latar belakang chip kategori, ikon sekunder, dan penanda status ringan.
- **Ink (`#1F2937`)**: Warna teks primer berlatar terang untuk kenyamanan membaca optimal.
- **Muted (`#636B78`)**: Warna teks sekunder (deskripsi singkat, spesifikasi, dan metadata).
- **Soft (`#F4F6F8`)**: Latar belakang dasar halaman untuk mereduksi kelelahan mata.

## 2. Tipografi & Hierarki

- **Heading**: Menggunakan font Plus Jakarta Sans untuk memberikan kesan modern, rapi, dan kokoh pada judul produk dan label harga.
- **Body & Form**: Menggunakan font Inter untuk memastikan legibilitas teks deskripsi, spesifikasi teknis, serta formulir input.

## 3. Komponen Utama

- **Kartu Produk**: Memiliki batas lembut (`border-slate-100`), padding terukur, gambar proporsional (`aspect-square`), indikator stok/diskon, serta tombol aksi cepat.
- **Footer Partner**: Grid responsif dua kolom yang menampilkan logo resmi metode pembayaran dan mitra pengiriman berlatar putih dengan border presisi.
- **Navigasi Bawah Mobile**: Memiliki target sentuh minimal 44x44px untuk memastikan keramahan penggunaan pada perangkat layar sentuh.
