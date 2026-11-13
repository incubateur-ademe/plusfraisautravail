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
# Idempotent: moves the update dates typed in the page bodies to the update date field,
# a no-op once none is left. After `migrate`, it needs the column. Drop this call once
# prod is done.
python manage.py move_update_dates_to_field
