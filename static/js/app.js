// Script ditaruh di file terpisah (bukan inline) agar sesuai Content-Security-Policy.

// Konfirmasi sebelum submit form yang memiliki atribut data-confirm (mis. hapus produk).
document.addEventListener("submit", function (event) {
    const message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
        event.preventDefault();
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
