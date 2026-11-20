# Deploying plusfraisautravail to Scaleway

Single source of truth for the bootstrap and the day-to-day deploy flow.

The stack is provisioned with [OpenTofu](https://opentofu.org/) (`infra/envs/prod/`) on Scaleway:

| Resource | Module | Created from |
|---|---|---|
| Bucket `pfat-terraform` | none | `just bootstrap-state` (state backend) |
| Secret `pfat-prod-state-passphrase` | none | `just bootstrap-state` (2.2) |
| Secrets `pfat-prod-…` | none | `just secrets-push`, Scaleway Secret Manager (2.3) |
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

- Scaleway account with a project, plus an API key (access key + secret key) allowed on containers, registry, Object Storage, RDB, VPC and Secret Manager. For these secrets, the IAM permission sets `SecretManagerReadOnly` (find them by name) and `SecretManagerSecretAccess` (read their values); `SecretManagerFullAccess` for the key that creates or changes them (2.2, 2.3), which need not be the one of the CI.
- The secrets of the third parties, each optional: Météo-France [Vigilance API](https://portail-api.meteofrance.fr/) application ID, RTE Ecowatt OAuth2 client ID and secret, PlusFraîcheMaVille Climadiag token, Notion token. Without one, the matching feature answers 503 or is off; everything else works.
- [GitHub CLI](https://cli.github.com/) (`gh auth login`), [AWS CLI v2](https://docs.aws.amazon.com/cli/) (S3 client), [Scaleway CLI](https://cli.scaleway.com/), [OpenTofu](https://opentofu.org/) 1.10+, Docker, [`just`](https://github.com/casey/just), `jq`, `curl`, `openssl`.

---

## 2. One-time bootstrap

Run these in order. The recipes that change something ask for confirmation.

**In another Scaleway project**, change these names first (bucket names are global, registry namespaces are unique per region):

| What | Where |
|---|---|
| State bucket `pfat-terraform` | `infra/envs/prod/backend.tf`, `bootstrap-state` in the `Justfile` |
| Secret names `pfat-prod-…` | `infra/envs/prod/main.tf`, `infra/tofu.sh`; `state-passphrase`, `secrets-show` and `secrets-push` in the `Justfile` |
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

### 2.2 State bucket and its passphrase

OpenTofu can't manage its own state bucket:

```bash
just bootstrap-state
```

It also creates the secret `pfat-prod-state-passphrase`, a random passphrase, unless it exists (`just state-passphrase` does only that). The state holds every secret of the stack: OpenTofu encrypts it with a key derived from this passphrase before it leaves the machine, so the bucket only holds ciphertext. `infra/tofu.sh` reads the passphrase at each run, in CI and for the `just` recipes: nothing to export. A bare `tofu` in `infra/envs/prod` stops on the missing `var.state_passphrase`: use `infra/tofu.sh <command>` instead.

**The state cannot be read without the passphrase.** The secret is protected against deletion; never disable its version, and keep a copy in the team's password manager (`just secrets-show state-passphrase`).

The states of the previews (section 4) are not encrypted.

### 2.3 The secrets: one file, one Secret Manager secret per value

Every hand-provided secret is one Scaleway Secret Manager secret, named `pfat-prod-<name>`, at the default path. `infra/envs/prod/secrets.example.json` lists them. OpenTofu reads the latest enabled version of each at every plan and passes it to the containers that need it. All ten must exist: a missing one fails the plan, naming it.

```bash
cp infra/envs/prod/secrets.example.json infra/envs/prod/secrets.json   # gitignored
# fill it in, then
just secrets-push
rm infra/envs/prod/secrets.json
```

`secrets-push` creates the missing secrets, adds a version to those whose value changed (disabling the previous one) and leaves the others alone. It refuses a file whose keys differ from `secrets.example.json`: a new secret is added there first.

| Key | What it is | Goes to | GitHub secret it replaces |
|---|---|---|---|
| `vigilance-app-id` | Météo-France Vigilance application ID | cms | `VIGILANCE_APP_ID` |
| `rte-client-id` | RTE Ecowatt OAuth2 client ID | cms | `RTE_CLIENT_ID` |
| `rte-client-secret` | RTE Ecowatt OAuth2 client secret | cms | `RTE_CLIENT_SECRET` |
| `climadiag-api-token` | PlusFraîcheMaVille Climadiag token | cms | `CLIMADIAG_API_TOKEN` |
| `notion-token` | Notion integration token (contact form) | cms, cms-manage | `NOTION_TOKEN` |
| `email-host-password` | Scaleway API secret key allowed to send with Transactional Email | cms, cms-manage | `EMAIL_HOST_PASSWORD`, or `S3_BUCKET_SCW_SECRET_KEY` if it was never set |
| `cms-media-access-key-id` | Scaleway API access key for the media bucket | cms, cms-manage | `S3_BUCKET_SCW_ACCESS_KEY_ID` |
| `cms-media-secret-key` | its secret key | cms, cms-manage | `S3_BUCKET_SCW_SECRET_KEY` |
| `e2e-fixtures-access-key-id` | Scaleway API access key for the e2e fixtures bucket | e2e-dump | `S3_BUCKET_SCW_ACCESS_KEY_ID` |
| `e2e-fixtures-secret-key` | its secret key | e2e-dump | `S3_BUCKET_SCW_SECRET_KEY` |

The media, fixtures and e-mail secrets may all hold the same Scaleway key today. They are separate so that each can later get its own key, restricted to its bucket or to e-mail, without touching the code.

The first six are optional credentials: leave `""` for one you do not have. Its secret still exists, it is not passed to the containers and its feature is off (503 on the matching API endpoint, no Notion sync, no outgoing mail). The four key secrets must not be empty: the plan fails, naming the empty one.

If a secret named `pfat-prod` is left from earlier trials, delete it: nothing reads it.

To change a secret later: `just secrets-show > infra/envs/prod/secrets.json`, edit, `just secrets-push`, delete the file, then apply (`just deploy infrastructure`, or any merge touching `infra/`). The Django `SECRET_KEY` and the database passwords are not secrets to create: OpenTofu generates them. To rotate the Django key, run 🏗️ Infrastructure by hand with `tofu_replace` = `random_password.django_secret_key`: every admin is logged out and pending signed links (password reset) stop working.

For these secrets, GitHub masks nothing in logs, as it does not know their values: only OpenTofu's `sensitive` marking hides them, in a plan that is public. Never wrap them in `nonsensitive()` or put them in an output.

### 2.4 Registry, first image, then everything else

Scaleway only creates a container whose image exists, so the registry and a first image come first:

```bash
just tf-init
infra/tofu.sh apply -target=scaleway_registry_namespace.pfat
just deploy-cms-bootstrap   # builds and pushes rg.fr-par.scw.cloud/pfat/cms:latest
just tf-apply
```

**The RDB instance takes several minutes to provision.** From then on OpenTofu ignores the containers' image: the deploys roll images out.

### 2.5 GitHub secrets and environments

```bash
just bootstrap-secrets        # the 4 SCW_* repository secrets (plan on pull requests)
just bootstrap-environments   # cms / autodiag / alert-widget / climadiag / tofu-apply environments, `preview` label
```

GitHub only holds the Scaleway key: `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`, at repository level and in each environment (restricted to `main`). Not secret, as repository variables: `SENTRY_DSN`, `POSTHOG_KEY`, and `CMS_BASE_URL` while testing before a DNS cutover.

**On a repository set up before Secret Manager**, create the passphrase (`just state-passphrase`) and the ten secrets (2.3) before merging. GitHub does not give a secret back: take the values from where they came from (Scaleway console, Météo-France, RTE, PlusFraîcheMaVille and Notion accounts). Give the Scaleway key of the CI the two Secret Manager permission sets (section 1). Until the first apply from CI is over, `just bastion-up` fails ("Moved resource instances excluded by targeting"). That apply also writes the state encrypted, even if it changes nothing else: from then on a local checkout from before the encryption can no longer read it. Until then the stack still accepts a state in clear: once that apply is over, remove the `unencrypted` method and the `fallback` block from `infra/envs/prod/backend.tf` and add `enforced = true` to its `state` block, in a pull request.

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

## 4. Preview of a pull request

The `preview` label on a pull request to `main` (same repository, not a fork) runs `preview.yml`, which applies `infra/envs/preview` in a workspace `pr-<number>` and posts the URL on the pull request. Each push updates it.

| Created per pull request | Name |
|---|---|
| Database on the production instance | `preview_pr_<number>` |
| Its user: not admin, permission `all` on that database and on no other | `preview_pr_<number>` |
| Public container, on the database's Private Network, stopped while unused | `cms-pr-<number>` |
| Image tags in the private registry | `cms-preview:pr-<number>-<sha>` |

The image holds the nightly anonymised dump. At its first start the container restores it into its database; later starts only run the migrations, so what is changed in a preview is kept. A preview gets no mail, Notion, Sentry, PostHog, alert API or bucket key.

**Media.** A preview has no bucket (`apps/cms/cms/preview.py`). What it uploads, and the renditions it makes, go to its own database (the `db_storage` of sites-conformes) and are destroyed with it. The images of production are read from their public URL (`/media/images/`, `/media/original_images/`). Documents are not public: a preview has none, their links answer an error.

At every start the container first tries to connect to the production database as its own user, and only starts if PostgreSQL answers "permission denied for database". This detects a configuration error (a permission granted by mistake, another instance). It does not contain hostile code: a pull request can remove the check.

Every preview holds the password of its database user and its Django key, in its container and in clear in its state (`env:/pr-<number>/` in `pfat-terraform`).

### What a preview shares with production

- **Connections.** The instance has one pool for every database. Production may open up to 48 (3 instances, 2 workers, 8 threads), plus its two private containers. A preview keeps no connection between requests and opens at most 8 while it serves (one worker). Run `SHOW max_connections` on the instance: with the PostgreSQL default of 100, **keep to 5 previews at once**. This assumes Scaleway reserves no more connections than PostgreSQL's three, and that production stays at 48 (two revisions overlap during one of its deploys). Nothing enforces the ceiling, and a stopped preview wakes up at the first request.
- **Disk.** 10 GB for everything. A preview takes about 115 MB as soon as it exists, plus what it uploads and the renditions it makes, and keeps it until it is destroyed, backups included.
- **Load.** The first start of each preview restores and indexes on the production instance (about 25 s locally).

**Nothing is destroyed by itself**, not even when the pull request is closed. To destroy a preview: run the `🌱 Preview` workflow by hand with the number of the pull request (`gh workflow run preview.yml -f pr_number=<number>`). It destroys everything in the table above. What stays behind until then: the database, the user, the stopped container and the image tags.

**In another Scaleway project**, change: the state bucket and the instance name `cms-prod` in `infra/envs/preview/main.tf`; the bucket `pfat-e2e-fixtures` and the registry `rg.fr-par.scw.cloud/pfat` in `preview.yml`; the production URL of the media in `apps/cms/cms/settings/preview.py`. `just bootstrap-environments` creates the `preview` label.

---

## 5. Frontend bucket layout

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

## 6. Public hostname: Scalingo nginx proxy

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

The app is `plusfraisautravail-proxy` (osc-fr1). Its env already carries `BUILDPACK_URL`, `PROJECT_DIR=infra/scalingo-proxy`, `CMS_HOST` (the cms container's Scaleway hostname, from `infra/tofu.sh output cms_url`). `scalingo -a plusfraisautravail-proxy git-setup` adds the `scalingo` git remote, then:

```bash
git push scalingo main   # or link the GitHub repo in the Scalingo dashboard
```

The nginx buildpack needs no Procfile and no APT packages on the `scalingo-26` stack.

**Testing on the proxy hostname before cutover.** Absolute URLs (media, `image.full_url`, admin emails) are built from `WAGTAILADMIN_BASE_URL`, which defaults to the production domain. To test on `https://plusfraisautravail-proxy.osc-fr1.scalingo.io`, set the GitHub repo variable `CMS_BASE_URL` to that URL and re-run 🏗️ Infrastructure (`infrastructure.yml`); delete the variable and re-apply at cutover. The `canonical`/`og:url` tags come from the Wagtail Site record in the database and always name the production domain, which is correct.

The SPAs must be built with their default sub-path base (`/autodiag/` etc.), not `VITE_BASE_URL=/`, for the proxy's prefix routing to work. Wagtail pages must not use the slugs `static`, `media`, `api`, `autodiag`, `alert-widget` or `climadiag`.

`just proxy-check` renders the template and runs `nginx -t` on it.

---

## 7. Troubleshooting

**"image not found" on the first `tofu apply`.**
The containers are created with `pfat/cms:latest`: push it first (2.4).

**`infra/tofu.sh` fails with "Cannot read the secret pfat-prod-state-passphrase".**
The secret does not exist (`just state-passphrase`), its version is disabled, or the Scaleway key cannot read Secret Manager (section 1).

**`tofu` fails with "decryption failed for all provided methods" or stops on `var.state_passphrase`.**
The second: use `infra/tofu.sh`, not a bare `tofu`. The first: the enabled version of `pfat-prod-state-passphrase` is not the one the state was written with. Enable that version again (`scw secret version list <secret-id>`), or take the passphrase from the password manager.

**The plan fails on `data.scaleway_secret_version.app["…"]`.**
The secret `pfat-prod-…` named in the error does not exist, has no enabled version, or the Scaleway key cannot read Secret Manager (2.3). Nothing was changed. To go back to the previous value of a secret, disable its latest version and apply.

**Destroying the stack.**
Not a workflow: the database and its instance have `prevent_destroy` and the media bucket no `force_destroy`. Remove them in a pull request first, then `infra/tofu.sh destroy` locally.

**API returns 502 on `/api/alerts/meteo` or `/api/alerts/electricity`.**
The upstream (Météo-France or RTE) failed and no earlier snapshot is cached. Check the cms container logs (Scaleway dashboard -> Containers -> `cms-prod` -> Logs). Most common cause: a wrong `VIGILANCE_APP_ID`; a missing one answers 503.

**API returns 503 on `/api/alerts/electricity`.**
`pfat-prod-rte-client-id` or `pfat-prod-rte-client-secret` is empty (2.3). Wrong credentials answer 502 instead.

**API returns 503 on `/api/climadiag/search`.**
`pfat-prod-climadiag-api-token` is empty (2.3). A wrong token answers 502 instead.

**CMS returns 502.**
Check Scaleway dashboard -> Containers -> `cms-prod` -> Logs. Most common causes: missing/wrong `DATABASE_URL` or `DJANGO_SECRET_KEY`, or the container can't reach Postgres over the Private Network (verify `module.cms` and `module.cms_db` ended up on the same `private_network_id` - check `infra/tofu.sh output cms_db_host` is a private `10.x`/`172.x` address, not a public one).

**CMS migrations don't seem to have run.**
Migrations are *not* run on container cold start - `entrypoint.sh` only starts gunicorn, to stay within the container's startup probe budget (a slow migration there previously got the container killed as "failed to start" even when the migration itself succeeded). Each CMS deploy runs them in the private `cms-manage` container (same image, `manage_server.py`, `POST /run` runs `manage_jobs.sh`); its stdout is in the deploy job's log, its errors in the container logs (Cockpit): they can quote a row. To run them by hand: `curl -X POST "$(infra/tofu.sh output -raw cms_manage_url)/run" -H "X-Auth-Token: $SCW_SECRET_KEY"`.

**Reaching the database by hand.**
The database has no public endpoint: only its Private Network reaches it (the CMS, cms-manage and e2e-dump containers). For an admin session, `just bastion-up <your public IP>` (or `bastion_allowed_ip_ranges` in `terraform.tfvars`: only those addresses reach it) creates a Public Gateway with an SSH bastion on that network (SSH keys: those of the Scaleway project), `just cms-shell-prod` then opens a Django shell through an SSH tunnel, and `just bastion-down` removes the gateway. For psql or pg_dump: `ssh -N -p 61000 -L 15432:$(infra/tofu.sh output -raw cms_db_host):$(infra/tofu.sh output -raw cms_db_port) bastion@$(infra/tofu.sh output -raw bastion_ip)`, then connect to `127.0.0.1:15432`. Any infrastructure apply from `main` removes the bastion.

The public endpoint of an instance created before this change survives the apply (the provider keeps it): delete it once with `scw rdb endpoint delete <endpoint_id> instance-id=<instance_id> region=fr-par`, the IDs coming from `infra/tofu.sh state show module.cms_db.scaleway_rdb_instance.this` (its `load_balancer` block).

**CMS media uploads fail with 403.**
`pfat-cms-media` has a bucket policy (public-read for objects). A Scaleway bucket policy denies everything it doesn't list, including the project's own keys, so the policy's first statement must keep `s3:*` for the project - see `infra/modules/object-bucket/main.tf`. If uploads 403, check that statement survived and that the S3 key the container uses belongs to this project. The key is a `secret_environment_variable`, so it won't show in `tofu output` - check the container's env in the Scaleway dashboard.

**`tofu apply` fails with `insufficient permissions: write application`.**
The deploying Scaleway API key doesn't have IAM write rights. `object-bucket` used to create a bucket-scoped IAM application/policy/key for `cms`'s S3 media access; that's parked for now in favor of reusing the account-wide key, specifically to avoid needing this permission. If you still see this error, you're on an older revision of this module - pull `main`.

**GitHub Actions deploy fails on `aws s3 sync` or registry login.**
Check `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` repo secrets - all deploy workflows use the same credentials.

**`tofu apply` fails with "state lock".**
Someone else is mid-apply, or a previous run was killed (the lock is the object `envs/prod/terraform.tfstate.tflock` of the state bucket). Identify the lock with `just tf-plan` (it prints the lock ID) and release with:

```bash
infra/tofu.sh force-unlock <LOCK_ID>
```

**`just status` prints "(tofu output failed)".**
Run `just tf-init` first, or check that you're authenticated with the right Scaleway project (`echo $SCW_DEFAULT_PROJECT_ID`).
