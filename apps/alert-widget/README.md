# @pfat/alert-widget

Embeddable widget showing the current Météo-France heatwave vigilance for a user-selected department, with links to prevention measures.

## Dev

```bash
# from repo root
npm run dev:alert-widget
```

Opens http://localhost:5173/alert-widget/. Vite proxies `/api/*` to `http://localhost:8080` (the FastAPI gateway).

Set `VITE_API_BASE_URL` to override the API base URL at build time.

## Embed bundle

`npm run build` produces:

- `dist/index.html` and assets - standalone SPA, deployed to its own bucket.
- `dist/alert-widget-embed.js` - IIFE bundle exposing `window.PfatAlertWidget.mount(...)`.

### Manual mount

```html
<div id="alert-root"></div>
<script src="https://.../alert-widget-embed.js"></script>
<script>
  PfatAlertWidget.mount({
    target: '#alert-root',
    apiBaseUrl: 'https://api.plusfraisautravail.beta.gouv.fr',
    preventionUrl: 'https://...',
    leversUrl: 'https://...',
  });
</script>
```

### Auto mount (single script tag)

The widget will insert itself right after the existing `fr-notice` that follows `<header>` (or right after `<header>` if no notice is present). Drop this single tag in the page template:

```html
<script
  src="https://.../alert-widget-embed.js"
  data-auto
  data-api-base-url="https://api.plusfraisautravail.beta.gouv.fr"
  data-prevention-url="https://plusfraisautravail.beta.gouv.fr/reglementation/"
></script>
```

Or, if you prefer to call it from JS:

```html
<script src="https://.../alert-widget-embed.js"></script>
<script>
  PfatAlertWidget.autoMount({
    apiBaseUrl: 'https://api.plusfraisautravail.beta.gouv.fr',
  });
</script>
```
