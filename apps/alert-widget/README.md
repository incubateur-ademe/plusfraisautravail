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
