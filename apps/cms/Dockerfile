FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

COPY manage.py ./
COPY sites_conformes ./sites_conformes
RUN uv sync --frozen --no-dev || uv sync --no-dev

# collectstatic doesn't touch the DB, so a placeholder DATABASE_URL is fine -
# only DJANGO_SECRET_KEY and a syntactically valid DB URL are needed for
# Django to boot far enough to run the management command. Not a real
# secret and never copied into the runtime stage - docker linters flag any
# ENV named *SECRET* regardless of content, this one is a false positive.
ENV DJANGO_SECRET_KEY=build-time-placeholder \
    DATABASE_URL=sqlite:///build.sqlite3 \
    ALLOWED_HOSTS=[] \
    PATH="/app/.venv/bin:$PATH"
RUN python manage.py collectstatic --noinput

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Django handles user-uploaded media - run as non-root, unlike api/Dockerfile
# which has no comparable file-handling surface.
RUN useradd --system --create-home cms

COPY --from=builder /app /app
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh && chown -R cms:cms /app

USER cms

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
