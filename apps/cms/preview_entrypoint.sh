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
empty=$(run -At -c "SELECT to_regclass('django_migrations') IS NULL")
if [ "$empty" = t ]; then
    echo "Restoring the anonymised dump"
    # A first start cut short may have left its session, holding locks. This
    # also interrupts another container of this preview still restoring, which
    # then starts again.
    run -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = current_user AND pid <> pg_backend_pid()" > /dev/null
    # One transaction: all of it, or an empty database to restore again.
    pg_restore --no-owner --no-privileges --exit-on-error --single-transaction -d "$DATABASE_URL" /latest.dump
fi
# The dump sets a known password on protected pages and collections
# (infra/e2e-dump/rules.sql): on a public URL, nobody must know it. At every
# start, before anything is served: a start cut short after the restore.
run -c "UPDATE wagtailcore_pageviewrestriction SET password = gen_random_uuid() WHERE password = 'e2e'" \
    -c "UPDATE wagtailcore_collectionviewrestriction SET password = gen_random_uuid() WHERE password = 'e2e'"
# The migrations of the pull request.
python manage.py migrate --noinput
# Nobody of the dump can log in (their passwords are unusable): one account for
# the reviewers, whose password is generated for this preview
# (infra/envs/preview; read it with `just preview-admin-password <number>`).
# At every start: the password of the state wins over one changed in the admin.
python manage.py shell -c '
import os
from django.contrib.auth import get_user_model
user, _ = get_user_model().objects.get_or_create(
    username="preview", defaults={"email": "preview@example.test"}
)
user.is_staff = user.is_superuser = user.is_active = True
user.set_password(os.environ["PREVIEW_ADMIN_PASSWORD"])
user.save()
' > /dev/null
unset PREVIEW_ADMIN_PASSWORD # not for the served application
# The dump has no search index (built from raw content).
[ "$(run -At -c 'SELECT count(*) FROM wagtailsearch_indexentry')" != 0 ] || python manage.py update_index > /dev/null

exec ./entrypoint.sh
