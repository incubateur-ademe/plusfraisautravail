#!/usr/bin/env bash
set -euo pipefail

# Idempotent; Postgres DDL self-serializes concurrent migrate runs from
# multiple cold-starting replicas, so this is safe without a separate
# release-phase job (Scaleway Serverless Containers don't have one).
python manage.py migrate --noinput
exec gunicorn sites_conformes.wsgi:application --bind 0.0.0.0:8080 --workers 2
