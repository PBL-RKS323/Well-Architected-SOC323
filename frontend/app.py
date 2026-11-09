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
        "name": "Samsung Galaxy S24 Ultra 12/256GB",
        "slug": "samsung-galaxy-s24-ultra",
        "brand": "Samsung",
        "category": "Smartphone",
        "image": "s24-ultra.png",
        "price": 18999000,
        "original_price": 21999000,
        "stock": 15,
        "specs": "Snapdragon 8 Gen 3 · Kamera 200MP · S Pen",
        "description": "Era baru kecerdasan mobile. Galaxy S24 Ultra menghadirkan bodi titanium, kamera resolusi tinggi dengan ProVisual engine, dan layar Dynamic AMOLED 2X yang sangat cerah.",
        "flash_sale": True,
        "flash_sale_ends_at": "2026-10-31T23:59:59",
        "featured": True,
        "sort_order": 5
    },
    {
        "id": "prod-7",
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "slug": "sony-wh-1000xm5",
        "brand": "Sony",
        "category": "Audio",
        "image": "sony-xm5.png",
        "price": 4999000,
        "original_price": 5999000,
        "stock": 20,
        "specs": "Active Noise Cancelling · 30 Jam Baterai · LDAC",
        "description": "Ketenangan murni dalam setiap nada. Headphone noise-cancelling terdepan di industri dengan dua prosesor dan delapan mikrofon untuk kualitas suara tanpa kompromi.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 6
    },
    {
        "id": "prod-8",
        "name": "Apple Watch Series 10 GPS 46mm",
        "slug": "apple-watch-series-10",
        "brand": "Apple",
        "category": "Smartwatch",
        "image": "apple-watch-10.png",
        "price": 7499000,
        "original_price": 7999000,
        "stock": 10,
        "specs": "Layar OLED Wide-Angle · Sensor EKG · Tahan Air 50m",
        "description": "Desain tertipis dengan layar terluas yang pernah ada di Apple Watch. Dilengkapi fitur kesehatan mutakhir seperti deteksi sleep apnea dan sensor suhu air.",
        "flash_sale": False,
        "flash_sale_ends_at": None,
        "featured": True,
        "sort_order": 7
    }
]

# Helper to find product by slug or id
def get_product(slug_or_id):
    for p in PRODUCTS:
        if p["slug"] == slug_or_id or p["id"] == slug_or_id:
            return p
    return None

# Context processor: inject common variables
@app.context_processor
def inject_globals():
    return {
        "categories": ["Semua", "Smartphone", "Laptop", "Smartwatch", "Audio"],
        "brands": ["Semua", "Apple", "Samsung", "Xiaomi", "POCO", "Sony", "Beats", "Amazfit"]
    }

# 1. Beranda (Landing Page)
@app.route("/")
def index():
    flash_sale_products = [p for p in PRODUCTS if p["flash_sale"]]
    featured_products = [p for p in PRODUCTS if p["featured"]]
    categories = [
        {"name": "Smartphone", "icon": "smartphone", "count": 18},
        {"name": "Laptop", "icon": "laptop", "count": 12},
        {"name": "Audio", "icon": "headphones", "count": 15},
        {"name": "Smartwatch", "icon": "watch", "count": 9},
        {"name": "Aksesoris", "icon": "cable", "count": 24}
    ]
    return render_template(
        "index.html",
        flash_sale_products=flash_sale_products,
        featured_products=featured_products,
        categories=categories,
        active_page="beranda"
    )

# 2. Katalog / Jelajah Produk
@app.route("/produk")
@app.route("/products")
def products():
    category = request.args.get("kategori", "Semua")
    brand = request.args.get("merek", "Semua")
    q = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "default")
    
    filtered = PRODUCTS.copy()
    
    if category and category != "Semua":
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    if brand and brand != "Semua":
        filtered = [p for p in filtered if p["brand"].lower() == brand.lower()]
    if q:
        filtered = [p for p in filtered if q in p["name"].lower() or q in p["description"].lower()]
        
    if sort == "price_asc":
        filtered.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        filtered.sort(key=lambda x: x["price"], reverse=True)
    elif sort == "newest":
        filtered.sort(key=lambda x: x["sort_order"], reverse=True)
        
    return render_template(
        "products.html",
        products=filtered,
        selected_category=category,
        selected_brand=brand,
        search_query=q,
        current_sort=sort,
        active_page="produk"
    )

# 3. Detail Produk
@app.route("/produk/<slug_or_id>")
def product_detail(slug_or_id):
    product = get_product(slug_or_id)
    if not product:
        abort(404)
    related = [p for p in PRODUCTS if p["category"] == product["category"] and p["id"] != product["id"]][:4]
    return render_template(
        "product_detail.html",
        product=product,
        related_products=related,
        active_page="produk"
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
    host = os.environ.get("HOST", "127.0.0.1")
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug_mode)
