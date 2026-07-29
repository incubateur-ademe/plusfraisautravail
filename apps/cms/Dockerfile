FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

# Build context is the repo root (see deploy-cms.yml / .dockerignore), not
# apps/cms - needed so the editable path dependencies in pyproject.toml's
# [tool.uv.sources] (../../packages/*) resolve to real files inside the
# build. WORKDIR mirrors apps/cms's real position in the repo so those
# relative paths land in the same place they do outside Docker.
WORKDIR /app/apps/cms

COPY apps/cms/pyproject.toml apps/cms/uv.lock* apps/cms/README.md ./
COPY packages /app/packages
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

COPY apps/cms/manage.py ./
COPY apps/cms/cms ./cms
RUN uv sync --frozen --no-dev || uv sync --no-dev

# collectstatic doesn't touch the DB, so a placeholder DATABASE_URL is fine -
# only DJANGO_SECRET_KEY and a syntactically valid DB URL are needed for
# Django to boot far enough to run the management command. Not a real
# secret and never copied into the runtime stage - docker linters flag any
# ENV named *SECRET* regardless of content, this one is a false positive.
ENV DJANGO_SECRET_KEY=build-time-placeholder \
    DATABASE_URL=sqlite:///build.sqlite3 \
    ALLOWED_HOSTS=[] \
    PATH="/app/apps/cms/.venv/bin:$PATH"
RUN python manage.py collectstatic --noinput

FROM python:3.12-slim AS runtime

# Printed by entrypoint.sh at boot so log lines can be traced back to the
# exact build, e.g. when comparing deployments while debugging.
ARG BUILD_SHA=unknown
ENV BUILD_SHA=${BUILD_SHA}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/apps/cms/.venv/bin:$PATH"

WORKDIR /app/apps/cms

COPY --from=builder /app /app
COPY apps/cms/entrypoint.sh apps/cms/manage_jobs.sh ./
RUN chmod +x entrypoint.sh manage_jobs.sh

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
