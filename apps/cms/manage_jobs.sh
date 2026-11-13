#!/usr/bin/env bash
# Run by the private cms-manage container (manage_server.py, POST /run), which
# cms.yml calls at each deploy, before the CMS rollout. Migrations run here, not in entrypoint.sh's
# boot path: entrypoint.sh must start gunicorn within the container's startup
# probe budget, and a slow migration risked the container being killed as
# "failed to start" even when the migration itself succeeded (see fea5b49).
set -euo pipefail

# No startup probe on this path: a request may last 30 min (infra/envs/prod).
python manage.py migrate --noinput
# Idempotent: the database table of the "pfat_api" cache (cms/settings/base.py).
python manage.py createcachetable
# The nightly e2e dump (infra/e2e-dump) reads with the e2e_dump role, whose
# Scaleway "readonly" privilege only covers the tables that existed when it
# was applied: grant the ones this deploy's migrations created.
python manage.py shell <<'PYTHON'
from django.db import connection

connection.cursor().execute("""
    DO $$ BEGIN
        IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'e2e_dump') THEN
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO e2e_dump;
            GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO e2e_dump;
        END IF;
    END $$
""")
PYTHON
