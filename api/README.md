# pfat-api

FastAPI gateway aggregating alert sources for plusfraisautravail.beta.gouv.fr.

## Sources

- **Météo-France Vigilance** (via [`meteole`](https://pypi.org/project/meteole/)) - heatwave (phenomenon `8`).

## Endpoints

- `GET /health`
- `GET /alerts/heatwave` - nationwide snapshot (all departments).
- `GET /alerts/heatwave/{dept}` - single department (e.g. `75`, `2A`).
- `GET /sources` - source metadata.

## Local dev

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
cd api
cp .env.example .env  # then fill VIGILANCE_APP_ID
uv sync
uv run uvicorn pfat_api.main:app --reload --port 8080
```

Open http://localhost:8080/docs.

## Tests

```bash
uv run pytest
```

## Build container

```bash
docker build -t pfat-api .
docker run -p 8080:8080 --env-file .env pfat-api
```

## Deploy

The image is built and pushed by `.github/workflows/deploy-api.yml` to the Scaleway Container Registry, then the Scaleway Serverless Container is updated to the new image. Infra is provisioned by OpenTofu under `infra/`.
