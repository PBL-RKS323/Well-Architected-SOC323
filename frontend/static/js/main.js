/**
 * Gadgetin - Main JavaScript
 * Vanilla JS store state (Cart, Favorites, User) and UI interactions
 */

// Helper: Format number to Indonesian Rupiah
function rupiah(value) {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);
}

// Store Keys
const CART_KEY = "gadgetin_cart";
const FAV_KEY = "gadgetin_favorites";
const USER_KEY = "gadgetin_user";

// State Helpers
function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateBadges();
  document.dispatchEvent(new CustomEvent("gadgetin:cart-updated", { detail: cart }));
}

function getFavorites() {
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY)) || [];
  } catch (e) {
    return [];
  }
}

function saveFavorites(favs) {
  localStorage.setItem(FAV_KEY, JSON.stringify(favs));
  updateBadges();
  document.dispatchEvent(new CustomEvent("gadgetin:fav-updated", { detail: favs }));
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY)) || null;
  } catch (e) {
    return null;
  }
}

function saveUser(user) {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
  document.dispatchEvent(new CustomEvent("gadgetin:user-updated", { detail: user }));
}

// Toast Notifications
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className =
    "pointer-events-auto flex items-center gap-3 rounded-xl bg-ink px-4 py-3.5 text-sm text-white shadow-xl animate-toast border border-white/10";

  let iconHtml = '<i data-lucide="check-circle-2" class="size-5 shrink-0 text-brand"></i>';
  if (type === "fav") {
    iconHtml = '<i data-lucide="heart" class="size-5 shrink-0 text-red-500 fill-red-500"></i>';
  } else if (type === "cart") {
    iconHtml = '<i data-lucide="shopping-bag" class="size-5 shrink-0 text-brand"></i>';
  }

  toast.innerHTML = `
    ${iconHtml}
    <p class="font-medium text-xs sm:text-sm leading-tight">${message}</p>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons({ root: toast });

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

// Cart Actions
function addToCart(product, quantity = 1) {
  const cart = getCart();
  const existingIndex = cart.findIndex((item) => item.product.id === product.id);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({ product, quantity });
  }

  saveCart(cart);
  showToast(`"${product.name}" ditambahkan ke keranjang`, "cart");
}

function updateCartQuantity(productId, quantity) {
  let cart = getCart();
  if (quantity <= 0) {
    cart = cart.filter((item) => item.product.id !== productId);
  } else {
    const item = cart.find((item) => item.product.id === productId);
    if (item) {
      item.quantity = quantity;
    }
  }
  saveCart(cart);
}

function removeFromCart(productId) {
  let cart = getCart();
  cart = cart.filter((item) => item.product.id !== productId);
  saveCart(cart);
  showToast("Produk dihapus dari keranjang");
}

function clearCart() {
  saveCart([]);
}

// Favorites Actions
function toggleFavorite(product) {
  let favs = getFavorites();
  const index = favs.findIndex((item) => (typeof item === "object" ? item.id : item) === product.id);

  if (index > -1) {
    favs.splice(index, 1);
    saveFavorites(favs);
    showToast(`Dihapus dari produk favorit`);
    updateFavoriteButtons(product.id, false);
  } else {
    favs.push(product);
    saveFavorites(favs);
    showToast(`Disimpan ke produk favorit`, "fav");
    updateFavoriteButtons(product.id, true);
  }
}

function updateFavoriteButtons(productId, isFav) {
  document.querySelectorAll(`[data-fav-btn="${productId}"]`).forEach((btn) => {
    const icon = btn.querySelector("svg, i");
    if (isFav) {
      btn.classList.add("text-red-500");
      if (icon) {
        icon.classList.add("fill-red-500", "text-red-500");
      }
    } else {
      btn.classList.remove("text-red-500");
      if (icon) {
        icon.classList.remove("fill-red-500", "text-red-500");
      }
    }
  });
}

// Update Badges across Header
function updateBadges() {
  const cart = getCart();
  const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  document.querySelectorAll(".cart-badge-count").forEach((el) => {
    el.textContent = totalCount;
    el.style.display = totalCount > 0 ? "flex" : "none";
  });

  const favs = getFavorites();
  document.querySelectorAll(".fav-badge-count").forEach((el) => {
    el.textContent = favs.length;
    el.style.display = favs.length > 0 ? "flex" : "none";
  });

  // Sync heart buttons
  const favIds = favs.map((f) => (typeof f === "object" ? f.id : f));
  document.querySelectorAll("[data-fav-btn]").forEach((btn) => {
    const id = btn.getAttribute("data-fav-btn");
    const isFav = favIds.includes(id);
    const icon = btn.querySelector("svg, i");
    if (isFav) {
      btn.classList.add("text-red-500");
      if (icon) icon.classList.add("fill-red-500", "text-red-500");
    } else {
      btn.classList.remove("text-red-500");
      if (icon) icon.classList.remove("fill-red-500", "text-red-500");
    }
  });

  // User badge in header
  const user = getUser();
  const userText = document.getElementById("header-user-text");
  if (userText) {
    userText.textContent = user ? user.name.split(" ")[0] : "Masuk / Daftar";
  }
}

// Global DOM Content Loaded
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  updateBadges();

  // Menu Dropdown Toggle
  const menuBtn = document.getElementById("menu-toggle-btn");
  const menuDropdown = document.getElementById("menu-dropdown");
  if (menuBtn && menuDropdown) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      menuDropdown.classList.toggle("hidden");
    });

    document.addEventListener("click", (e) => {
      if (!menuDropdown.contains(e.target) && !menuBtn.contains(e.target)) {
        menuDropdown.classList.add("hidden");
      }
    });
  }

  // Header Search Form
  const headerSearchForm = document.getElementById("header-search-form");
  const headerSearchInput = document.getElementById("header-search-input");
  if (headerSearchForm && headerSearchInput) {
    headerSearchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = headerSearchInput.value.trim();
      if (q) {
        window.location.href = `/katalog?q=${encodeURIComponent(q)}`;
      } else {
        window.location.href = `/katalog`;
      }
    });
  }

  // Flash Sale Countdown Timer
  const countdownEl = document.getElementById("flash-sale-countdown");
  if (countdownEl) {
    let seconds = 24 * 3600 - 450;
    const updateTimer = () => {
      const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
      const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
      const s = String(seconds % 60).padStart(2, "0");
      countdownEl.innerHTML = `
        <span class="font-card font-semibold text-ink">${h}</span>
        <span class="text-muted">:</span>
        <span class="font-card font-semibold text-ink">${m}</span>
        <span class="text-muted">:</span>
        <span class="font-card font-semibold text-ink">${s}</span>
      `;
      if (seconds > 0) seconds--;
    };
    updateTimer();
    setInterval(updateTimer, 1000);
  }

  // Hero Slider
  const heroSlider = document.getElementById("hero-slider-section");
  if (heroSlider) {
    initHeroSlider();
  }

  // Mobile Filters Drawer in Catalog
  const mobileFilterBtn = document.getElementById("btn-mobile-filter");
  const filterSidebar = document.getElementById("filter-sidebar");
  if (mobileFilterBtn && filterSidebar) {
    mobileFilterBtn.addEventListener("click", () => {
      filterSidebar.classList.toggle("hidden");
      filterSidebar.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Product Detail Page Logic
  initProductDetailPage();

  // Cart & Checkout Page Logic
  initCartPage();
  initCheckoutPage();
});

// Hero Slider Implementation
function initHeroSlider() {
  const slides = [
    {
      label: "SMARTWATCH COLLECTION",
      eyebrow: "Teknologi yang mengikuti langkahmu.",
      title: "SMALL TECH.\nBIG POSSIBILITIES.",
      desc: "Smartwatch pilihan untuk hidup yang lebih terkoneksi.",
      category: "Smartwatch",
      image: "41a39.png",
      alt: "Smartwatch Amazfit",
    },
    {
      label: "SMARTPHONE COLLECTION",
      eyebrow: "Saatnya upgrade ke yang lebih baik.",
      title: "YOUR NEXT\nSMART MOVE.",
      desc: "Temukan smartphone andalan untuk setiap harimu.",
      category: "Smartphone",
      image: "a0332.png",
      alt: "iPhone 14",
    },
    {
      label: "AUDIO COLLECTION",
      eyebrow: "Dengarkan setiap detailnya.",
      title: "GOOD SOUND.\nGREAT DAYS.",
      desc: "Audio favorit untuk musik, kerja, dan segalanya.",
      category: "Audio",
      image: "bc437.png",
      alt: "Beats Headphone",
    },
  ];

  let current = 0;
  const labelEl = document.getElementById("hero-label");
  const eyebrowEl = document.getElementById("hero-eyebrow");
  const titleEl = document.getElementById("hero-title");
  const descEl = document.getElementById("hero-desc");
  const linkEl = document.getElementById("hero-link");
  const imgEl = document.getElementById("hero-img");
  const dots = document.querySelectorAll(".hero-dot");

  function setSlide(index) {
    current = (index + slides.length) % slides.length;
    const slide = slides[current];

    if (labelEl) labelEl.textContent = slide.label;
    if (eyebrowEl) eyebrowEl.textContent = slide.eyebrow;
    if (titleEl) titleEl.innerText = slide.title;
    if (descEl) descEl.textContent = slide.desc;
    if (linkEl) linkEl.href = `/katalog?kategori=${slide.category}`;
    if (imgEl) {
      imgEl.src = `/static/images/${slide.image}`;
      imgEl.alt = slide.alt;
    }

    dots.forEach((dot, idx) => {
      if (idx === current) {
        dot.className = "hero-dot h-1.5 w-7 rounded-full bg-brand p-0 transition-all";
      } else {
        dot.className = "hero-dot size-1.5 rounded-full bg-white/35 p-0 transition-all";
      }
    });
  }

  const prevBtn = document.getElementById("hero-prev-btn");
  const nextBtn = document.getElementById("hero-next-btn");
  if (prevBtn) prevBtn.addEventListener("click", () => setSlide(current - 1));
  if (nextBtn) nextBtn.addEventListener("click", () => setSlide(current + 1));

  dots.forEach((dot, idx) => {
    dot.addEventListener("click", () => setSlide(idx));
  });

  setInterval(() => {
    setSlide(current + 1);
  }, 6000);
}

// Product Detail Page Logic
function initProductDetailPage() {
  const qtyMinus = document.getElementById("detail-qty-minus");
  const qtyPlus = document.getElementById("detail-qty-plus");
  const qtyInput = document.getElementById("detail-qty-val");
  const maxStock = parseInt(qtyInput?.getAttribute("data-max-stock") || "20", 10);

  if (qtyMinus && qtyPlus && qtyInput) {
    qtyMinus.addEventListener("click", () => {
      let val = parseInt(qtyInput.textContent || "1", 10);
      if (val > 1) {
        qtyInput.textContent = val - 1;
      }
    });

    qtyPlus.addEventListener("click", () => {
      let val = parseInt(qtyInput.textContent || "1", 10);
      if (val < maxStock) {
        qtyInput.textContent = val + 1;
      }
    });
  }

  // Tabs
  const tabBtns = document.querySelectorAll(".product-tab-btn");
  const tabContents = document.querySelectorAll(".product-tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");

      tabBtns.forEach((b) => {
        b.classList.remove("border-blue", "text-blue", "font-bold");
        b.classList.add("border-transparent", "text-muted");
      });
      btn.classList.add("border-blue", "text-blue", "font-bold");
      btn.classList.remove("border-transparent", "text-muted");

      tabContents.forEach((c) => {
        if (c.id === `tab-${target}`) {
          c.classList.remove("hidden");
        } else {
          c.classList.add("hidden");
        }
      });
    });
  });
}

// Cart Page Logic
function initCartPage() {
  const cartContainer = document.getElementById("cart-items-container");
  const emptyState = document.getElementById("cart-empty-state");
  const cartLayout = document.getElementById("cart-layout");
  const summarySubtotal = document.getElementById("cart-summary-subtotal");
  const summaryTotal = document.getElementById("cart-summary-total");
  const summaryCount = document.getElementById("cart-summary-count");

  if (!cartContainer || !cartLayout) return;

  function renderCart() {
    const cart = getCart();

    if (cart.length === 0) {
      if (emptyState) emptyState.classList.remove("hidden");
      cartLayout.classList.add("hidden");
      return;
    }

    if (emptyState) emptyState.classList.add("hidden");
    cartLayout.classList.remove("hidden");

    let subtotal = 0;
    let totalItems = 0;

    cartContainer.innerHTML = cart
      .map((item) => {
        const itemSubtotal = item.product.price * item.quantity;
        subtotal += itemSubtotal;
        totalItems += item.quantity;

        const imgUrl = item.product.image
          ? `/static/images/${item.product.image}`
          : "/static/images/a0332.png";

        return `
        <div class="grid grid-cols-12 items-center gap-3 border-t border-line p-4 first:border-t-0 sm:p-6" data-item-id="${item.product.id}">
          <a href="/produk/${item.product.slug}" class="col-span-3 sm:col-span-2">
            <div class="relative h-24 rounded-lg bg-surface p-2 flex items-center justify-center overflow-hidden">
              <img src="${imgUrl}" alt="${item.product.name}" class="h-full w-full object-contain" />
            </div>
          </a>
          <div class="col-span-8 sm:col-span-5">
            <p class="mb-1 text-xs text-muted">${item.product.brand}</p>
            <a href="/produk/${item.product.slug}" class="text-sm font-bold text-ink hover:text-blue line-clamp-2">
              ${item.product.name}
            </a>
            <p class="mt-2 text-sm text-blue font-bold">${rupiah(item.product.price)}</p>
          </div>
          <button type="button" onclick="removeFromCart('${item.product.id}'); initCartPage();" class="col-span-1 text-muted hover:text-red-600 sm:hidden flex justify-end">
            <i data-lucide="trash-2" class="size-4"></i>
          </button>
          <div class="col-span-8 flex items-center gap-2 sm:col-span-3">
            <div class="inline-flex items-center rounded-lg border border-line bg-white">
              <button type="button" onclick="updateCartQuantity('${item.product.id}', ${item.quantity - 1}); initCartPage();" class="p-2 text-muted hover:text-ink">
                <i data-lucide="minus" class="size-3.5"></i>
              </button>
              <span class="w-8 text-center text-sm font-semibold">${item.quantity}</span>
              <button type="button" onclick="updateCartQuantity('${item.product.id}', ${item.quantity + 1}); initCartPage();" class="p-2 text-muted hover:text-ink">
                <i data-lucide="plus" class="size-3.5"></i>
              </button>
            </div>
            <button type="button" onclick="removeFromCart('${item.product.id}'); initCartPage();" class="hidden sm:flex p-2 text-muted hover:text-red-600">
              <i data-lucide="trash-2" class="size-4"></i>
            </button>
          </div>
          <p class="col-span-4 text-right text-sm font-bold text-ink sm:col-span-2">
            ${rupiah(itemSubtotal)}
          </p>
        </div>
      `;
      })
      .join("");

    if (summarySubtotal) summarySubtotal.textContent = rupiah(subtotal);
    if (summaryTotal) summaryTotal.textContent = rupiah(subtotal);
    if (summaryCount) summaryCount.textContent = `(${totalItems} produk)`;

    if (window.lucide) lucide.createIcons({ root: cartContainer });
  }

  renderCart();
}

// Checkout Page Logic
function initCheckoutPage() {
  const checkoutItemsList = document.getElementById("checkout-items-list");
  const checkoutSubtotal = document.getElementById("checkout-summary-subtotal");
  const checkoutTotal = document.getElementById("checkout-summary-total");
  const checkoutCount = document.getElementById("checkout-summary-count");
  const checkoutForm = document.getElementById("checkout-order-form");
  const successModal = document.getElementById("checkout-success-view");
  const checkoutMainView = document.getElementById("checkout-main-view");

  if (!checkoutForm) return;

  const cart = getCart();

  if (checkoutItemsList && cart.length > 0) {
    let subtotal = 0;
    let totalItems = 0;

    checkoutItemsList.innerHTML = cart
      .map((item) => {
        subtotal += item.product.price * item.quantity;
        totalItems += item.quantity;
        const imgUrl = item.product.image
          ? `/static/images/${item.product.image}`
          : "/static/images/a0332.png";

        return `
        <div class="flex items-center gap-3">
          <div class="size-12 rounded-lg bg-surface p-1 shrink-0 flex items-center justify-center overflow-hidden">
            <img src="${imgUrl}" alt="${item.product.name}" class="h-full w-full object-contain" />
          </div>
          <div class="min-w-0 text-xs flex-1">
            <p class="line-clamp-1 font-semibold text-ink">${item.product.name}</p>
            <p class="mt-1 text-muted">${item.quantity} × ${rupiah(item.product.price)}</p>
          </div>
        </div>
      `;
      })
      .join("");

    if (checkoutSubtotal) checkoutSubtotal.textContent = rupiah(subtotal);
    if (checkoutTotal) checkoutTotal.textContent = rupiah(subtotal);
    if (checkoutCount) checkoutCount.textContent = `(${totalItems} produk)`;
  }

  checkoutForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const btnSubmit = document.getElementById("btn-submit-order");
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = `<span>Membuat pesanan...</span>`;
    }

    setTimeout(() => {
      const orderId = "GD-" + Math.random().toString(36).substring(2, 10).toUpperCase();
      const totalAmount = checkoutTotal ? checkoutTotal.textContent : "Rp 0";

      const orderNumberEl = document.getElementById("order-number-display");
      const orderTotalEl = document.getElementById("order-total-display");

      if (orderNumberEl) orderNumberEl.textContent = orderId;
      if (orderTotalEl) orderTotalEl.textContent = totalAmount;

      if (checkoutMainView) checkoutMainView.classList.add("hidden");
      if (successModal) successModal.classList.remove("hidden");

      clearCart();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, 800);
  });
}

