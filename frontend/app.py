import os
from flask import Flask, render_template, request, abort

app = Flask(__name__)

# Template filter: Rupiah currency formatting
@app.template_filter('rupiah')
def rupiah_format(value):
    try:
        val = int(value)
        return f"Rp {val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"Rp {value}"

# Static dummy products data (sesuai data Figma asli)
PRODUCTS = [
    {
        "id": "prod-1",
        "name": "Xiaomi Redmi 13C 8/256GB",
        "slug": "xiaomi-redmi-13c",
        "brand": "Xiaomi",
        "category": "Smartphone",
        "image": "6ebd4.png",
        "price": 1599000,
        "original_price": 1999000,
        "stock": 24,
        "specs": "Layar 6,74 inci · RAM 8GB · Penyimpanan 256GB",
        "description": "Ruang lebih luas untuk cerita harianmu. Redmi 13C menggabungkan layar lega, kamera 50MP, dan baterai 5.000 mAh dalam desain yang nyaman digenggam.",
        "flash_sale": True,
        "flash_sale_ends_at": "2026-10-31T23:59:59",
        "featured": False,
        "sort_order": 0
    },
    {
        "id": "prod-2",
        "name": "POCO M6 Pro 5G 6/128GB",
        "slug": "poco-m6-pro",
        "brand": "POCO",
        "category": "Smartphone",
        "image": "93a8e.png",
        "price": 2199000,
        "original_price": 2799000,
        "stock": 18,
        "specs": "Snapdragon 4 Gen 2 · 5G · Baterai 5.000 mAh",
        "description": "Performa cepat untuk semua kegiatanmu. POCO M6 Pro hadir dengan konektivitas 5G, layar FHD+ yang jernih, dan daya tahan baterai untuk menemani aktivitas seharian.",
        "flash_sale": True,
        "flash_sale_ends_at": "2026-10-31T23:59:59",
        "featured": False,
        "sort_order": 1
    },
    {
        "id": "prod-3",
        "name": "MacBook Pro 14 inci M4",
        "slug": "macbook-pro-14-m4",
        "brand": "Apple",
        "category": "Laptop",
        "image": "macbook-pro-14.png",
        "price": 24999000,
        "original_price": 27999000,
        "stock": 8,
        "specs": "Apple M4 · RAM 16GB · SSD 512GB · Space Black",
        "description": "Tenaga untuk ide-ide besarmu. MacBook Pro 14 inci dengan chip M4 menawarkan performa andal, layar Liquid Retina XDR, serta desain aluminium yang elegan. Cocok untuk kreativitas, pekerjaan, dan produktivitas setiap hari.",
        "flash_sale": True,
        "flash_sale_ends_at": "2026-10-31T23:59:59",
        "featured": False,
        "sort_order": 2
    },
    {
        "id": "prod-4",
        "name": "Amazfit GTS 2 Mini Smartwatch",
        "slug": "amazfit-gts-2-mini",
        "brand": "Amazfit",
        "category": "Smartwatch",
        "image": "41a39.png",
        "price": 899000,
        "original_price": 1199000,
        "stock": 32,
        "specs": "Layar AMOLED · Pemantauan detak jantung · Tahan air 5 ATM",
        "description": "Teknologi yang mengikuti langkahmu. Pantau aktivitas, tidur, dan kebugaran dengan smartwatch ringan dan nyaman. Dilengkapi berbagai mode olahraga, notifikasi pintar, dan baterai tahan lama. Bukan perangkat diagnosis medis.",
        "flash_sale": True,
        "flash_sale_ends_at": "2026-10-31T23:59:59",
        "featured": False,
        "sort_order": 3
    },
    {
        "id": "prod-5",
        "name": "Beats Studio3 Wireless Headphone",
        "slug": "beats-studio3-wireless",
        "brand": "Beats",
        "category": "Audio",
        "image": "bc437.png",
        "price": 2899000,
        "original_price": 3499000,
        "stock": 12,
        "specs": "Wireless Bluetooth · Noise cancelling · Over-ear",
        "description": "Nikmati musik dengan fokus penuh. Beats Studio3 Wireless menghadirkan suara kaya, peredam bising aktif, dan bantalan yang nyaman untuk sesi mendengarkan panjang.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 4
    },
    {
        "id": "prod-6",
        "name": "iPhone 14 128GB — Blue",
        "slug": "iphone-14-128gb",
        "brand": "Apple",
        "category": "Smartphone",
        "image": "a0332.png",
        "price": 8999000,
        "original_price": 10999000,
        "stock": 15,
        "specs": "Chip A15 Bionic · Layar 6,1 inci · Penyimpanan 128GB",
        "description": "Semua hal yang kamu sukai dari iPhone. Tangkap momen dengan sistem kamera ganda, nikmati layar Super Retina XDR, dan andalkan performa chip A15 Bionic. Warna Blue, kapasitas 128GB.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 5
    },
    {
        "id": "prod-7",
        "name": "realme Narzo 50 6/128GB",
        "slug": "realme-narzo-50",
        "brand": "realme",
        "category": "Smartphone",
        "image": "de46d.png",
        "price": 1899000,
        "original_price": 2499000,
        "stock": 21,
        "specs": "Helio G96 · Layar 120Hz · Pengisian cepat 33W",
        "description": "Performa lebih, harga tetap pas. realme Narzo 50 dirancang untuk gaming dan aktivitas sehari-hari, dengan layar 120Hz yang mulus serta baterai besar untuk keseruan lebih lama.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 6
    },
    {
        "id": "prod-8",
        "name": "Xiaomi Redmi Note 12 8/128GB",
        "slug": "xiaomi-redmi-note-12",
        "brand": "Xiaomi",
        "category": "Smartphone",
        "image": "b862f.png",
        "price": 2399000,
        "original_price": 2899000,
        "stock": 17,
        "specs": "AMOLED 120Hz · RAM 8GB · Kamera utama 50MP",
        "description": "Warna hidup di setiap layar. Redmi Note 12 menawarkan pengalaman visual AMOLED, performa responsif, dan kamera yang siap mengabadikan hari-harimu. Dilengkapi baterai 5.000 mAh dan pengisian cepat.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 7
    },
    {
        "id": "prod-9",
        "name": "Sony PlayStation 5 Disc Edition",
        "slug": "sony-playstation-5",
        "brand": "Sony",
        "category": "Gaming",
        "image": "e6f97.png",
        "price": 7499000,
        "original_price": 8299000,
        "stock": 9,
        "specs": "SSD 825GB · Kontroler DualSense · Disc Edition",
        "description": "Masuki dunia permainan generasi baru. PlayStation 5 menghadirkan pengalaman gaming imersif, waktu muat cepat, dan sensasi kontroler DualSense. Paket mencakup konsol serta satu kontroler.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 8
    },
    {
        "id": "prod-10",
        "name": "Xbox Wireless Controller — Black",
        "slug": "xbox-wireless-controller",
        "brand": "Microsoft",
        "category": "Aksesori",
        "image": "dd62b.png",
        "price": 799000,
        "original_price": 999000,
        "stock": 25,
        "specs": "Wireless · Kompatibel Xbox & PC · Ergonomis",
        "description": "Kontrol presisi untuk permainan favoritmu. Kontroler wireless berdesain ergonomis dengan grip nyaman, D-pad responsif, dan konektivitas praktis untuk konsol maupun PC.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 9
    },
    {
        "id": "prod-11",
        "name": "DJI Phantom 4 Camera Drone",
        "slug": "dji-phantom-4",
        "brand": "DJI",
        "category": "Kamera",
        "image": "9596c.png",
        "price": 18999000,
        "original_price": 20999000,
        "stock": 4,
        "specs": "Video 4K · Gimbal stabil · Kontrol jarak jauh",
        "description": "Sudut pandang baru untuk kreativitasmu. DJI Phantom menghadirkan perekaman udara stabil dan kontrol intuitif. Gunakan sesuai peraturan penerbangan drone yang berlaku di wilayahmu.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 10
    },
    {
        "id": "prod-12",
        "name": "Smart Indoor Camera 1080p",
        "slug": "smart-indoor-camera",
        "brand": "Gadgetin",
        "category": "Kamera",
        "image": "9d954.png",
        "price": 349000,
        "original_price": 499000,
        "stock": 38,
        "specs": "Full HD 1080p · Wi-Fi · Pemantauan melalui aplikasi",
        "description": "Tetap terhubung dengan rumahmu. Kamera indoor pintar dengan video Full HD, pandangan malam, dan audio dua arah. Membutuhkan jaringan Wi-Fi dan aplikasi yang kompatibel.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 11
    }
]

CATEGORIES = ["Smartphone", "Laptop", "Smartwatch", "Audio", "Gaming", "Kamera", "Aksesori"]

# 1. Beranda / Home
@app.route("/")
def index():
    deals = [p for p in PRODUCTS if p.get("flash_sale")][:4]
    featured = [p for p in PRODUCTS if p.get("featured")][:8]
    return render_template(
        "index.html",
        deals=deals,
        featured=featured,
        active_page="beranda"
    )

# 2. Katalog Produk
@app.route("/katalog")
@app.route("/products")
def products():
    category = request.args.get("kategori", "").strip()
    brand = request.args.get("brand", "").strip()
    query = request.args.get("q", "").strip().lower()
    promo = request.args.get("promo", "") == "1"

    filtered = PRODUCTS
    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    if brand:
        filtered = [p for p in filtered if p["brand"].lower() == brand.lower()]
    if promo:
        filtered = [p for p in filtered if p.get("flash_sale")]
    if query:
        filtered = [
            p for p in filtered
            if query in p["name"].lower()
            or query in p["brand"].lower()
            or query in p["category"].lower()
        ]

    brands = sorted(list(set(p["brand"] for p in PRODUCTS)))

    return render_template(
        "products.html",
        products=filtered,
        brands=brands,
        total_count=len(PRODUCTS),
        active_category=category,
        active_brand=brand,
        is_promo=promo,
        query=query,
        active_page="katalog"
    )

# 3. Detail Produk
@app.route("/produk/<slug>")
def product_detail(slug):
    product = next((p for p in PRODUCTS if p["slug"] == slug), None)
    if not product:
        abort(404)

    related = [p for p in PRODUCTS if p["id"] != product["id"]]
    related.sort(key=lambda p: p["category"] == product["category"], reverse=True)

    return render_template(
        "product_detail.html",
        product=product,
        related=related,
        active_page="katalog"
    )

# 4. Keranjang Belanja
@app.route("/keranjang")
@app.route("/cart")
def cart():
    return render_template("cart.html", active_page="keranjang")

# 5. Checkout
@app.route("/checkout")
def checkout():
    return render_template("checkout.html", active_page="checkout")

# 6. Produk Favorit
@app.route("/favorit")
@app.route("/favorites")
def favorites():
    return render_template("favorites.html", active_page="favorit")

# 7. Masuk (Login)
@app.route("/masuk")
@app.route("/login")
def login():
    return render_template("login.html", active_page="masuk")

# 8. Daftar (Register)
@app.route("/daftar")
@app.route("/register")
def register():
    return render_template("register.html", active_page="daftar")

# 9. Akun Saya
@app.route("/akun")
@app.route("/account")
def account():
    return render_template("account.html", active_page="akun")

# 10. Pusat Bantuan & FAQ
@app.route("/bantuan")
@app.route("/help")
def help():
    return render_template("help.html", active_page="bantuan")

# 11. Dashboard Toko (Preview)
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", products=PRODUCTS, active_page="dashboard")

# Error 404 Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Error 500 Handler
@app.errorhandler(500)
def server_error(e):
    return render_template("error.html"), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

