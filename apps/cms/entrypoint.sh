#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for database..."
set +e
for i in $(seq 1 30); do
  if python -c "
import django; django.setup()
from django.db import connection
connection.cursor().execute('SELECT 1')
" 2>/dev/null; then
    echo "Database is ready."
    break
  fi
  echo "  attempt $i/30..."
  sleep 2
done
set -e

python manage.py migrate --noinput || true

exec gunicorn cms.wsgi:application --bind 0.0.0.0:8080 --workers 2
