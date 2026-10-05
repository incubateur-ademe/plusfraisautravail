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
# Idempotent: no-op unless the DB still carries the legacy Sites Faciles schema.
python manage.py migrate_from_sites_faciles --no-input
# A database that predates the ContentPage swap needs
# `python manage.py migrate_content_page_model` here, before `migrate`.
# Prod is done (2026-09-28); the command and its tests stay for other DBs.
# Idempotent too: moves sites_conformes_blog.BlogEntryPage rows to the swapped-in
# cms_pages.BlogEntryPage. Must run before `migrate`, which would otherwise create
# empty cms_pages tables and orphan the existing blog entries. Drop this call
# once prod is done, as for the content pages.
python manage.py migrate_blog_entry_page_model
python manage.py migrate --noinput
# python manage.py wagtail_update_image_renditions
# python manage.py set_s3_cache_control
