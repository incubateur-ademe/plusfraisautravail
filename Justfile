# plusfraisautravail — local dev commands
#
# Run `just` to list available recipes, or `just <recipe>` to run one.
# Requires: node 22+, uv, terraform, awscli (for bucket sync).

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
# Vite proxies /api/* → http://localhost:8080 — start `just api` in another terminal.
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

# Terraform fmt + validate (prod env).
tf-fmt:
    cd infra && terraform fmt -recursive

tf-validate:
    cd infra/envs/prod && terraform init -backend=false && terraform validate

# ── api container ────────────────────────────────────────────────────────

# Run the locally built API image (requires .env in api/).
run-api-container: build-api
    docker run --rm -p 8080:8080 --env-file api/.env pfat-api:local

# ── infra (terraform) ────────────────────────────────────────────────────

# Init the prod stack. Run once; needs SCW_* env vars set.
tf-init:
    cd infra/envs/prod && terraform init

# Plan the prod stack.
tf-plan:
    cd infra/envs/prod && terraform plan

# Apply the prod stack (interactive confirm).
tf-apply:
    cd infra/envs/prod && terraform apply

# ── housekeeping ─────────────────────────────────────────────────────────

# Remove all build/test caches and node_modules. Forces a fresh `just install`.
clean:
    rm -rf node_modules apps/*/node_modules apps/*/dist packages/*/node_modules
    rm -rf api/.venv api/.pytest_cache api/.ruff_cache
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
