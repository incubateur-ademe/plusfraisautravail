# sites-conformes CMS

Django app deployed as `apps/cms` (Scaleway Serverless Container `cms-prod`). See `/DEPLOY.md` at the repo root for infra and deploy details.

## Local dev

```bash
cp .env.example .env
uv sync --extra dev
uv run python manage.py migrate
uv run python manage.py runserver 8080
```

## Tests

```bash
uv run ruff check .
uv run pytest
```
