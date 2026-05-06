# TODO

Outstanding work after the monorepo restructuring.

For the deployment bootstrap (one-time) see [`DEPLOY.md`](./DEPLOY.md). The
items below are ongoing engineering work, not setup.

## API

- [ ] Verify `/alerts/heatwave` against the real Vigilance API (currently only `/health` is tested)
- [ ] Add integration test that mocks `meteole.Vigilance` and exercises the cache + dept filter
- [ ] Decide cache TTL (default 1h — confirm vs Vigilance refresh cadence)
- [ ] Tighten CORS origins once the production frontend domains are known
- [ ] Add structured logging (JSON, request ID) before going live
- [ ] Add `/metrics` or similar if observability is needed

## Alert-widget

- [ ] Replace placeholder `#` links with real URLs:
  - `preventionUrl` — "mesures de préventions règlementaires"
  - `leversUrl` — "leviers à actionner pour anticiper les vagues de chaleur"
- [ ] Decide what the standalone SPA at `/alert-widget/` should look like vs. the embed bundle (currently identical)
- [ ] Add a small E2E test (Playwright) covering: select dept → see vigilance card
- [ ] Verify embed bundle works inside the actual host page (plusfraisautravail.beta.gouv.fr or other)

## Autodiag migration follow-ups

- [ ] Update embed URLs in https://plusfraisautravail.beta.gouv.fr (Wagtail) to point at the new bucket
- [ ] Disable GitHub Pages on the repo once the bucket is live

## Infra / OpenTofu

- [ ] Decide on custom domains (out of scope for v1, no CDN/HTTPS on bucket endpoints)
- [ ] When custom domains needed: switch from `static-site` to `static-site` + Edge Services (or front with Cloudflare)
- [ ] Move `apply` into CI with manual approval once the workflow stabilises
- [ ] Add a `staging` env if/when the team grows or pre-prod testing is needed

## Repo hygiene

- [ ] Add a `LICENSE` file (likely AGPL or MIT — beta.gouv.fr convention)
- [ ] Add a `CONTRIBUTING.md` once external contributors are expected
- [ ] Consider adding pre-commit hooks (ruff, prettier, `tofu fmt`)

## Nice-to-haves

- [ ] Code-split autodiag's bundle (current warning: 812 kB embed) — recharts is the heavy hitter
- [ ] Add `/sources` UI to the alert-widget showing last refresh time
- [ ] Add more sources to the API (BAAC, ozone, air quality?) — only when product asks for them
- [ ] Replace the in-process TTL cache with Redis if multi-instance deploys are needed
