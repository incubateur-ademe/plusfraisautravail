# plusfraisautravail

Monorepo for the [plusfraisautravail.beta.gouv.fr](https://plusfraisautravail.beta.gouv.fr) ecosystem — a self-assessment tool for employers to evaluate worksite adaptation to heat waves.

## Layout

```
.
├── apps/
│   ├── autodiag/         # Self-assessment SPA (Vite + React + react-dsfr)
│   └── alert-widget/     # Embeddable canicule alert widget
├── api/                  # FastAPI gateway aggregating alert sources (meteole/Vigilance)
├── packages/
│   └── api-client/       # Shared TS client for the API
├── infra/                # OpenTofu (Scaleway: buckets + serverless containers)
├── scripts/              # Ad-hoc scripts
├── sources/              # Raw source material, exploration notebooks
└── .github/workflows/    # CI + per-app deploy workflows
```

## Stack

- **Frontends:** npm workspaces, Vite, React 19, TypeScript, [`@codegouvfr/react-dsfr`](https://github.com/codegouvfr/react-dsfr).
- **API:** Python 3.12, [`uv`](https://docs.astral.sh/uv/), FastAPI, [`meteole`](https://pypi.org/project/meteole/).
- **Infra:** OpenTofu → Scaleway (Object Storage website buckets, Serverless Containers, Container Registry). State on Scaleway Object Storage (S3-compatible backend).
- **CI/CD:** GitHub Actions, path-filtered per app.

## Development

### Prerequisites
- Node 22+
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)

### Frontends
```bash
npm install
npm run dev:autodiag        # http://localhost:5173/autodiag/
npm run dev:alert-widget    # http://localhost:5173/alert-widget/  (proxies /api → :8080)
```

### API
```bash
cd api
cp .env.example .env  # set VIGILANCE_APP_ID
uv sync --extra dev
uv run uvicorn pfat_api.main:app --reload --port 8080
```
OpenAPI: http://localhost:8080/docs

### Tests / lint
```bash
npm run build           # builds all workspaces
cd api && uv run pytest && uv run ruff check .
```

## Deployment model

- **autodiag** — currently GitHub Pages (transitional). Will move to Scaleway bucket once `infra/envs/prod` is applied (see task in `.github/workflows/deploy-autodiag.yml`).
- **alert-widget** — Scaleway website bucket, deployed by `deploy-alert-widget.yml` on push to `main`.
- **api** — Built and pushed to Scaleway Container Registry, then the Serverless Container is redeployed by `deploy-api.yml`.
- **infra** — `tofu plan` runs in CI on PRs touching `infra/**`. `tofu apply` is run manually from a developer's machine.

## GitHub secrets / variables required

**Secrets:**
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`
- `VIGILANCE_APP_ID`

**Variables:**
- `API_BASE_URL` — public URL of the deployed API (used at frontend build time)
- `SCW_API_CONTAINER_ID` — Scaleway container ID, output of `tofu apply`

## Sources / data

The Météo-France Vigilance API ([`meteole`](https://pypi.org/project/meteole/)) returns per-département color codes (1=vert, 2=jaune, 3=orange, 4=rouge) per phenomenon. The API gateway focuses on phenomenon `8` (canicule).
