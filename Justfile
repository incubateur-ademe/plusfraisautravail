# plusfraisautravail - local dev commands
#
# Run `just` to list available recipes, or `just <recipe>` to run one.
# Requires: node 22+, uv, opentofu (`tofu`), awscli (for bucket sync).

set shell := ["bash", "-cu"]
set dotenv-load := false

# ── default ──────────────────────────────────────────────────────────────

default:
    @just --list

# ── install / bootstrap ──────────────────────────────────────────────────

# Install all JS workspace dependencies + sync API venv.
install:
    npm install
    cd api && uv sync --extra dev

# Just the JS side.
install-js:
    npm install

# Just the Python side.
install-api:
    cd api && uv sync --extra dev

# ── dev servers ──────────────────────────────────────────────────────────

# Run the FastAPI gateway locally on :8080 (auto-reload).
api:
    cd api && uv run uvicorn pfat_api.main:app --reload --port 8080

# Run the autodiag SPA on :5173 (http://localhost:5173/autodiag/).
autodiag:
    npm run dev --workspace @pfat/autodiag

# Run the alert-widget SPA on :5173 (http://localhost:5173/alert-widget/).
# Vite proxies /api/* -> http://localhost:8080 - start `just api` in another terminal.
alert-widget:
    npm run dev --workspace @pfat/alert-widget

# Run API + alert-widget together (requires `parallel` from moreutils, or split into two shells).
dev:
    @echo "Run in two terminals:"
    @echo "  just api"
    @echo "  just alert-widget"

# ── build ────────────────────────────────────────────────────────────────

# Build everything (all JS workspaces).
build:
    npm run build

build-autodiag:
    npm run build --workspace @pfat/autodiag

build-alert-widget:
    npm run build --workspace @pfat/alert-widget

# Build the API container image locally.
build-api:
    cd api && docker build -t pfat-api:local .

# ── test / lint ──────────────────────────────────────────────────────────

# Run all checks: JS build + API tests + ruff.
check: build test-api lint-api

# API tests.
test-api:
    cd api && uv run pytest

# API lint (ruff).
lint-api:
    cd api && uv run ruff check .

# Auto-fix ruff issues where possible.
fmt-api:
    cd api && uv run ruff check --fix .
    cd api && uv run ruff format .

# JS lint (per-workspace).
lint-js:
    npm run lint --if-present

# ── pre-commit hooks ─────────────────────────────────────────────────────

# Install the git pre-commit hook (one-time, run after cloning).
install-hooks:
    cd api && uv run pre-commit install

# Run all hooks on every tracked file (handy after editing the config).
hooks:
    cd api && uv run pre-commit run --all-files

# OpenTofu fmt + validate (prod env).
tf-fmt:
    cd infra && tofu fmt -recursive

tf-validate:
    cd infra/envs/prod && tofu init -backend=false && tofu validate

# ── api container ────────────────────────────────────────────────────────

# Run the locally built API image (requires .env in api/).
run-api-container: build-api
    docker run --rm -p 8080:8080 --env-file api/.env pfat-api:local

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
    echo "  bucket:   pfat-tfstate"
    echo "  region:   fr-par"
    read -r -p "Proceed? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
    aws --endpoint-url=https://s3.fr-par.scw.cloud s3 mb s3://pfat-tfstate --region fr-par

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
# on the api / autodiag / alert-widget GitHub Environments.
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

    echo
    echo "Done. Run \`just bootstrap-environments\` next to push deploy-time secrets."

# Create (or update) the api / autodiag / alert-widget GitHub Environments
# and push the right secrets and variables to each. Reads SCW_*, VIGILANCE_APP_ID,
# RTE_* from your shell and api_url / container_id / *_url from `tofu output`.
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
    read -r -p "Create/update environments api, autodiag, alert-widget and push secrets? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }

    # Capture tofu outputs once. Empty strings are OK - set_env_variable skips.
    api_url=""
    container_id=""
    autodiag_url=""
    alert_widget_url=""
    if (cd infra/envs/prod && tofu output -raw api_url) >/dev/null 2>&1; then
      api_url=$(cd infra/envs/prod && tofu output -raw api_url)
      # Scaleway REST API expects the bare UUID, not the "fr-par/<uuid>" form
      # that `tofu output` returns.
      container_id=$(cd infra/envs/prod && tofu output -raw container_id)
      container_id="${container_id##*/}"
      autodiag_url=$(cd infra/envs/prod && tofu output -raw autodiag_url)
      alert_widget_url=$(cd infra/envs/prod && tofu output -raw alert_widget_url)
    else
      echo "  warn   tofu output unavailable - *_URL / SCW_API_CONTAINER_ID will be skipped."
      echo "         Run \`just tf-apply\` (with the container created), then re-run this."
    fi

    echo
    echo "── api environment ──────────────────────────────────────────"
    create_env_main_only api
    set_env_secret   api SCW_ACCESS_KEY         "${SCW_ACCESS_KEY:-}"
    set_env_secret   api SCW_SECRET_KEY         "${SCW_SECRET_KEY:-}"
    set_env_secret   api SCW_DEFAULT_PROJECT_ID "${SCW_DEFAULT_PROJECT_ID:-}"
    set_env_secret   api VIGILANCE_APP_ID       "${VIGILANCE_APP_ID:-}"
    set_env_secret   api RTE_CLIENT_ID          "${RTE_CLIENT_ID:-}"
    set_env_secret   api RTE_CLIENT_SECRET      "${RTE_CLIENT_SECRET:-}"
    set_env_variable api SCW_API_CONTAINER_ID   "$container_id"
    set_env_variable api API_URL                "$api_url"

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
    set_env_variable alert-widget API_BASE_URL   "$api_url"
    set_env_variable alert-widget SITE_URL       "$alert_widget_url"

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
    set_env_variable tofu-apply API_URL                     "$api_url"

    echo
    echo "Done. Verify in the GitHub UI:"
    echo "  https://github.com/$REPO/settings/environments"

# ── deploy (manual triggers) ─────────────────────────────────────────────

# One-time first image push, before the second tf-apply.
# Requires SCW_SECRET_KEY in env (used as docker registry password).
deploy-api-bootstrap:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -z "${SCW_SECRET_KEY:-}" ]]; then
      echo "ERROR: SCW_SECRET_KEY must be set in the environment."
      exit 1
    fi
    REGISTRY="rg.fr-par.scw.cloud"
    NAMESPACE="pfat-prod"
    IMAGE="$REGISTRY/$NAMESPACE/api:bootstrap"
    # Scaleway Serverless Containers only run amd64. `buildx --push` builds
    # cross-arch and uploads in one step (no need to materialize the image
    # locally - handy on Apple Silicon).
    echo "About to:"
    echo "  1. docker login $REGISTRY (user=nologin, password=\$SCW_SECRET_KEY)"
    echo "  2. docker buildx build --platform linux/amd64 --push api/ -t $IMAGE"
    read -r -p "Proceed? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
    echo "$SCW_SECRET_KEY" | docker login "$REGISTRY" --username nologin --password-stdin
    docker buildx build --platform linux/amd64 --push -t "$IMAGE" api/
    echo
    echo "Pushed: $IMAGE"
    echo
    echo "Now edit infra/envs/prod/terraform.tfvars:"
    echo "  api_image  = \"$IMAGE\""
    echo "  api_deploy = true"
    echo "Then run: just tf-apply"

# Trigger the API deploy workflow on GitHub.
deploy-api:
    #!/usr/bin/env bash
    set -euo pipefail
    gh workflow run deploy-api.yml
    sleep 2
    URL=$(gh run list --workflow=deploy-api.yml --limit 1 --json url --jq '.[0].url')
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

# Show tofu outputs + last-deploy timestamps for each workflow.
status:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "── tofu outputs ───────────────────────────────────────────────"
    (cd infra/envs/prod && tofu output) || echo "(tofu output failed - did you run \`just tf-init\` + \`just tf-apply\`?)"
    echo
    echo "── last GitHub Actions runs ───────────────────────────────────"
    for wf in deploy-api.yml deploy-autodiag.yml deploy-alert-widget.yml; do
      printf '%-30s ' "$wf"
      gh run list --workflow="$wf" --limit 1 \
        --json status,conclusion,createdAt,url \
        --jq '.[] | "\(.status)/\(.conclusion // " - ")  \(.createdAt)  \(.url)"' \
        2>/dev/null || echo "(no runs yet)"
    done

# ── housekeeping ─────────────────────────────────────────────────────────

# Remove all build/test caches and node_modules. Forces a fresh `just install`.
clean:
    rm -rf node_modules apps/*/node_modules apps/*/dist packages/*/node_modules
    rm -rf api/.venv api/.pytest_cache api/.ruff_cache
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
