#!/usr/bin/env bash
# Entrypoint of a preview (Dockerfile.preview): its database lives on the
# production instance, as a user that must only reach its own database.
set -euo pipefail

psql -q "$DATABASE_URL" -c 'SELECT 1' > /dev/null
# Same user, production database: Scaleway gives a new user no permission on
# it (infra/envs/preview). Never start a preview that proves otherwise.
if psql -q "$PRODUCTION_DATABASE_URL" -c 'SELECT 1' > /dev/null 2>&1; then
    echo "The preview user can connect to the production database: refusing to start." >&2
    exit 1
fi

# First start only: what the pull request changes in the database is then kept.
if [ "$(psql -At "$DATABASE_URL" -c "SELECT to_regclass('django_migrations') IS NULL")" = t ]; then
    echo "Restoring the anonymised dump"
    # One transaction: a restore cut short leaves the database empty, to redo.
    pg_restore --no-owner --no-privileges --exit-on-error --single-transaction -d "$DATABASE_URL" /latest.dump
    # The dump sets a known password on protected pages and collections
    # (infra/e2e-dump/rules.sql): on a public URL, nobody must know it.
    psql -q -v ON_ERROR_STOP=1 "$DATABASE_URL" \
        -c "UPDATE wagtailcore_pageviewrestriction SET password = gen_random_uuid() WHERE password <> ''" \
        -c "UPDATE wagtailcore_collectionviewrestriction SET password = gen_random_uuid() WHERE password <> ''"
    restored=1
fi
# The migrations of the pull request.
./manage_jobs.sh
# The dump has no search index (built from raw content).
[ -z "${restored:-}" ] || python manage.py update_index > /dev/null

exec ./entrypoint.sh
