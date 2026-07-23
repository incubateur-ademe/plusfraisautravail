# Deploying plusfraisautravail to Scaleway

Single source of truth for the bootstrap and the day-to-day deploy flow.

The stack is provisioned with [OpenTofu](https://opentofu.org/) (`infra/envs/prod/`) on Scaleway:

| Resource | Module | Created from |
|---|---|---|
| Bucket `pfat-tfstate` | none | manual `aws s3 mb` (state backend) |
| Bucket `pfat-autodiag` | `static-site` | `module.autodiag_site` |
| Bucket `pfat-alert-widget` | `static-site` | `module.alert_widget_site` |
| Bucket `pfat-climadiag` | `static-site` | `module.climadiag_site` |
| Bucket `pfat-cms-media` (private) | `object-bucket` | `module.cms_media` |
| Container Registry namespace `pfat` | none | `scaleway_registry_namespace.pfat` (shared by `api` and `cms`) |
| Container namespace `api-prod` | `serverless-container` | `module.api` |
| Container `api-prod` | `serverless-container` | `module.api` |
| Private Network `cms-prod` | `managed-postgres` | `module.cms_db` |
| RDB instance `cms-prod` | `managed-postgres` | `module.cms_db` |
| Container namespace `cms-prod` | `serverless-container` | `module.cms` |
| Container `cms-prod` | `serverless-container` | `module.cms` |

CI/CD lives under `.github/workflows/`:

- `ci.yml` - JS build + Python ruff + pytest (api and cms) on every PR/push.
- `terraform-plan.yml` - `tofu plan` on PRs touching `infra/**`.
- `deploy-api.yml` - Docker build, push to registry, `PATCH redeploy=true`.
- `deploy-cms.yml` - Docker build, push to registry, `PATCH redeploy=true` (same shape as `deploy-api.yml`).
- `deploy-autodiag.yml` - Vite build, `aws s3 sync` to the bucket.
- `deploy-alert-widget.yml` - Vite build, `aws s3 sync` to the bucket.
- `deploy-climadiag.yml` - Vite build (SPA + embed), `aws s3 sync` to the bucket.

---

## 1. Prerequisites

Install once on your workstation:

- Scaleway account with a project, plus an API key (Access key + Secret key) scoped for project, container, registry, object-storage, RDB, VPC and IAM.
- Météo-France [Vigilance API](https://portail-api.meteofrance.fr/) application ID.
- (optional) RTE Ecowatt OAuth2 client ID & secret. Without these the `/alerts/electricity` endpoint returns 503; everything else still works.
- (optional) PlusFraîcheMaVille Climadiag `X-AUTH-TOKEN`. Without it `/climadiag/search` returns 503; everything else still works.
- A Django `SECRET_KEY` for the CMS - generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
- [GitHub CLI](https://cli.github.com/) (`gh auth login`).
- [AWS CLI v2](https://docs.aws.amazon.com/cli/) - used as a Scaleway S3 client.
- [OpenTofu](https://opentofu.org/) 1.8+ (`tofu` CLI).
- Docker.
- [`just`](https://github.com/casey/just) (already used as the task runner here).

---

## 2. One-time bootstrap

Run these in order. Every step has a `just` recipe; the recipes that mutate state ask for confirmation.

### 2.1 Set Scaleway credentials in your shell

The same Scaleway access/secret key serves three roles: OpenTofu provider auth, S3 backend auth (via `AWS_*`), and Docker registry auth.

**fish:**

```fish
set -x SCW_ACCESS_KEY              SCWxxxxxxxxxxxxxxxxx
set -x SCW_SECRET_KEY              xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
set -x SCW_DEFAULT_PROJECT_ID      xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
set -x SCW_DEFAULT_ORGANIZATION_ID xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
set -x AWS_ACCESS_KEY_ID           $SCW_ACCESS_KEY
set -x AWS_SECRET_ACCESS_KEY       $SCW_SECRET_KEY
```

**bash / zsh:**

```bash
export SCW_ACCESS_KEY=SCWxxxxxxxxxxxxxxxxx
export SCW_SECRET_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export SCW_DEFAULT_PROJECT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export SCW_DEFAULT_ORGANIZATION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export AWS_ACCESS_KEY_ID="$SCW_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SCW_SECRET_KEY"
```

### 2.2 Create the OpenTofu state bucket

OpenTofu can't manage its own state bucket - bootstrap it once:

```bash
just bootstrap-state
```

### 2.3 Fill `terraform.tfvars`

```bash
just bootstrap-tfvars
```

Set at least `vigilance_app_id`. Set `rte_client_id` / `rte_client_secret` if you have them; leave empty to disable `/alerts/electricity`. Set `climadiag_api_token` if you have it; leave empty to disable `/climadiag/search`. Set `django_secret_key` for the CMS. Leave `api_image=""`/`api_deploy=false` and `cms_image=""`/`cms_deploy=false` for now.

### 2.4 Initialize OpenTofu

```bash
just tf-init
```

**Upgrading an existing deployment (registry namespace already exists from before `cms` was added):** run this once, before the first apply below, so the existing `pfat` registry namespace is relabeled in state instead of destroyed and recreated (which would orphan already-pushed `api` images):

```bash
cd infra/envs/prod
tofu state mv module.api.scaleway_registry_namespace.this scaleway_registry_namespace.pfat
```

Skip this on a fresh account with no prior state - there's nothing to migrate.

### 2.5 First apply (creates buckets, registry, Postgres, Private Network - no container deploy yet)

```bash
just tf-apply
```

This succeeds with `api_deploy=false`/`cms_deploy=false` because the registry must exist before any image can be pushed to it (chicken-and-egg). **The RDB instance takes several minutes to provision** - `scaleway_rdb_instance.this: Still creating... [4m0s elapsed]`-style output is expected, not a stuck apply.

### 2.6 First image push

```bash
just deploy-api-bootstrap
just deploy-cms-bootstrap
```

Builds `api/Dockerfile` / `apps/cms/Dockerfile`, logs into `rg.fr-par.scw.cloud` (username `nologin`, password = `$SCW_SECRET_KEY`), pushes `rg.fr-par.scw.cloud/pfat/api:bootstrap` and `rg.fr-par.scw.cloud/pfat/cms:bootstrap`. Each recipe prints the exact reference at the end.

### 2.7 Edit `terraform.tfvars` again

Set:

```hcl
api_image  = "rg.fr-par.scw.cloud/pfat/api:bootstrap"
api_deploy = true
cms_image  = "rg.fr-par.scw.cloud/pfat/cms:bootstrap"
cms_deploy = true
```

### 2.8 Second apply (creates the containers)

```bash
just tf-apply
```

After this, note the `cms_url` output and add it to `cms_extra_allowed_hosts` in `terraform.tfvars`, then apply once more - the container's own Scaleway domain can't be known before it's created, so Django's `ALLOWED_HOSTS` needs this one extra round-trip (same reason `api_image`/`api_deploy` needed two applies).

### 2.9 Capture outputs

```bash
just status
```

Note the `container_id`, `api_url`, `cms_container_id`, and `cms_url` outputs - you need them for the next step.

### 2.10 Set GitHub secrets and environments

Two recipes, both idempotent:

```bash
just bootstrap-secrets        # repo-level secrets (used only by terraform-plan.yml on PRs)
just bootstrap-environments   # creates api / cms / autodiag / alert-widget / climadiag envs + their secrets
```

`bootstrap-environments` reads `SCW_*`, `VIGILANCE_APP_ID`, `RTE_*`, `DJANGO_SECRET_KEY` from your shell and `api_url` / `container_id` / `cms_url` / `cms_container_id` / bucket URLs from `tofu output`. It creates each environment with a `branch=main` policy so only main-branch deploys can read those secrets.

**Why two scopes:** `terraform-plan.yml` runs on PRs from any branch; environment-scoped secrets aren't readable from non-main refs, so its credentials live at repo level. `deploy-*.yml` workflows live in their respective environments - the GitHub UI shows a deployment history per environment with a clickable URL.

You're done. The next push to `main` touching `api/**` will redeploy the API container; `apps/cms/**` will redeploy the CMS container; `apps/autodiag/**` and `apps/alert-widget/**` will sync to their buckets. The deploy progress is visible at:

```
https://github.com/incubateur-ademe/plusfraisautravail/deployments
```

---

## 3. Normal deploy flow

| Trigger | What happens |
|---|---|
| Push to `main` touching `api/**` | `deploy-api.yml` builds + pushes a new image, then `PATCH`es the container with `redeploy=true`. |
| Push to `main` touching `apps/cms/**` | `deploy-cms.yml` builds + pushes a new image, then `PATCH`es the container with `redeploy=true`. |
| Push to `main` touching `apps/autodiag/**` | `deploy-autodiag.yml` builds and `aws s3 sync`s to `pfat-autodiag`. |
| Push to `main` touching `apps/alert-widget/**` | `deploy-alert-widget.yml` builds and `aws s3 sync`s to `pfat-alert-widget`. |
| Push to `main` touching `apps/climadiag/**` | `deploy-climadiag.yml` builds (SPA + embed) and `aws s3 sync`s to `pfat-climadiag`. |
| PR touching `infra/**` | `terraform-plan.yml` posts a plan as a step summary. |
| Push to `main` touching `infra/**` | `terraform-apply.yml` runs `tofu apply` against prod. The deployment shows up in the `tofu-apply` GitHub Environment. |

Both containers have `registry_image` under `lifecycle { ignore_changes = [registry_image] }` so `tofu apply` won't fight the deploy workflows - image rollouts go through `deploy-api.yml`/`deploy-cms.yml`, infra changes go through Tofu, neither steps on the other.

Manual triggers from your machine:

```bash
just deploy-api
just deploy-cms
just deploy-autodiag
just deploy-alert-widget
just deploy-climadiag
just tf-apply          # local apply, still works as an escape hatch
just status            # current outputs + last-run timestamps
```

To roll out an infrastructure change: edit `infra/envs/prod/**`, open a PR, review the plan in CI, merge. CI handles the apply.

---

## 4. Frontend bucket layout

All SPAs are built with `VITE_BASE_URL=/` in CI so all asset URLs are root-relative. Buckets serve at the root, e.g.:

- `https://pfat-autodiag.s3-website.fr-par.scw.cloud/`
- `https://pfat-alert-widget.s3-website.fr-par.scw.cloud/`
- `https://pfat-climadiag.s3-website.fr-par.scw.cloud/`

The local dev server keeps the historical sub-path (`/autodiag/`, `/alert-widget/`, `/climadiag/`) - only the deployed bundles use root.

`deploy-climadiag.yml` builds both the standalone SPA (`index.html` + assets) **and** the single-file embed (`climadiag-embed.js`) into the same `dist/`, so both land in the bucket. To embed just the blue search widget on another page, drop:

```html
<script
  src="https://pfat-climadiag.s3-website.fr-par.scw.cloud/climadiag-embed.js"
  data-auto
  data-api-base-url="https://<api-prod-url>"
></script>
```

The script self-mounts right where it's placed in the DOM and injects the DSFR CSS from a CDN - no other markup or stylesheet needed on the host page.

---

## 5. Troubleshooting

**"image not found" on the first `tofu apply`.**
You forgot `api_deploy=false`/`cms_deploy=false` for the first pass. Set it, apply, then push the image with `just deploy-api-bootstrap`/`just deploy-cms-bootstrap`, then flip `*_deploy=true` and apply again.

**API returns 502.**
The container is up but the app crashed at boot. Check Scaleway dashboard -> Containers -> `api-prod` -> Logs (or `scw container container logs <id>` if you have the CLI). Most common cause: missing/wrong `VIGILANCE_APP_ID`. RTE is optional; if the creds are wrong only `/alerts/electricity` will 503.

**API returns 503 on `/alerts/electricity`.**
RTE creds are missing or wrong. Set `rte_client_id` / `rte_client_secret` in `terraform.tfvars` and re-apply, or set the corresponding GitHub secrets and re-run `terraform-plan.yml` for visibility (the actual variable injection happens at `tofu apply` time, locally).

**API returns 503 on `/climadiag/search`.**
`climadiag_api_token` is missing. Set it in `terraform.tfvars` and re-apply, or set the `CLIMADIAG_API_TOKEN` GitHub secret (repo-level and on the `tofu-apply` environment) and re-run the apply.

**CMS returns 502.**
Check Scaleway dashboard -> Containers -> `cms-prod` -> Logs. Most common causes: missing/wrong `DATABASE_URL` or `DJANGO_SECRET_KEY`, or the container can't reach Postgres over the Private Network (verify `module.cms` and `module.cms_db` ended up on the same `private_network_id` - check `tofu output cms_db_host` is a private `10.x`/`172.x` address, not a public one).

**CMS migrations don't seem to have run.**
`entrypoint.sh` runs `manage.py migrate --noinput` before starting gunicorn on every cold start - check the container logs for migration output/errors. If it's stuck on "Still creating" style output for Postgres, the RDB instance may still be provisioning (can take several minutes on first apply).

**CMS media uploads fail with 403.**
`pfat-cms-media` is a private bucket - check the `object-bucket` module's IAM policy and API key actually reached the container as `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (both are `secret_environment_variables`, so they won't show in `tofu output`; check the Scaleway container's env vars in the dashboard instead).

**GitHub Actions deploy fails on `aws s3 sync` or registry login.**
Check `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` repo secrets - all deploy workflows use the same credentials.

**`tofu apply` fails with "state lock".**
Someone else is mid-apply, or a previous run was killed. Identify the lock with `tofu plan` (it prints the lock ID) and release with:

```bash
cd infra/envs/prod
tofu force-unlock <LOCK_ID>
```

**`just status` prints "(tofu output failed)".**
Run `just tf-init` first, or check that you're authenticated with the right Scaleway project (`echo $SCW_DEFAULT_PROJECT_ID`).
