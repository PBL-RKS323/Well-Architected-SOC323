// Script ditaruh di file terpisah (bukan inline) agar sesuai Content-Security-Policy.

// Konfirmasi sebelum submit form yang memiliki atribut data-confirm (mis. hapus produk).
document.addEventListener("submit", function (event) {
    const form = event.target;
    const message = form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
        event.preventDefault();
        return;
    }
    // Form penting (buat pesanan, unggah bukti) dikunci setelah dikirim agar tidak terkirim dua kali.
    // Server tetap menolak pengiriman ganda; ini hanya mencegah klik ganda yang tidak disengaja.
    if (form.hasAttribute("data-kirim-sekali")) {
        setTimeout(function () {
            form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (b) {
                b.disabled = true;
            });
        }, 0);
    }
});

// Tombol - / + untuk mengubah jumlah barang (tetap di antara batas min & max input).
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-qty-step]");
    if (!button) {
        return;
    }
    const input = button.closest("[data-qty]").querySelector('input[type="number"]');
    const min = parseInt(input.min || "1", 10);
    const max = parseInt(input.max || "99", 10);
    const next = (parseInt(input.value, 10) || min) + parseInt(button.dataset.qtyStep, 10);
    input.value = Math.min(max, Math.max(min, next));
});

// Tombol mata untuk menampilkan / menyembunyikan isi kolom kata sandi.
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-toggle-password]");
    if (!button) {
        return;
    }
    const input = button.parentElement.querySelector("input");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-label", show ? "Sembunyikan kata sandi" : "Tampilkan kata sandi");
    button.querySelector('[data-icon="show"]').classList.toggle("hidden", show);
    button.querySelector('[data-icon="hide"]').classList.toggle("hidden", !show);
});

// Konfirmasi untuk tombol tertentu di form yang punya beberapa tombol (mis. batalkan pesanan).
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-confirm-click]");
    if (button && !window.confirm(button.dataset.confirmClick)) {
        event.preventDefault();
    }
});

// Tombol salin (nomor pesanan / nomor rekening).
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-copy]");
    if (!button || !navigator.clipboard) {
        return;
    }
    navigator.clipboard.writeText(button.dataset.copy).then(function () {
        const label = button.querySelector("[data-copy-label]");
        if (label) {
            const awal = label.textContent;
            label.textContent = "Tersalin";
            setTimeout(function () { label.textContent = awal; }, 1500);
        }
    });
});

// Checkout: tampilkan form alamat / info toko dan ongkir sesuai metode pengiriman yang dipilih.
// Total di layar hanya informasi; harga final tetap dihitung ulang di server.
document.addEventListener("change", function (event) {
    if (event.target.name !== "metode_pengiriman") {
        return;
    }
    const metode = event.target.value;
    document.querySelectorAll("[data-show-for]").forEach(function (el) {
        el.classList.toggle("hidden", el.dataset.showFor !== metode);
    });
    document.querySelectorAll("[data-kurir][data-ambil]").forEach(function (el) {
        el.textContent = el.dataset[metode];
    });
});

// Carousel beranda: geser manual (jari / tombol panah / titik). Tidak berganti otomatis.
document.querySelectorAll("[data-carousel]").forEach(function (carousel) {
    const track = carousel.querySelector("[data-carousel-track]");
    const dots = carousel.querySelectorAll("[data-carousel-dot]");
    const halus = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
    const posisi = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    const ke = function (i) {
        const jumlah = track.children.length;
        track.scrollTo({ left: ((i + jumlah) % jumlah) * track.clientWidth, behavior: halus });
    };
    const prev = carousel.querySelector("[data-carousel-prev]");
    const next = carousel.querySelector("[data-carousel-next]");
    if (prev) { prev.addEventListener("click", function () { ke(posisi() - 1); }); }
    if (next) { next.addEventListener("click", function () { ke(posisi() + 1); }); }
    dots.forEach(function (dot) {
        dot.addEventListener("click", function () { ke(parseInt(dot.dataset.carouselDot, 10)); });
    });
    track.addEventListener("scroll", function () {
        const aktif = posisi();
        dots.forEach(function (dot, i) {
            dot.querySelector("span").toggleAttribute("data-aktif", i === aktif);
        });
    }, { passive: true });
});
