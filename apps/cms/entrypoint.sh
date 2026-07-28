#!/usr/bin/env bash
# Container entrypoint. Migrations (migrate_from_sites_faciles, migrate) are
# run once, out-of-band via `manage.py` from CI or locally - not on every
# cold start. Running them inside the startup-probe-gated boot path meant a
# slow migration could exceed the probe budget and get the container killed
# before gunicorn ever started, even though the migration itself was fine.
set -euo pipefail

echo "Starting gunicorn..."
exec gunicorn cms.wsgi:application --bind 0.0.0.0:8080 --workers 2
