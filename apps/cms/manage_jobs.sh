#!/usr/bin/env bash
# Entrypoint for the cms_manage Serverless Job. Scaleway Jobs' `command`
# field isn't run through a shell - it can't parse `&&`/`;` in a single
# string (confirmed via Scaleway's own troubleshooting docs, which point
# at Secret Manager script references for anything beyond one command).
# Baking the chain into the image instead avoids needing that.
set -euo pipefail

# Migrations run here, not in entrypoint.sh's boot path: entrypoint.sh must
# start gunicorn within the container's startup probe budget, and a slow
# migration risked the container being killed as "failed to start" even
# when the migration itself succeeded (see fea5b49). This job has no such
# time pressure (1800s timeout, no probe).
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
