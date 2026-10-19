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

// Carousel beranda: geser manual (jari / tombol panah / titik) dan putar otomatis tiap 5 detik.
// Putar otomatis berhenti sementara saat kursor/fokus keyboard ada di carousel atau tab tidak terlihat,
// dan bisa dijeda lewat tombol. Jika pengguna memilih "kurangi gerakan", slide berganti tanpa animasi geser.
const JEDA_CAROUSEL_MS = 5000;
document.querySelectorAll("[data-carousel]").forEach(function (carousel) {
    const track = carousel.querySelector("[data-carousel-track]");
    const dots = carousel.querySelectorAll("[data-carousel-dot]");
    const kurangiGerak = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const halus = kurangiGerak ? "auto" : "smooth";
    const posisi = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    const ke = function (i) {
        const jumlah = track.children.length;
        track.scrollTo({ left: ((i + jumlah) % jumlah) * track.clientWidth, behavior: halus });
    };

    const tombolJeda = carousel.querySelector("[data-carousel-jeda]");
    let dijeda = false;           // dijeda pengguna lewat tombol
    let dihover = false;          // sementara: kursor ada di atas carousel
    let difokus = false;          // sementara: fokus keyboard ada di dalam carousel
    let timer = null;
    const mulai = function () {
        clearInterval(timer);
        timer = null;
        if (!dijeda && !dihover && !difokus && track.children.length > 1) {
            timer = setInterval(function () { if (!document.hidden) { ke(posisi() + 1); } }, JEDA_CAROUSEL_MS);
        }
    };
    const tampilkanJeda = function () {
        if (!tombolJeda) { return; }
        tombolJeda.setAttribute("aria-label", dijeda ? "Putar otomatis" : "Jeda putar otomatis");
        tombolJeda.querySelector("[data-ikon-jeda]").classList.toggle("hidden", dijeda);
        tombolJeda.querySelector("[data-ikon-putar]").classList.toggle("hidden", !dijeda);
    };
    if (tombolJeda) {
        tombolJeda.addEventListener("click", function () { dijeda = !dijeda; tampilkanJeda(); mulai(); });
    }
    carousel.addEventListener("mouseenter", function () { dihover = true; mulai(); });
    carousel.addEventListener("mouseleave", function () { dihover = false; mulai(); });
    // Hanya fokus keyboard (Tab) yang menahan; klik mouse pada tombol tidak membuat carousel macet
    carousel.addEventListener("focusin", function (e) { difokus = e.target.matches(":focus-visible"); mulai(); });
    carousel.addEventListener("focusout", function (e) {
        if (!carousel.contains(e.relatedTarget)) { difokus = false; mulai(); }
    });
    track.addEventListener("touchend", mulai, { passive: true });  // setelah digeser jari, hitung ulang 5 detik

    const prev = carousel.querySelector("[data-carousel-prev]");
    const next = carousel.querySelector("[data-carousel-next]");
    if (prev) { prev.addEventListener("click", function () { ke(posisi() - 1); mulai(); }); }
    if (next) { next.addEventListener("click", function () { ke(posisi() + 1); mulai(); }); }
    dots.forEach(function (dot) {
        dot.addEventListener("click", function () { ke(parseInt(dot.dataset.carouselDot, 10)); mulai(); });
    });
    tampilkanJeda();
    mulai();
    track.addEventListener("scroll", function () {
        const aktif = posisi();
        dots.forEach(function (dot, i) {
            dot.querySelector("span").toggleAttribute("data-aktif", i === aktif);
        });
    }, { passive: true });
});
