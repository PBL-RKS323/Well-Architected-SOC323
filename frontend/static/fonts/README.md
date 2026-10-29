# Static Fonts

Font pada template ini (Lato, Rubik, Public Sans, Inter, Poppins) dimuat secara otomatis melalui Google Fonts CDN di `static/css/style.css`.

Jika ingin menggunakan font lokal/offline, letakkan file `.woff2` atau `.ttf` di folder ini dan sesuaikan `@font-face` di `static/css/style.css` menggunakan format:

```css
@font-face {
  font-family: 'Lato';
  src: url('/static/fonts/Lato-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}
```

