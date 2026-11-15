#!/usr/bin/env bash
# Entrypoint of a preview (Dockerfile.preview): its database lives on the
# production instance, as a user that must only reach its own database.
set -euo pipefail

# Same user, production database: Scaleway gives a new user no permission on
# it (infra/envs/preview). Start only on that very refusal: a successful
# connection, or any other failure, means the setup is not the expected one.
# A guard against a configuration error, not against the code of the pull
# request, which could remove it.
production_url=$PRODUCTION_DATABASE_URL
unset PRODUCTION_DATABASE_URL # not for Django
refusal=$(LC_ALL=C psql -q "$production_url" -c 'SELECT 1' 2>&1 > /dev/null || true)
case "$refusal" in
    *"permission denied for database"*) ;;
    *)
        echo "Refusing to start: the preview user must be denied the production database, got: ${refusal:-a connection}" >&2
        exit 1
        ;;
esac

run() { psql -q -v ON_ERROR_STOP=1 "$DATABASE_URL" "$@"; }

# First start only: what the pull request changes in the database is then kept.
if [ "$(run -At -c "SELECT to_regclass('django_migrations') IS NULL")" = t ]; then
    echo "Restoring the anonymised dump"
    # A first start cut short may have left its session, holding locks.
    run -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = current_user AND pid <> pg_backend_pid()" > /dev/null
    pg_restore --no-owner --no-privileges -f /tmp/seed.sql /latest.dump
    # The dump sets a known password on protected pages and collections
    # (infra/e2e-dump/rules.sql): on a public URL, nobody must know it. The
    # script of pg_restore empties the search path: schema-qualified names.
    cat >> /tmp/seed.sql <<'SQL'
UPDATE public.wagtailcore_pageviewrestriction SET password = gen_random_uuid() WHERE password <> '';
UPDATE public.wagtailcore_collectionviewrestriction SET password = gen_random_uuid() WHERE password <> '';
SQL
    # One transaction: all of it, or an empty database to seed again.
    run --single-transaction -f /tmp/seed.sql > /dev/null
    rm /tmp/seed.sql
fi
# The migrations of the pull request.
python manage.py migrate --noinput
# The dump has no search index (built from raw content).
[ "$(run -At -c 'SELECT count(*) FROM wagtailsearch_indexentry')" != 0 ] || python manage.py update_index > /dev/null

exec ./entrypoint.sh
