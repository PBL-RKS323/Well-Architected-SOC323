// Script ditaruh di file terpisah (bukan inline) agar sesuai Content-Security-Policy.

// ---------------------------------------------------------------------------------------------
// VALIDASI SISI KLIEN (lapis 1)
// Form memakai atribut novalidate agar gelembung bawaan browser (bahasa Inggris, tampilan beda tiap
// browser) tidak muncul. Penggantinya fungsi di bawah: dijalankan sebelum form dikirim, membaca aturan
// dari atribut HTML yang dibuat WTForms (required, minlength, maxlength, min, max, type="email") dan
// atribut tambahan dari forms/*.py (data-pola, data-sama-dengan, data-maks-byte). Pesan tampil di bawah
// kolom dengan gaya yang sama dengan pesan dari server.
// Validasi server (WTForms di folder forms/) tetap berjalan sebagai lapis 2, karena validasi browser
// bisa dilewati (JavaScript dimatikan, request dikirim langsung lewat curl / Burp Suite).
// ---------------------------------------------------------------------------------------------
function pesanValidasi(input) {
    input.setCustomValidity("");
    const nilai = (input.value || "").trim();

    // Aturan tambahan yang tidak punya padanan atribut HTML standar
    if (nilai && input.dataset.pola) {
        const dicek = input.dataset.polaTanpaSpasi !== undefined ? nilai.replace(/[\s-]/g, "") : nilai;
        if (!new RegExp(input.dataset.pola).test(dicek)) {
            input.setCustomValidity(input.dataset.polaPesan || "Format tidak valid.");
        }
    }
    if (input.dataset.samaDengan) {
        const asal = input.form.elements.namedItem(input.dataset.samaDengan);
        if (asal && input.value && input.value !== asal.value) {
            input.setCustomValidity(input.dataset.samaPesan || "Isian tidak cocok.");
        }
    }
    if (input.type === "file" && input.dataset.maksByte && input.files.length) {
        if (input.files[0].size > parseInt(input.dataset.maksByte, 10)) {
            input.setCustomValidity("Ukuran file terlalu besar (maksimal 2 MB).");
        }
    }

    const v = input.validity;
    if (v.valid) {
        return "";
    }
    if (v.valueMissing) {
        if (input.type === "checkbox") { return "Bagian ini wajib dicentang."; }
        if (input.type === "radio") { return "Pilih salah satu."; }
        if (input.type === "file") { return "Pilih file terlebih dahulu."; }
        return "Kolom ini wajib diisi.";
    }
    if (v.customError) { return input.validationMessage; }
    if (v.typeMismatch) { return "Format email tidak valid."; }
    if (v.tooShort) { return "Minimal " + input.minLength + " karakter (sekarang " + input.value.length + ")."; }
    if (v.tooLong) { return "Maksimal " + input.maxLength + " karakter."; }
    if (v.badInput) { return "Harus berupa angka."; }
    if (v.rangeUnderflow) { return "Nilai minimal " + input.min + "."; }
    if (v.rangeOverflow) { return "Nilai maksimal " + input.max + "."; }
    return "Isian tidak valid.";
}

function tampilkanPesanKlien(input, pesan) {
    // Radio: satu pesan per grup, ditaruh di akhir kelompok pilihan
    const jangkar = input.type === "radio"
        ? (input.closest("label") || input).parentElement
        : (input.closest(".relative") || input.closest("label") || input);
    const lama = jangkar.parentElement.querySelector('[data-galat-klien="' + input.name + '"]');
    if (lama) { lama.remove(); }
    input.toggleAttribute("aria-invalid", Boolean(pesan));
    input.classList.toggle("border-coral", Boolean(pesan));
    if (!pesan) { return; }
    const span = document.createElement("span");
    span.className = "text-coral text-xs block mt-1.5";
    span.dataset.galatKlien = input.name;
    span.textContent = pesan;
    if (input.type === "radio") { jangkar.appendChild(span); } else { jangkar.after(span); }
}

function kolomYangDicek(form) {
    return Array.from(form.elements).filter(function (el) {
        return el.name && !el.disabled && el.willValidate && el.type !== "hidden"
            // Kolom di bagian yang disembunyikan (mis. alamat saat memilih "ambil di toko") tidak dicek
            && !el.closest(".hidden, [hidden]");
    });
}

function validasiForm(form) {
    let pertama = null;
    const sudah = new Set();
    kolomYangDicek(form).forEach(function (el) {
        if (el.type === "radio" && sudah.has(el.name)) { return; }
        sudah.add(el.name);
        const pesan = pesanValidasi(el);
        tampilkanPesanKlien(el, pesan);
        if (pesan && !pertama) { pertama = el; }
    });
    return pertama;
}

// Fase capture: berjalan sebelum listener submit lain (konfirmasi, kunci tombol kirim)
document.addEventListener("submit", function (event) {
    const form = event.target;
    if (event.submitter && event.submitter.formNoValidate) { return; }
    const salah = validasiForm(form);
    if (salah) {
        event.preventDefault();
        event.stopPropagation();
        salah.focus();
    }
}, true);

// Setelah pesan muncul, pesan diperbarui langsung saat pengguna memperbaiki isiannya
["input", "change"].forEach(function (jenis) {
    document.addEventListener(jenis, function (event) {
        const el = event.target;
        if (!el.form || !el.name) { return; }
        const ada = el.form.querySelector('[data-galat-klien="' + el.name + '"]');
        if (ada) { tampilkanPesanKlien(el, pesanValidasi(el)); }
        // Kolom konfirmasi ikut dicek ulang saat kata sandi aslinya diubah
        el.form.querySelectorAll('[data-sama-dengan="' + el.name + '"]').forEach(function (k) {
            if (el.form.querySelector('[data-galat-klien="' + k.name + '"]')) {
                tampilkanPesanKlien(k, pesanValidasi(k));
            }
        });
    });
});

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

// Carousel beranda: geser manual (jari / tombol panah / titik) dan putar otomatis tiap 3 detik.
// Berhenti hanya jika dijeda lewat tombol, saat pengguna keyboard sedang menekan Tab di dalam carousel,
// atau saat tab browser tidak terlihat. Klik panah/titik hanya mengulang hitungan 3 detik.
// Perpindahan slide dianimasikan sendiri (bukan scrollTo smooth) agar selalu terlihat bergeser,
// karena sebagian browser langsung melompat jika animasi sistem dimatikan.
const JEDA_CAROUSEL_MS = 3000;
const DURASI_GESER_MS = 600;
let pakaiKeyboard = false;  // true setelah tombol Tab ditekan, false lagi setelah klik/sentuh
document.addEventListener("keydown", function (e) { if (e.key === "Tab") { pakaiKeyboard = true; } });
document.addEventListener("pointerdown", function () { pakaiKeyboard = false; });
document.querySelectorAll("[data-carousel]").forEach(function (carousel) {
    const track = carousel.querySelector("[data-carousel-track]");
    const dots = carousel.querySelectorAll("[data-carousel-dot]");
    const posisi = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    let indeks = 0;       // slide tujuan (dipakai selama animasi, saat scrollLeft masih di tengah jalan)
    let animasi = null;   // id timer animasi yang sedang berjalan
    const hentikanAnimasi = function () {
        clearTimeout(animasi);
        animasi = null;
        track.style.scrollSnapType = "";
    };
    const ke = function (i) {
        const jumlah = track.children.length;
        indeks = (i + jumlah) % jumlah;
        const awal = track.scrollLeft;
        const jarak = indeks * track.clientWidth - awal;
        const mulaiPada = performance.now();
        clearTimeout(animasi);
        track.style.scrollSnapType = "none";  // snap dimatikan sementara agar tidak melawan animasi
        const langkah = function () {
            const p = Math.min((performance.now() - mulaiPada) / DURASI_GESER_MS, 1);
            const halus = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;  // ease-in-out
            track.scrollLeft = awal + jarak * halus;
            if (p < 1) {
                animasi = setTimeout(langkah, 16);  // +-60 langkah per detik
            } else {
                hentikanAnimasi();
            }
        };
        langkah();
    };

    const tombolJeda = carousel.querySelector("[data-carousel-jeda]");
    let dijeda = false;           // dijeda pengguna lewat tombol
    let difokus = false;          // sementara: fokus keyboard (Tab) ada di dalam carousel
    let timer = null;
    const mulai = function () {
        clearInterval(timer);
        timer = null;
        if (!dijeda && !difokus && track.children.length > 1) {
            timer = setInterval(function () { if (!document.hidden) { ke(indeks + 1); } }, JEDA_CAROUSEL_MS);
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
    // Hanya fokus dari Tab yang menahan; klik mouse pada tombol tidak membuat carousel berhenti
    carousel.addEventListener("focusin", function () { difokus = pakaiKeyboard; mulai(); });
    carousel.addEventListener("focusout", function (e) {
        if (!carousel.contains(e.relatedTarget)) { difokus = false; mulai(); }
    });
    track.addEventListener("touchstart", function () {  // jari menyentuh: animasi berhenti, geser manual ambil alih
        hentikanAnimasi();
    }, { passive: true });
    track.addEventListener("touchend", mulai, { passive: true });  // setelah digeser jari, hitung ulang 3 detik

    const prev = carousel.querySelector("[data-carousel-prev]");
    const next = carousel.querySelector("[data-carousel-next]");
    if (prev) { prev.addEventListener("click", function () { ke(indeks - 1); mulai(); }); }
    if (next) { next.addEventListener("click", function () { ke(indeks + 1); mulai(); }); }
    dots.forEach(function (dot) {
        dot.addEventListener("click", function () { ke(parseInt(dot.dataset.carouselDot, 10)); mulai(); });
    });
    tampilkanJeda();
    mulai();
    track.addEventListener("scroll", function () {
        const aktif = posisi();
        if (animasi === null) { indeks = aktif; }  // ikut posisi setelah digeser jari
        dots.forEach(function (dot, i) {
            dot.querySelector("span").toggleAttribute("data-aktif", i === aktif);
        });
    }, { passive: true });
});

// Tab informasi produk (Deskripsi / Spesifikasi / Pengiriman). Tanpa JavaScript semua panel tampil
// berurutan; di sini daftar tab dimunculkan dan hanya panel aktif yang terlihat. Pola keyboard ARIA:
// panah kiri/kanan pindah tab, Home/End ke tab pertama/terakhir.
document.querySelectorAll("[data-tabs]").forEach(function (wadah) {
    const daftar = wadah.querySelector("[data-tablist]");
    const tabs = Array.from(daftar.querySelectorAll('[role="tab"]'));
    const panels = tabs.map(function (tab) { return document.getElementById(tab.getAttribute("aria-controls")); });
    const pilih = function (i, fokus) {
        tabs.forEach(function (tab, j) {
            tab.setAttribute("aria-selected", String(i === j));
            tab.tabIndex = i === j ? 0 : -1;
            panels[j].hidden = i !== j;
        });
        if (fokus) { tabs[i].focus(); }
    };
    daftar.classList.replace("hidden", "flex");
    panels.forEach(function (panel) {
        panel.classList.remove("mt-8");
        panel.querySelector("[data-tab-judul]").classList.add("sr-only");
    });
    tabs.forEach(function (tab, i) {
        tab.addEventListener("click", function () { pilih(i, false); });
        tab.addEventListener("keydown", function (e) {
            const tujuan = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
            if (tujuan === undefined) { return; }
            e.preventDefault();
            pilih((tujuan + tabs.length) % tabs.length, true);
        });
    });
    pilih(0, false);
});
