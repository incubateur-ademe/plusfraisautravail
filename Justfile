# plusfraisautravail - local dev commands
#
# Run `just` to list available recipes, or `just <recipe>` to run one.
# Requires: node 22+, uv, opentofu (`tofu`), awscli (for bucket sync).

set shell := ["bash", "-cu"]
set dotenv-load := true

# ── default ──────────────────────────────────────────────────────────────

default:
    @just --list

# ── install / bootstrap ──────────────────────────────────────────────────

# Install all JS workspace dependencies + sync the CMS venv.
install:
    npm install
    cd apps/cms && uv sync --extra dev

# Just the JS side.
install-js:
    npm install

# Just the CMS's Python side.
install-cms:
    cd apps/cms && uv sync --extra dev

# ── dev servers ──────────────────────────────────────────────────────────

# Run the autodiag SPA on :5173 (http://localhost:5173/autodiag/).
autodiag:
    npm run dev --workspace @pfat/autodiag

# Run the alert-widget SPA on :5173 (http://localhost:5173/alert-widget/).
# Vite proxies /api/* -> http://localhost:8080 - start `just cms` in another terminal.
alert-widget:
    npm run dev --workspace @pfat/alert-widget

# Run the climadiag SPA on :5173 (http://localhost:5173/climadiag/).
# Vite proxies /api/* -> http://localhost:8080 - start `just cms` in another terminal.
climadiag:
    npm run dev --workspace @pfat/climadiag

# Run the CMS locally on :8080 (auto-reload), with the alert API under /api/.
# Requires apps/cms/.env - copy from .env.example.
cms:
    cd apps/cms && DJANGO_SETTINGS_MODULE=cms.settings.dev uv run python manage.py runserver 8080

# Django shell against the PROD database, read-write - every ORM write hits
# production. Pass a command to run it non-interactively:
#   just cms-shell-prod -c "from wagtail.images import get_image_model; print(get_image_model().objects.count())"
[positional-arguments]
cms-shell-prod *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    # tofu's S3 backend needs the SCW keys from .env, same as the other
    # prod recipes - without it `tofu output` 403s on state load.
    cd "{{justfile_directory()}}/infra/envs/prod"
    set -a && source ../../../.env && set +a
    dsn="$(tofu output -raw cms_db_public_url)"
    pw="$(tofu output -raw cms_db_password)"
    # The RDB password contains % ) + < = - dj_database_url parses
    # DATABASE_URL as a URI, so the raw password can't be interpolated
    # (% starts an escape, + decodes to a space). Percent-encode it.
    pw_enc="$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$pw")"
    # Rebuild the DSN with the encoded password; cms_db_public_url carries
    # the host/port/dbname and ?sslmode=require already.
    url="${dsn%%://*}://cms:${pw_enc}@${dsn##*@}"
    cd "{{justfile_directory()}}/apps/cms"
    # "$@" via just's positional args, so a multi-line -c "..." script stays
    # one argument instead of being word-split.
    DATABASE_URL="$url" DJANGO_SETTINGS_MODULE=cms.settings.dev \
      uv run python manage.py shell "$@"

# Extract translatable strings from the wagtail-notion-form package into its French .po file.
makemessages-notion-form:
    cd packages/wagtail-notion-form/wagtail_notion_form && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py makemessages -l fr

# Extract translatable strings from the sites-conformes-footer-partners package into its French .po file.
makemessages-footer-partners:
    cd packages/sites-conformes-footer-partners/sites_conformes_footer_partners && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py makemessages -l fr

# Extract translatable strings from the sites-conformes-header-logo package into its French .po file.
makemessages-header-logo:
    cd packages/sites-conformes-header-logo/sites_conformes_header_logo && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py makemessages -l fr

# Compile all .po files (including the local packages) into .mo, so translations take effect.
# wagtail-notion-form, sites-conformes-footer-partners, and sites-conformes-header-logo live
# outside apps/cms's tree, so compilemessages doesn't reach them - compiled separately below.
compilemessages-cms:
    cd apps/cms && DJANGO_SETTINGS_MODULE=cms.settings.dev uv run python manage.py compilemessages -l fr
    cd packages/wagtail-notion-form/wagtail_notion_form && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py compilemessages -l fr
    cd packages/sites-conformes-footer-partners/sites_conformes_footer_partners && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py compilemessages -l fr
    cd packages/sites-conformes-header-logo/sites_conformes_header_logo && ../../../apps/cms/.venv/bin/python ../../../apps/cms/manage.py compilemessages -l fr

# Run the CMS (with the API) + alert-widget together.
dev:
    @echo "Run in two terminals:"
    @echo "  just cms"
    @echo "  just alert-widget"

# ── build ────────────────────────────────────────────────────────────────

# Build everything (all JS workspaces).
build:
    npm run build

build-autodiag:
    npm run build --workspace @pfat/autodiag

build-alert-widget:
    npm run build --workspace @pfat/alert-widget

build-climadiag:
    npm run build --workspace @pfat/climadiag

# Build the CMS container image locally.
# Context is the repo root, not apps/cms: the Dockerfile COPYs packages/*,
# which apps/cms depends on via editable path sources outside its own tree.
build-cms:
    docker build -f apps/cms/Dockerfile -t pfat-cms:local .

# ── test / lint ──────────────────────────────────────────────────────────

# Run all checks: JS build + CMS tests (the API's included) + ruff.
check: build test-cms lint-cms

# CMS tests.
test-cms:
    cd apps/cms && uv run python manage.py compilemessages -l fr
    cd apps/cms && uv run pytest

# sites-conformes-rgaa package tests (not covered by test-cms's testpaths).
test-rgaa:
    cd packages/sites-conformes-rgaa && DJANGO_SETTINGS_MODULE=cms.settings.dev PYTHONPATH="../../apps/cms:${PYTHONPATH:-}" ../../apps/cms/.venv/bin/python -m pytest sites_conformes_rgaa/tests/

# CMS lint (ruff), with the API package it serves.
lint-cms:
    cd apps/cms && uv run ruff check . ../../packages/pfat-api

# Auto-fix ruff issues where possible.
fmt-cms:
    cd apps/cms && uv run ruff check --fix . ../../packages/pfat-api
    cd apps/cms && uv run ruff format . ../../packages/pfat-api

# JS lint (per-workspace).
lint-js:
    npm run lint --if-present

# ── pre-commit hooks ─────────────────────────────────────────────────────

# Install the git pre-commit hook (one-time, run after cloning).
install-hooks:
    cd apps/cms && uv run pre-commit install

# Run all hooks on every tracked file (handy after editing the config).
hooks:
    cd apps/cms && uv run pre-commit run --all-files

# OpenTofu fmt + validate (prod env).
tf-fmt:
    cd infra && tofu fmt -recursive

tf-validate:
    cd infra/envs/prod && tofu init -backend=false && tofu validate

# ── containers ───────────────────────────────────────────────────────────

# Run the locally built CMS image (requires .env in apps/cms/).
run-cms-container: build-cms
    docker run --rm -p 8081:8080 --env-file apps/cms/.env pfat-cms:local

# ── infra (opentofu) ─────────────────────────────────────────────────────

# Init the prod stack. Run once; needs SCW_* env vars set.
tf-init:
    cd infra/envs/prod && tofu init

# Plan the prod stack.
tf-plan:
    cd infra/envs/prod && tofu plan

# Apply the prod stack (interactive confirm).
tf-apply:
    cd infra/envs/prod && tofu apply

# ── bootstrap (one-time, run from a fresh Scaleway account) ──────────────
#
# Order is documented in DEPLOY.md. Each recipe is idempotent / safe to
# re-run except where noted.

# Create the OpenTofu state bucket on Scaleway Object Storage.
# Requires AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY = your SCW access/secret key.
bootstrap-state:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
      echo "ERROR: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set."
      echo "       Use your Scaleway access key / secret key (same values as SCW_ACCESS_KEY / SCW_SECRET_KEY)."
      echo
      echo "  fish: set -x AWS_ACCESS_KEY_ID \$SCW_ACCESS_KEY"
      echo "        set -x AWS_SECRET_ACCESS_KEY \$SCW_SECRET_KEY"
      echo "  bash: export AWS_ACCESS_KEY_ID=\$SCW_ACCESS_KEY"
      echo "        export AWS_SECRET_ACCESS_KEY=\$SCW_SECRET_KEY"
      exit 1
    fi
    echo "About to create the OpenTofu state bucket:"
    echo "  endpoint: https://s3.fr-par.scw.cloud"
    echo "  bucket:   pfat-terraform"
    echo "  region:   fr-par"
    read -r -p "Proceed? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
    aws --endpoint-url=https://s3.fr-par.scw.cloud s3 mb s3://pfat-terraform --region fr-par

# Copy terraform.tfvars.example to terraform.tfvars (if missing) and open it.
bootstrap-tfvars:
    #!/usr/bin/env bash
    set -euo pipefail
    cd infra/envs/prod
    if [[ -f terraform.tfvars ]]; then
      echo "infra/envs/prod/terraform.tfvars already exists - opening it."
    else
      cp terraform.tfvars.example terraform.tfvars
      echo "Created infra/envs/prod/terraform.tfvars from the example."
    fi
    "${EDITOR:-vi}" terraform.tfvars

# Push repo-level secrets used by terraform-plan.yml (which runs on PRs from
# any branch and can't read environment-scoped secrets). For the deploy
# workflows, use `just bootstrap-environments` instead - those secrets live
# on the cms / autodiag / alert-widget / climadiag GitHub Environments.
bootstrap-secrets:
    #!/usr/bin/env bash
    set -euo pipefail

    if ! command -v gh >/dev/null 2>&1; then
      echo "ERROR: gh CLI not found. Install it: https://cli.github.com/" >&2; exit 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
      echo "ERROR: gh CLI not authenticated. Run: gh auth login" >&2; exit 1
    fi

    set_secret() {
      local name="$1" value="$2"
      if [[ -z "$value" ]]; then echo "  skip   $name (empty)"
      else printf '  set    %s\n' "$name"; gh secret set "$name" --body "$value" >/dev/null
      fi
    }

    echo "Repo: $(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
    echo "Scope: repository (used by terraform-plan.yml on PRs)."
    read -r -p "Push repo-level secrets? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

    echo
    echo "── repo secrets ─────────────────────────────────────────────"
    set_secret SCW_ACCESS_KEY              "${SCW_ACCESS_KEY:-}"
    set_secret SCW_SECRET_KEY              "${SCW_SECRET_KEY:-}"
    set_secret SCW_DEFAULT_PROJECT_ID      "${SCW_DEFAULT_PROJECT_ID:-}"
    set_secret SCW_DEFAULT_ORGANIZATION_ID "${SCW_DEFAULT_ORGANIZATION_ID:-}"
    set_secret VIGILANCE_APP_ID            "${VIGILANCE_APP_ID:-}"
    set_secret RTE_CLIENT_ID               "${RTE_CLIENT_ID:-}"
    set_secret RTE_CLIENT_SECRET           "${RTE_CLIENT_SECRET:-}"
    set_secret CLIMADIAG_API_TOKEN         "${CLIMADIAG_API_TOKEN:-}"
    set_secret DJANGO_SECRET_KEY           "${DJANGO_SECRET_KEY:-}"

    echo
    echo "Done. Run \`just bootstrap-environments\` next to push deploy-time secrets."

# Create (or update) the cms / autodiag / alert-widget / climadiag
# GitHub Environments and push the right secrets and variables to each. Reads
# SCW_*, S3_BUCKET_SCW_*, VIGILANCE_APP_ID, RTE_*, CLIMADIAG_API_TOKEN,
# DJANGO_SECRET_KEY from your shell and cms_url / cms_container_id / *_url
# from `tofu output`.
# Restricts each environment to the `main` branch so only main-branch deploys
# can read them. Idempotent.
bootstrap-environments:
    #!/usr/bin/env bash
    set -euo pipefail

    if ! command -v gh >/dev/null 2>&1; then
      echo "ERROR: gh CLI not found. Install it: https://cli.github.com/" >&2; exit 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
      echo "ERROR: gh CLI not authenticated. Run: gh auth login" >&2; exit 1
    fi

    REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')

    set_env_secret() {
      local env="$1" name="$2" value="$3"
      if [[ -z "$value" ]]; then echo "  skip   [$env] $name (empty)"
      else
        printf '  set    [%s] %s\n' "$env" "$name"
        gh secret set "$name" --env "$env" --body "$value" >/dev/null
      fi
    }
    set_env_variable() {
      local env="$1" name="$2" value="$3"
      if [[ -z "$value" ]]; then echo "  skip   [$env] $name (empty)"
      else
        printf '  set    [%s] %s = %s\n' "$env" "$name" "$value"
        gh variable set "$name" --env "$env" --body "$value" >/dev/null
      fi
    }
    create_env_main_only() {
      local env="$1"
      printf '  ensure %s (branch=main)\n' "$env"
      # PUT is idempotent. Pipe a real JSON body so the booleans get encoded
      # as booleans (gh api's -f always sends strings, and -F doesn't reach
      # into nested keys like deployment_branch_policy.protected_branches).
      printf '%s' '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' \
        | gh api -X PUT "repos/$REPO/environments/$env" --input - --silent
      # Wipe any existing branch policies, then add `main` only.
      gh api "repos/$REPO/environments/$env/deployment-branch-policies" \
        --jq '.branch_policies[].id' \
        | while read -r id; do
            [[ -n "$id" ]] && gh api -X DELETE \
              "repos/$REPO/environments/$env/deployment-branch-policies/$id" --silent
          done
      gh api -X POST "repos/$REPO/environments/$env/deployment-branch-policies" \
        -f name=main -f type=branch --silent || true
    }

    echo "Repo: $REPO"
    read -r -p "Create/update environments cms, autodiag, alert-widget, climadiag and push secrets? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

    # Capture tofu outputs once. Empty strings are OK - set_env_variable skips.
    cms_url=""
    cms_container_id=""
    cms_manage_job_id=""
    autodiag_url=""
    alert_widget_url=""
    climadiag_url=""
    if (cd infra/envs/prod && tofu output -raw autodiag_url) >/dev/null 2>&1; then
      autodiag_url=$(cd infra/envs/prod && tofu output -raw autodiag_url)
      alert_widget_url=$(cd infra/envs/prod && tofu output -raw alert_widget_url)
      climadiag_url=$(cd infra/envs/prod && tofu output -raw climadiag_url)
    else
      echo "  warn   tofu output unavailable - *_URL will be skipped."
      echo "         Run \`just tf-apply\`, then re-run this."
    fi
    if (cd infra/envs/prod && tofu output -raw cms_url) >/dev/null 2>&1; then
      cms_url=$(cd infra/envs/prod && tofu output -raw cms_url)
      # Scaleway REST API expects the bare UUID, not the "fr-par/<uuid>" form
      # that `tofu output` returns.
      cms_container_id=$(cd infra/envs/prod && tofu output -raw cms_container_id)
      cms_container_id="${cms_container_id##*/}"
      cms_manage_job_id=$(cd infra/envs/prod && tofu output -raw cms_manage_job_id)
      cms_manage_job_id="${cms_manage_job_id##*/}"
    else
      echo "  warn   tofu output unavailable - CMS_URL / SCW_CMS_CONTAINER_ID / SCW_CMS_MANAGE_JOB_ID will be skipped."
      echo "         Run \`just tf-apply\` (with cms_deploy=true), then re-run this."
    fi

    echo
    echo "── cms environment ──────────────────────────────────────────"
    create_env_main_only cms
    set_env_secret   cms SCW_ACCESS_KEY         "${SCW_ACCESS_KEY:-}"
    set_env_secret   cms SCW_SECRET_KEY         "${SCW_SECRET_KEY:-}"
    set_env_secret   cms SCW_DEFAULT_PROJECT_ID "${SCW_DEFAULT_PROJECT_ID:-}"
    set_env_secret   cms DJANGO_SECRET_KEY      "${DJANGO_SECRET_KEY:-}"
    set_env_variable cms SCW_CMS_CONTAINER_ID   "$cms_container_id"
    set_env_variable cms SCW_CMS_MANAGE_JOB_ID  "$cms_manage_job_id"
    set_env_variable cms CMS_URL                "$cms_url"

    echo
    echo "── autodiag environment ─────────────────────────────────────"
    create_env_main_only autodiag
    set_env_secret   autodiag SCW_ACCESS_KEY    "${SCW_ACCESS_KEY:-}"
    set_env_secret   autodiag SCW_SECRET_KEY    "${SCW_SECRET_KEY:-}"
    set_env_variable autodiag SITE_URL          "$autodiag_url"

    echo
    echo "── alert-widget environment ─────────────────────────────────"
    create_env_main_only alert-widget
    set_env_secret   alert-widget SCW_ACCESS_KEY "${SCW_ACCESS_KEY:-}"
    set_env_secret   alert-widget SCW_SECRET_KEY "${SCW_SECRET_KEY:-}"
    # Same origin: the proxy sends /api/ to the CMS (no CORS).
    set_env_variable alert-widget API_BASE_URL   "/api"
    set_env_variable alert-widget SITE_URL       "$alert_widget_url"

    echo
    echo "── climadiag environment ────────────────────────────────────"
    create_env_main_only climadiag
    set_env_secret   climadiag SCW_ACCESS_KEY "${SCW_ACCESS_KEY:-}"
    set_env_secret   climadiag SCW_SECRET_KEY "${SCW_SECRET_KEY:-}"
    set_env_variable climadiag API_BASE_URL   "/api"
    set_env_variable climadiag SITE_URL       "$climadiag_url"

    echo
    echo "── tofu-apply environment ───────────────────────────────────"
    # Used by terraform-apply.yml. Needs the full set of Scaleway creds
    # plus the TF_VAR_* secrets that drive the runtime configuration.
    create_env_main_only tofu-apply
    set_env_secret   tofu-apply SCW_ACCESS_KEY              "${SCW_ACCESS_KEY:-}"
    set_env_secret   tofu-apply SCW_SECRET_KEY              "${SCW_SECRET_KEY:-}"
    set_env_secret   tofu-apply SCW_DEFAULT_PROJECT_ID      "${SCW_DEFAULT_PROJECT_ID:-}"
    set_env_secret   tofu-apply SCW_DEFAULT_ORGANIZATION_ID "${SCW_DEFAULT_ORGANIZATION_ID:-}"
    set_env_secret   tofu-apply VIGILANCE_APP_ID            "${VIGILANCE_APP_ID:-}"
    set_env_secret   tofu-apply RTE_CLIENT_ID               "${RTE_CLIENT_ID:-}"
    set_env_secret   tofu-apply RTE_CLIENT_SECRET           "${RTE_CLIENT_SECRET:-}"
    set_env_secret   tofu-apply CLIMADIAG_API_TOKEN         "${CLIMADIAG_API_TOKEN:-}"
    set_env_secret   tofu-apply DJANGO_SECRET_KEY           "${DJANGO_SECRET_KEY:-}"
    set_env_secret   tofu-apply S3_BUCKET_SCW_ACCESS_KEY_ID "${S3_BUCKET_SCW_ACCESS_KEY_ID:-}"
    set_env_secret   tofu-apply S3_BUCKET_SCW_SECRET_KEY    "${S3_BUCKET_SCW_SECRET_KEY:-}"

    echo
    echo "Done. Verify in the GitHub UI:"
    echo "  https://github.com/$REPO/settings/environments"

# ── deploy (manual triggers) ─────────────────────────────────────────────

# One-time first image push for the CMS, before the second tf-apply.
# Requires SCW_SECRET_KEY in env (used as docker registry password).
deploy-cms-bootstrap:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -z "${SCW_SECRET_KEY:-}" ]]; then
      echo "ERROR: SCW_SECRET_KEY must be set in the environment."
      exit 1
    fi
    REGISTRY="rg.fr-par.scw.cloud"
    NAMESPACE="pfat"
    IMAGE="$REGISTRY/$NAMESPACE/cms:bootstrap"
    echo "About to:"
    echo "  1. docker login $REGISTRY (user=nologin, password=\$SCW_SECRET_KEY)"
    echo "  2. docker buildx build --platform linux/amd64 --push apps/cms/ -t $IMAGE"
    read -r -p "Proceed? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
    echo "$SCW_SECRET_KEY" | docker login "$REGISTRY" --username nologin --password-stdin
    docker buildx build --platform linux/amd64 --push -t "$IMAGE" apps/cms/
    echo
    echo "Pushed: $IMAGE"
    echo
    echo "Now edit infra/envs/prod/terraform.tfvars:"
    echo "  cms_image  = \"$IMAGE\""
    echo "  cms_deploy = true"
    echo "Then run: just tf-apply"

# Trigger the CMS deploy workflow on GitHub.
deploy-cms:
    #!/usr/bin/env bash
    set -euo pipefail
    gh workflow run deploy-cms.yml
    sleep 2
    URL=$(gh run list --workflow=deploy-cms.yml --limit 1 --json url --jq '.[0].url')
    echo "Triggered: $URL"

# Trigger the autodiag deploy workflow on GitHub.
deploy-autodiag:
    #!/usr/bin/env bash
    set -euo pipefail
    gh workflow run deploy-autodiag.yml
    sleep 2
    URL=$(gh run list --workflow=deploy-autodiag.yml --limit 1 --json url --jq '.[0].url')
    echo "Triggered: $URL"

# Trigger the alert-widget deploy workflow on GitHub.
deploy-alert-widget:
    #!/usr/bin/env bash
    set -euo pipefail
    gh workflow run deploy-alert-widget.yml
    sleep 2
    URL=$(gh run list --workflow=deploy-alert-widget.yml --limit 1 --json url --jq '.[0].url')
    echo "Triggered: $URL"

# Trigger the climadiag deploy workflow on GitHub.
deploy-climadiag:
    #!/usr/bin/env bash
    set -euo pipefail
    gh workflow run deploy-climadiag.yml
    sleep 2
    URL=$(gh run list --workflow=deploy-climadiag.yml --limit 1 --json url --jq '.[0].url')
    echo "Triggered: $URL"

# Show tofu outputs + last-deploy timestamps for each workflow.
status:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "── tofu outputs ───────────────────────────────────────────────"
    (cd infra/envs/prod && tofu output) || echo "(tofu output failed - did you run \`just tf-init\` + \`just tf-apply\`?)"
    echo
    echo "── last GitHub Actions runs ───────────────────────────────────"
    for wf in deploy-cms.yml deploy-autodiag.yml deploy-alert-widget.yml deploy-climadiag.yml; do
      printf '%-30s ' "$wf"
      gh run list --workflow="$wf" --limit 1 \
        --json status,conclusion,createdAt,url \
        --jq '.[] | "\(.status)/\(.conclusion // " - ")  \(.createdAt)  \(.url)"' \
        2>/dev/null || echo "(no runs yet)"
    done

# Render infra/scalingo-proxy/servers.conf.erb and run `nginx -t` on it (nginx via nix).
proxy-check:
    #!/usr/bin/env bash
    set -euo pipefail
    tmp=$(mktemp -d)
    (cd infra/scalingo-proxy && PORT=8080 CMS_HOST=cms.example erb servers.conf.erb) > "$tmp/servers.conf"
    printf 'pid %s/nginx.pid;\nerror_log stderr;\nevents {}\nhttp { access_log off; include %s/servers.conf; }\n' "$tmp" "$tmp" > "$tmp/nginx.conf"
    nix run nixpkgs#nginx -- -t -c "$tmp/nginx.conf" -p "$tmp" 2>&1 | grep -v 'could not open error log'
    rm -rf "$tmp"

# ── housekeeping ─────────────────────────────────────────────────────────

# Remove all build/test caches and node_modules. Forces a fresh `just install`.
clean:
    rm -rf node_modules apps/*/node_modules apps/*/dist packages/*/node_modules
    rm -rf apps/cms/.venv apps/cms/.pytest_cache apps/cms/.ruff_cache apps/cms/staticfiles
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
