# Deploying plusfraisautravail to Scaleway

Single source of truth for the bootstrap and the day-to-day deploy flow.

The stack is provisioned with [OpenTofu](https://opentofu.org/) (`infra/envs/prod/`) on Scaleway:

| Resource | Module | Created from |
|---|---|---|
| Bucket `pfat-terraform` | none | `just bootstrap-state` (state backend) |
| Secrets `pfat-prod-…` | none | by hand, Scaleway Secret Manager (2.3) |
| Buckets `pfat-autodiag`, `pfat-alert-widget`, `pfat-climadiag` | `static-site` | `module.site` |
| Bucket `pfat-cms-media` (private) | `object-bucket` | `module.cms_media` |
| Container Registry namespace `pfat` | none | `scaleway_registry_namespace.pfat` |
| Private Network `cms-prod` | `managed-postgres` | `module.cms_db` |
| RDB instance `cms-prod` | `managed-postgres` | `module.cms_db` |
| Container namespace `cms-prod` | `serverless-container` | `module.cms` |
| Container `cms-prod` | `serverless-container` | `module.cms` |
| Private containers `cms-manage-prod`, `e2e-dump-prod` | `serverless-container` | `module.cms_manage`, `module.e2e_dump` |
| Bucket `pfat-e2e-fixtures` (private) | `object-bucket` | `module.e2e_fixtures` |

CI/CD lives under `.github/workflows/`:

- `review.yml` (💣 Pull request) - on PRs, runs the checks of each product the PR touches (`.github/ci-areas.yml`). Require its `✅ CI` job.
- `cd.yml` (🚀 Production) - on `main`, runs the same checks and deploys each product it touches. Manual runs pick one product or all.
- `cms.yml` - ruff, pytest with coverage; on deploy, Docker build, push to registry, then the migrations: the image is rolled out on the private `cms-manage` container and `POST /run` runs `manage_jobs.sh`. Only then is the CMS container rolled out (`PATCH redeploy=true`): a failed migration fails the deploy and leaves the current CMS in place. Containers are found by name (`.github/scripts/scw-container.sh`).
- `frontend.yml` - ESLint and Vite build of one SPA; on deploy, `aws s3 sync` to its bucket.
- `infrastructure.yml` - `tofu plan`, shown on the run's summary page; on `main` (or a manual run), `tofu apply`.

---

## 1. Prerequisites

- Scaleway account with a project, plus an API key (access key + secret key) allowed on containers, registry, Object Storage, RDB, VPC and Secret Manager. For the secret, the IAM permission sets `SecretManagerReadOnly` (find it by name) and `SecretManagerSecretAccess` (read its value).
- The secrets of the third parties, each optional: Météo-France [Vigilance API](https://portail-api.meteofrance.fr/) application ID, RTE Ecowatt OAuth2 client ID and secret, PlusFraîcheMaVille Climadiag token, Notion token. Without one, the matching feature answers 503 or is off; everything else works.
- [GitHub CLI](https://cli.github.com/) (`gh auth login`), [AWS CLI v2](https://docs.aws.amazon.com/cli/) (S3 client), [Scaleway CLI](https://cli.scaleway.com/), [OpenTofu](https://opentofu.org/) 1.10+, Docker, [`just`](https://github.com/casey/just).

---

## 2. One-time bootstrap

Run these in order. The recipes that change something ask for confirmation.

**In another Scaleway project**, change these names first (bucket names are global, registry namespaces are unique per region):

| What | Where |
|---|---|
| State bucket `pfat-terraform` | `infra/envs/prod/backend.tf`, `bootstrap-state` in the `Justfile` |
| Bucket names `pfat-…`, registry namespace `pfat` | `infra/envs/prod/main.tf`; `REGISTRY_NAMESPACE` in `.github/workflows/cms.yml`, `BUCKET` in `frontend.yml`; `deploy-cms-bootstrap` in the `Justfile`; `src` in `e2e/restore.sh`; the default hosts of `infra/scalingo-proxy/servers.conf.erb` |
| Domain | `base_domain` in `infra/envs/prod/main.tf` |

### 2.1 Scaleway credentials in your shell

The same key serves OpenTofu, its S3 state backend (`AWS_*`) and the Docker registry.

```bash
export SCW_ACCESS_KEY=SCWxxxxxxxxxxxxxxxxx
export SCW_SECRET_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export SCW_DEFAULT_PROJECT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export SCW_DEFAULT_ORGANIZATION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export AWS_ACCESS_KEY_ID="$SCW_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SCW_SECRET_KEY"
```

### 2.2 State bucket

OpenTofu can't manage its own state bucket:

```bash
just bootstrap-state
```

### 2.3 The secrets: one Secret Manager secret each

Every hand-provided secret is one Scaleway Secret Manager secret, named `pfat-prod-<name>`, at the default path. OpenTofu reads the latest enabled version of each at every plan and passes it to the containers that need it. All ten must exist: a missing one fails the plan, naming it.

| Secret | What it is | Goes to | GitHub secret it replaces |
|---|---|---|---|
| `pfat-prod-vigilance-app-id` | Météo-France Vigilance application ID | cms | `VIGILANCE_APP_ID` |
| `pfat-prod-rte-client-id` | RTE Ecowatt OAuth2 client ID | cms | `RTE_CLIENT_ID` |
| `pfat-prod-rte-client-secret` | RTE Ecowatt OAuth2 client secret | cms | `RTE_CLIENT_SECRET` |
| `pfat-prod-climadiag-api-token` | PlusFraîcheMaVille Climadiag token | cms | `CLIMADIAG_API_TOKEN` |
| `pfat-prod-notion-token` | Notion integration token (contact form) | cms, cms-manage | `NOTION_TOKEN` |
| `pfat-prod-email-host-password` | Scaleway API secret key allowed to send with Transactional Email | cms, cms-manage | `EMAIL_HOST_PASSWORD`, or `S3_BUCKET_SCW_SECRET_KEY` if it was never set |
| `pfat-prod-cms-media-access-key-id` | Scaleway API access key for the media bucket | cms, cms-manage | `S3_BUCKET_SCW_ACCESS_KEY_ID` |
| `pfat-prod-cms-media-secret-key` | its secret key | cms, cms-manage | `S3_BUCKET_SCW_SECRET_KEY` |
| `pfat-prod-e2e-fixtures-access-key-id` | Scaleway API access key for the e2e fixtures bucket | e2e-dump | `S3_BUCKET_SCW_ACCESS_KEY_ID` |
| `pfat-prod-e2e-fixtures-secret-key` | its secret key | e2e-dump | `S3_BUCKET_SCW_SECRET_KEY` |

The media, fixtures and e-mail secrets may all hold the same Scaleway key today. They are separate so that each can later get its own key, restricted to its bucket or to e-mail, without touching the code.

The first six are optional credentials. All ten secrets must still exist: for one you do not have, store an empty value (a file holding only a newline). It is then not passed to the containers and its feature is off (503 on the matching API endpoint, no Notion sync, no outgoing mail). The four key secrets must not be empty: the plan fails, naming the empty one.

For each one, with the value in a file outside the repository (UTF-8 without BOM; a final newline is ignored):

```bash
scw secret version create "$(scw secret secret create name=pfat-prod-<name> -o json | jq -r .id)" data=@/path/to/value
rm /path/to/value
```

If a secret named `pfat-prod` is left from earlier trials, delete it: nothing reads it.

To change a secret later: create a new version (`scw secret version create <secret-id> data=@/path/to/value`), then apply (`just deploy infrastructure`, or any merge touching `infra/`). The Django `SECRET_KEY` and the database passwords are not secrets to create: OpenTofu generates them. To rotate the Django key, run 🏗️ Infrastructure by hand with `tofu_replace` = `random_password.django_secret_key`: every admin is logged out and pending signed links (password reset) stop working.

For these secrets, GitHub masks nothing in logs, as it does not know their values: only OpenTofu's `sensitive` marking hides them, in a plan that is public. Never wrap them in `nonsensitive()` or put them in an output.

### 2.4 Registry, first image, then everything else

Scaleway only creates a container whose image exists, so the registry and a first image come first:

```bash
just tf-init
cd infra/envs/prod && tofu apply -target=scaleway_registry_namespace.pfat && cd -
just deploy-cms-bootstrap   # builds and pushes rg.fr-par.scw.cloud/pfat/cms:latest
just tf-apply
```

**The RDB instance takes several minutes to provision.** From then on OpenTofu ignores the containers' image: the deploys roll images out.

### 2.5 GitHub secrets and environments

```bash
just bootstrap-secrets        # the 4 SCW_* repository secrets (plan on pull requests)
just bootstrap-environments   # cms / autodiag / alert-widget / climadiag / tofu-apply environments
```

GitHub only holds the Scaleway key: `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`, at repository level and in each environment (restricted to `main`). Not secret, as repository variables: `SENTRY_DSN`, `POSTHOG_KEY`, and `CMS_BASE_URL` while testing before a DNS cutover.

**On a repository set up before Secret Manager**, create the ten secrets (2.3) before merging. GitHub does not give a secret back: take the values from where they came from (Scaleway console, Météo-France, RTE, PlusFraîcheMaVille and Notion accounts). Give the Scaleway key of the CI the two Secret Manager permission sets (section 1). Until the first apply from CI is over, `just bastion-up` fails ("Moved resource instances excluded by targeting").

The first apply replaces the Django key by the generated one: every admin is logged out once, and pending signed links stop working. After that apply, the GitHub secrets of the table in 2.3 and `DJANGO_SECRET_KEY` are no longer read and can be deleted, at repository level and in the `tofu-apply` and `cms` environments.

The next push to `main` deploys what it touches. Progress: <https://github.com/incubateur-ademe/plusfraisautravail/deployments>.

---

## 3. Normal deploy flow

| Trigger | What happens |
|---|---|
| Push to `main` touching `apps/cms/**` or `packages/**` | 🚀 Production checks the CMS, builds + pushes a new image, then `PATCH`es the container with `redeploy=true`. |
| Push to `main` touching `apps/autodiag/**` | 🚀 Production lints, builds and `aws s3 sync`s to `pfat-autodiag`. |
| Push to `main` touching `apps/alert-widget/**` | 🚀 Production lints, builds and `aws s3 sync`s to `pfat-alert-widget`. |
| Push to `main` touching `apps/climadiag/**` | 🚀 Production lints, builds (SPA + embed) and `aws s3 sync`s to `pfat-climadiag`. |
| PR touching `infra/**` | 💣 Pull request runs `tofu plan`. |
| Push to `main` touching `infra/**` | 🚀 Production runs `tofu apply` against prod. The deployment shows up in the `tofu-apply` GitHub Environment. |

The containers have `image` under `lifecycle { ignore_changes = [image] }` so `tofu apply` won't fight the deploy workflow - image rollouts go through `cms.yml`, infra changes go through Tofu, neither steps on the other.

Manual triggers from your machine:

```bash
just deploy-cms
just deploy-autodiag
just deploy-alert-widget
just deploy-climadiag
just tf-apply          # local apply, an escape hatch: needs terraform.tfvars (see below)
just status            # current outputs + last-run timestamps
```

A local apply does not read the GitHub variables: without `infra/envs/prod/terraform.tfvars` (copy `terraform.tfvars.example`, fill `sentry_dsn` and `posthog_key`), it turns Sentry and PostHog off until the next apply from CI.

To roll out an infrastructure change: edit `infra/envs/prod/**`, open a PR, review the plan in CI, merge. CI handles the apply.

---

## 4. Frontend bucket layout

All SPAs are built with their default sub-path base (`/autodiag/`, `/alert-widget/`, `/climadiag/`) so they work behind the proxy's prefix routing. Bucket files sit at the bucket root; the proxy strips the prefix. Direct bucket URLs therefore no longer render the SPAs on their own:

- `https://pfat-autodiag.s3-website.fr-par.scw.cloud/`
- `https://pfat-alert-widget.s3-website.fr-par.scw.cloud/`
- `https://pfat-climadiag.s3-website.fr-par.scw.cloud/`

The local dev server keeps the historical sub-path (`/autodiag/`, `/alert-widget/`, `/climadiag/`) - only the deployed bundles use root.

The climadiag deploy builds both the standalone SPA (`index.html` + assets) **and** the single-file embed (`climadiag-embed.js`) into the same `dist/`, so both land in the bucket. To embed just the blue search widget on another page, drop:

```html
<script
  src="https://pfat-climadiag.s3-website.fr-par.scw.cloud/climadiag-embed.js"
  data-auto
  data-api-base-url="https://plusfraisautravail.beta.gouv.fr/api"
></script>
```

The script self-mounts right where it's placed in the DOM and injects the DSFR CSS from a CDN - no other markup or stylesheet needed on the host page.

---

## 5. Public hostname: Scalingo nginx proxy

`plusfraisautravail.beta.gouv.fr` carries MX records, so it can't be a CNAME to Scaleway. Instead a tiny Scalingo app running the [nginx buildpack](https://github.com/Scalingo/nginx-buildpack) keeps the existing A records + TLS cert and reverse-proxies to Scaleway. Config: `infra/scalingo-proxy/servers.conf.erb`.

| Path | Upstream | Cache |
|---|---|---|
| `/static/` | cms container | follows whitenoise headers (1y on hashed files) |
| `/media/` | `pfat-cms-media` bucket (public-read on `images/*` and `original_images/*`) | 1y, unsigned URLs via `AWS_S3_CUSTOM_DOMAIN` |
| `/media/documents/` | none (404) | documents are served by Django at `/documents/`, permission-checked, uncached |
| `/<spa>/assets/` | SPA bucket | 1y (Vite content-hashed) |
| `/<spa>/` | SPA bucket | 5m (from the bucket's own Cache-Control) |
| `/ph/` | PostHog EU (`eu.i.posthog.com`, assets from `eu-assets.i.posthog.com`) | none - the PostHog snippet in Wagtail's custom scripts uses `api_host: '/ph'` |
| `/api/` | cms container (Wagtail's `api/v2/` and the alert API of `packages/pfat-api`) | none |
| `/` | cms container | none |

Requests for `www.plusfraisautravail.beta.gouv.fr` and `plus-fraiche-ma-boite.sites.beta.gouv.fr` get a 301 to the canonical domain; both domains are attached to the proxy app.

The app is `plusfraisautravail-proxy` (osc-fr1). Its env already carries `BUILDPACK_URL`, `PROJECT_DIR=infra/scalingo-proxy`, `CMS_HOST` (the cms container's Scaleway hostname, from `tofu output cms_url`). `scalingo -a plusfraisautravail-proxy git-setup` adds the `scalingo` git remote, then:

```bash
git push scalingo main   # or link the GitHub repo in the Scalingo dashboard
```

The nginx buildpack needs no Procfile and no APT packages on the `scalingo-26` stack.

**Testing on the proxy hostname before cutover.** Absolute URLs (media, `image.full_url`, admin emails) are built from `WAGTAILADMIN_BASE_URL`, which defaults to the production domain. To test on `https://plusfraisautravail-proxy.osc-fr1.scalingo.io`, set the GitHub repo variable `CMS_BASE_URL` to that URL and re-run 🏗️ Infrastructure (`infrastructure.yml`); delete the variable and re-apply at cutover. The `canonical`/`og:url` tags come from the Wagtail Site record in the database and always name the production domain, which is correct.

The SPAs must be built with their default sub-path base (`/autodiag/` etc.), not `VITE_BASE_URL=/`, for the proxy's prefix routing to work. Wagtail pages must not use the slugs `static`, `media`, `api`, `autodiag`, `alert-widget` or `climadiag`.

`just proxy-check` renders the template and runs `nginx -t` on it.

---

## 6. Troubleshooting

**"image not found" on the first `tofu apply`.**
The containers are created with `pfat/cms:latest`: push it first (2.4).

**The plan fails on `data.scaleway_secret_version.app["…"]`.**
The secret `pfat-prod-…` named in the error does not exist, has no enabled version, or the Scaleway key cannot read Secret Manager (2.3). Nothing was changed. To go back to the previous value of a secret, disable its latest version and apply.

**Destroying the stack.**
Not a workflow: the database and its instance have `prevent_destroy` and the media bucket no `force_destroy`. Remove them in a pull request first, then `tofu destroy` locally.

**API returns 502 on `/api/alerts/meteo` or `/api/alerts/electricity`.**
The upstream (Météo-France or RTE) failed and no earlier snapshot is cached. Check the cms container logs (Scaleway dashboard -> Containers -> `cms-prod` -> Logs). Most common cause: a wrong `VIGILANCE_APP_ID`; a missing one answers 503.

**API returns 503 on `/api/alerts/electricity`.**
`pfat-prod-rte-client-id` or `pfat-prod-rte-client-secret` is empty (2.3). Wrong credentials answer 502 instead.

**API returns 503 on `/api/climadiag/search`.**
`pfat-prod-climadiag-api-token` is empty (2.3). A wrong token answers 502 instead.

**CMS returns 502.**
Check Scaleway dashboard -> Containers -> `cms-prod` -> Logs. Most common causes: missing/wrong `DATABASE_URL` or `DJANGO_SECRET_KEY`, or the container can't reach Postgres over the Private Network (verify `module.cms` and `module.cms_db` ended up on the same `private_network_id` - check `tofu output cms_db_host` is a private `10.x`/`172.x` address, not a public one).

**CMS migrations don't seem to have run.**
Migrations are *not* run on container cold start - `entrypoint.sh` only starts gunicorn, to stay within the container's startup probe budget (a slow migration there previously got the container killed as "failed to start" even when the migration itself succeeded). Each CMS deploy runs them in the private `cms-manage` container (same image, `manage_server.py`, `POST /run` runs `manage_jobs.sh`); its stdout is in the deploy job's log, its errors in the container logs (Cockpit): they can quote a row. To run them by hand: `curl -X POST "$(tofu output -raw cms_manage_url)/run" -H "X-Auth-Token: $SCW_SECRET_KEY"`.

**Reaching the database by hand.**
The database has no public endpoint: only its Private Network reaches it (the CMS, cms-manage and e2e-dump containers). For an admin session, `just bastion-up <your public IP>` (or `bastion_allowed_ip_ranges` in `terraform.tfvars`: only those addresses reach it) creates a Public Gateway with an SSH bastion on that network (SSH keys: those of the Scaleway project), `just cms-shell-prod` then opens a Django shell through an SSH tunnel, and `just bastion-down` removes the gateway. For psql or pg_dump: `ssh -N -p 61000 -L 15432:$(tofu output -raw cms_db_host):$(tofu output -raw cms_db_port) bastion@$(tofu output -raw bastion_ip)`, then connect to `127.0.0.1:15432`. Any infrastructure apply from `main` removes the bastion.

The public endpoint of an instance created before this change survives the apply (the provider keeps it): delete it once with `scw rdb endpoint delete <endpoint_id> instance-id=<instance_id> region=fr-par`, the IDs coming from `tofu state show module.cms_db.scaleway_rdb_instance.this` (its `load_balancer` block).

**CMS media uploads fail with 403.**
`pfat-cms-media` has a bucket policy (public-read for objects). A Scaleway bucket policy denies everything it doesn't list, including the project's own keys, so the policy's first statement must keep `s3:*` for the project - see `infra/modules/object-bucket/main.tf`. If uploads 403, check that statement survived and that the S3 key the container uses belongs to this project. The key is a `secret_environment_variable`, so it won't show in `tofu output` - check the container's env in the Scaleway dashboard.

**`tofu apply` fails with `insufficient permissions: write application`.**
The deploying Scaleway API key doesn't have IAM write rights. `object-bucket` used to create a bucket-scoped IAM application/policy/key for `cms`'s S3 media access; that's parked for now in favor of reusing the account-wide key, specifically to avoid needing this permission. If you still see this error, you're on an older revision of this module - pull `main`.

**GitHub Actions deploy fails on `aws s3 sync` or registry login.**
Check `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` repo secrets - all deploy workflows use the same credentials.

**`tofu apply` fails with "state lock".**
Someone else is mid-apply, or a previous run was killed (the lock is the object `envs/prod/terraform.tfstate.tflock` of the state bucket). Identify the lock with `tofu plan` (it prints the lock ID) and release with:

```bash
cd infra/envs/prod
tofu force-unlock <LOCK_ID>
```

**`just status` prints "(tofu output failed)".**
Run `just tf-init` first, or check that you're authenticated with the right Scaleway project (`echo $SCW_DEFAULT_PROJECT_ID`).
