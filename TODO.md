# TODO

Outstanding work after the monorepo restructuring.

## Bootstrap (one-time, blocking everything else)

- [ ] Create Météo-France Vigilance application ID (if not already done) — store as `VIGILANCE_APP_ID` in:
  - local `api/.env`
  - GitHub repo secrets
  - `infra/envs/prod/terraform.tfvars` (`vigilance_app_id`)
- [ ] Create Scaleway API key with project + container + object-storage scopes
- [ ] Add GitHub secrets:
  - `SCW_ACCESS_KEY`
  - `SCW_SECRET_KEY`
  - `SCW_DEFAULT_PROJECT_ID`
  - `SCW_DEFAULT_ORGANIZATION_ID`
  - `VIGILANCE_APP_ID`
- [ ] Create the Terraform state bucket manually (Terraform can't manage its own state):
  ```bash
  aws --endpoint-url=https://s3.fr-par.scw.cloud s3 mb s3://pfat-tfstate --region fr-par
  ```

## First Terraform apply (two-step)

- [ ] `cd infra/envs/prod && cp terraform.tfvars.example terraform.tfvars` and fill it in
- [ ] `terraform init`
- [ ] `terraform apply` with `api_deploy = false` — creates buckets + registry namespace, no container yet
- [ ] First API image push (run `deploy-api.yml` manually via `workflow_dispatch`, or push locally:
  `docker build -t rg.fr-par.scw.cloud/pfat-prod/api:bootstrap api/ && docker push ...`)
- [ ] Update `terraform.tfvars`: set `api_image` to the pushed reference, `api_deploy = true`
- [ ] `terraform apply` again — creates the container
- [ ] Capture the container ID from `terraform output` and store as GitHub variable `SCW_API_CONTAINER_ID`
- [ ] Capture the API URL and store as GitHub variable `API_BASE_URL`

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

## Autodiag migration (Task #10, deferred)

- [ ] After Scaleway bucket exists: rewrite `.github/workflows/deploy-autodiag.yml` to `aws s3 sync` instead of `actions/upload-pages-artifact` + `deploy-pages` (mirror `deploy-alert-widget.yml`)
- [ ] Remove `permissions: pages` block and `concurrency: pages` group
- [ ] Update `VITE_BASE_URL` from `/plusfraisautravail/` to `/`
- [ ] Update embed URLs in https://plusfraisautravail.beta.gouv.fr (Wagtail) to point at the new bucket
- [ ] Disable GitHub Pages on the repo

## Infra / Terraform

- [ ] Decide on custom domains (out of scope for v1, no CDN/HTTPS on bucket endpoints)
- [ ] When custom domains needed: switch from `static-site` to `static-site` + Edge Services (or front with Cloudflare)
- [ ] Move `apply` into CI with manual approval once the workflow stabilises
- [ ] Add a `staging` env if/when the team grows or pre-prod testing is needed

## Repo hygiene

- [ ] First push: ensure `.env`, `terraform.tfvars`, and `node_modules/` are not committed (already in `.gitignore`)
- [ ] Add a `LICENSE` file (likely AGPL or MIT — beta.gouv.fr convention)
- [ ] Add a `CONTRIBUTING.md` once external contributors are expected
- [ ] Consider adding pre-commit hooks (ruff, prettier, terraform fmt)

## Nice-to-haves

- [ ] Code-split autodiag's bundle (current warning: 812 kB embed) — recharts is the heavy hitter
- [ ] Add `/sources` UI to the alert-widget showing last refresh time
- [ ] Add more sources to the API (BAAC, ozone, air quality?) — only when product asks for them
- [ ] Replace the in-process TTL cache with Redis if multi-instance deploys are needed
