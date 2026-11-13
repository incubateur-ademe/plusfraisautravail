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
# First, so that a job stopped here leaves the database as it found it: records core
# 0091_category_tree on a database that ran the chain it folded, does nothing when core
# never reached it, and stops on any other state. Drop this call once prod is done.
python manage.py record_core_category_tree
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
# Idempotent: moves the update dates typed in the page bodies to the update date field,
# a no-op once none is left. After `migrate`, it needs the column. Drop this call once
# prod is done.
python manage.py move_update_dates_to_field
# Idempotent: replaces the page tags by categories, a no-op once no page carries a mapped
# tag. After `migrate`, it needs the category tables. Drop this call once prod is done.
python manage.py seed_categories_from_tags
# python manage.py wagtail_update_image_renditions
# python manage.py set_s3_cache_control
