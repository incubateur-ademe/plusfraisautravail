#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for database..."
db_ready=0
for i in $(seq 1 30); do
  if python -c "
import django; django.setup()
from django.db import connection
connection.cursor().execute('SELECT 1')
  "; then
    echo "Database ready."
    db_ready=1
    break
  fi
  echo "  attempt $i/30..."
  sleep 2
done
if [ "$db_ready" -ne 1 ]; then
  echo "Database never became reachable - aborting." >&2
  exit 1
fi

echo "Running app label migration..."
python manage.py migrate_from_sites_faciles --no-input

echo "Applying Django migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn..."
exec gunicorn cms.wsgi:application --bind 0.0.0.0:8080 --workers 2
