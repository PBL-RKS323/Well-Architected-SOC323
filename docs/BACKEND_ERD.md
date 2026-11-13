# Dokumentasi Arsitektur Database & ERD E-Commerce
Disusun oleh: **Pedro Juanda Sebayang** (Backend Engineer)
Proyek: PBL Rekayasa Keamanan Siber (RKS 323), Politeknik Negeri Batam

---

## 1. Ringkasan Desain Skema Basis Data

Aplikasi web e-commerce Elektronik Store menggunakan arsitektur relasional berbasis **SQLAlchemy ORM** dan **Flask-Migrate (Alembic)** yang dinormalisasi ke Third Normal Form (3NF).

### Entitas Utama dan Kardinalitas:
1. **`users`** (1:N ke `pesanan`, `alamat`, `keranjang_item`, `ulasan`, `favorit`, `kode_otp`)
   - Menyimpan kredensial otentikasi (argon2 hash), role RBAC (`admin`, `staf`, `pelanggan`), counter gagal login, dan token rotasi sesi.
2. **`kategori`** (1:N ke `produk`)
   - Normalisasi katalog untuk mengelompokkan barang belanjaan berdasarkan jenis perangkat (Handphone, Laptop, Smartwatch, Tablet, Audio, Aksesoris).
3. **`produk`** (N:1 ke `kategori`, 1:N ke `pesanan_item`, `keranjang_item`, `ulasan`, `favorit`)
   - Menyimpan spesifikasi teknis terstruktur, histori harga promo/normal, persentase diskon, dan batas stok menipis.
4. **`pesanan`** (N:1 ke `users`, N:1 ke `kupon`, 1:N ke `pesanan_item`, `pesanan_riwayat`, 1:N ke `pembayaran`)
   - Transaksi pemesanan dengan snapshot alamat, status alur pesanan, subtotal, ongkir flat, dan potongan diskon kupon.
5. **`kupon`** (1:N ke `pesanan`)
   - Manajemen kode voucher promosi diskon (tipe persentase maupun nominal), batas minimum belanja, kuota kupon, dan masa berlaku.
6. **`favorit`** (Wishlist - relasi N:M antara `users` dan `produk`)
   - Dilengkapi *unique constraint* composite `(user_id, produk_id)` untuk mencegah redundansi wishlist.
7. **`pembayaran`** (N:1 ke `pesanan`, N:1 ke `users` sebagai verifikator)
   - Audit trail transaksi pembayaran, bukti transfer bank, status verifikasi (`pending`, `diverifikasi`, `ditolak`), dan pencatatan staf verifikator.

---

## 2. Diagram Hubungan Entitas (ERD)

```mermaid
erDiagram
    USERS ||--o{ PESANAN : "membuat"
    USERS ||--o{ ALAMAT : "menyimpan"
    USERS ||--o{ KERANJANG_ITEM : "memiliki"
    USERS ||--o{ FAVORIT : "menyimpan"
    USERS ||--o{ ULASAN : "menulis"
    KATEGORI ||--o{ PRODUK : "mengelompokkan"
    PRODUK ||--o{ PESANAN_ITEM : "dibeli dalam"
    PRODUK ||--o{ KERANJANG_ITEM : "dimasukkan ke"
    PRODUK ||--o{ FAVORIT : "difavoritkan"
    PESANAN ||--|{ PESANAN_ITEM : "berisi"
    PESANAN ||--o{ PESANAN_RIWAYAT : "merekam jejak"
    PESANAN ||--o{ PEMBAYARAN : "diverifikasi lewat"
    KUPON ||--o{ PESANAN : "diterapkan pada"

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        string nama_lengkap
        string telepon
        string jenis_kelamin
        date tanggal_lahir
    }

    KATEGORI {
        int id PK
        string nama UK
        string slug UK
        string ikon
        int urutan
        boolean aktif
    }

    PRODUK {
        int id PK
        string nama_produk
        string merek
        string kategori
        int kategori_id FK
        numeric harga
        numeric harga_normal
        int stok
        text spesifikasi
        string garansi
    }

    KUPON {
        int id PK
        string kode UK
        string tipe
        numeric nilai
        numeric min_belanja
        numeric maks_potongan
        int kuota
        int terpakai
        boolean aktif
    }

    FAVORIT {
        int id PK
        int user_id FK
        int produk_id FK
        datetime created_at
    }

    PESANAN {
        int id PK
        string kode UK
        int user_id FK
        int kupon_id FK
        numeric subtotal
        numeric ongkir
        numeric diskon
        numeric total
        string status
    }

    PEMBAYARAN {
        int id PK
        int pesanan_id FK
        numeric jumlah
        string status
        int diverifikasi_oleh FK
        datetime waktu_bayar
    }
```

---

## 3. Strategi Indexing & Integritas Referensial
- **Indeks Unik**: `users.username`, `users.email`, `kategori.slug`, `kupon.kode`, `pesanan.kode`.
- **Indeks Pencarian**: `produk.kategori_id`, `pesanan.user_id`, `pesanan.status`, `favorit.user_id`, `pembayaran.status`.
- **Integritas Cascade**:
  - `ON DELETE CASCADE`: menghapus `keranjang_item` dan `favorit` saat pengguna atau produk dihapus.
  - `ON DELETE SET NULL`: menjaga riwayat pemesanan tetap utuh (`kupon_id` dan `kategori_id`) meskipun master kupon atau kategori diarsipkan.
