# Arah Desain

Sumber utama: desain Figma tim (Intan), salinan PDF ada di folder Drive
`web-fundamental/figma/Design Web PBL.pdf`. File ini mencatat keputusan visual beserta alasannya
supaya perubahan berikutnya tetap konsisten dan tidak terlihat seperti template generik.
Aturan pemeriksaan yang dipakai: [antislop](https://github.com/miqdadbadjuber/anti-slop) (R-01 s.d. R-38).

## Karakter

Toko gadget yang rapi dan tenang: produk (foto) yang menonjol, bukan dekorasinya. Pembeli
kebanyakan membuka dari HP, admin bekerja di laptop.

- ENERGY 2/5: satu warna aksi (biru), latar netral, tanpa gradien atau glow.
- RHYTHM 2/5: kartu produk seragam di grid, tiap halaman punya satu titik fokus.
- MOTION 1/5: hanya perubahan warna saat hover. Tidak ada animasi zoom, fade, atau parallax.

## Warna

| Token | Nilai | Dipakai untuk | Alasan |
|---|---|---|---|
| `brand` | `#1A68D1` | Tombol utama, link, langkah aktif | Biru moodboard (`#2F80ED`) digelapkan karena teks putih di atasnya hanya 3,9:1. Sekarang 5,3:1 (lolos WCAG AA). Mockup Figma juga memakai biru yang lebih gelap untuk tombol. |
| `brand-dark` | `#1553A8` | Hover tombol | Umpan balik hover tanpa efek tambahan |
| `brand-soft` | `#EAF2FD` | Latar chip, ikon, info status | Biru muda dari moodboard |
| `ink` | `#1F2937` | Teks utama | Slate gelap dari moodboard |
| `muted` | `#636B78` | Teks sekunder | Abu bawaan (`#6B7280`) hanya 4,4:1 di atas latar `soft`; digelapkan menjadi 4,96:1 |
| `soft` | `#F4F6F8` | Latar halaman | Soft Gray dari moodboard |
| `peach` | `#FDF0EA` | Banner produk unggulan | Warna banner promo di Figma, dipakai solid (tanpa gradien) |
| `coral` | `#C8291D` | Diskon, error, batal | Coral Red moodboard (`#F04438`) hanya 3,8:1; digelapkan menjadi 5,5:1 |

Warna status (amber = perlu tindakan, emerald = selesai) hanya dipakai di badge status pesanan.

## Tipografi

- **Plus Jakarta Sans** untuk judul dan harga, **Inter** untuk isi (keduanya ada di moodboard).
- Label kecil berhuruf kapital (mis. `NOMOR PESANAN`, `METODE PENGIRIMAN`) memakai `tracking-wider`
  karena begitu di mockup checkout, dan hanya untuk judul bagian form, bukan dekorasi.

## Komponen

- **Tombol**: berbentuk pil (sesuai mockup). Tanpa bayangan berwarna. Panah hanya ada di tombol
  Checkout karena tombol itu memang berpindah ke langkah berikutnya.
- **Kartu**: sudut 16-24px dan border tipis, tanpa bayangan. Bayangan hanya untuk elemen yang
  benar-benar melayang: navigasi bawah HP dan bar bayar di checkout.
- **Badge**: hanya untuk informasi nyata (status pesanan, persen diskon, sisa stok, "Segera" untuk
  fitur yang belum ada). Tidak ada badge hiasan.
- **Ikon**: Lucide garis tipis, hanya bila menjelaskan isi (kategori, metode kirim, status). Ikon
  sparkle dan api dihapus karena tidak menjelaskan apa pun.
- **Motif**: garis vertikal biru kecil di kiri judul bagian beranda.
- **Area sentuh** minimal 44x44px. Jika lingkaran tombol lebih kecil (mis. tombol + di kartu produk
  36px), area klik tetap 44px lewat padding.

## Konten

- Tidak ada angka, testimoni, rating, atau klaim yang tidak berasal dari data. Contoh yang dihapus:
  "PROMO MINGGU INI" (tidak ada data periode promo), "estimasi 2-4 hari kerja", "biasanya selesai
  dalam beberapa jam".
- Data toko yang masih contoh (rekening, alamat toko, ongkir) diatur lewat `.env` dan disebut dummy
  di README.
- Fitur yang belum ada (QRIS/e-wallet lewat Midtrans) diberi label "Segera" dan tidak bisa diklik.

## Tema

Hanya tema terang, sesuai mockup Figma. Tidak ada toggle mode gelap karena tidak diminta desain.
