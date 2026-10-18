// Konfirmasi sebelum submit form yang memiliki atribut data-confirm (mis. hapus produk).
// Ditaruh di file terpisah (bukan onsubmit inline) agar sesuai Content-Security-Policy.
document.addEventListener("submit", function (event) {
    const message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});
