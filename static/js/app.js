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
