#!/usr/bin/env bash
# Restore the nightly anonymised dump of the CMS database, then run what a
# deploy runs, so the e2e tests start from production as it is (CI and local).
#
#   E2E_DATABASE_URL  target database, emptied first (default postgresql:///pfat_e2e)
#   E2E_DUMP_FILE     restore this file instead of downloading the latest dump
#
# The download needs read access to the private bucket: AWS_ACCESS_KEY_ID /
# AWS_SECRET_ACCESS_KEY, or the SCW_ACCESS_KEY / SCW_SECRET_KEY of .env.
set -euo pipefail

db_url="${E2E_DATABASE_URL:-postgresql:///pfat_e2e}"
# Guard: this script empties the target database.
db_name="$(psql -At "$db_url" -c 'SELECT current_database()')"
case "$db_name" in
    *e2e*) ;;
    *) echo "Refusing to empty '$db_name': the e2e database name must contain 'e2e'." >&2; exit 1 ;;
esac
# A pg_restore newer than the server (16, as in production) sends settings
# the server does not know.
server="$(psql -At "$db_url" -c 'SHOW server_version_num' | cut -c1-2)"
client="$(pg_restore --version | grep -oE '[0-9]+' | head -1)"
[ "$client" -le "$server" ] || { echo "pg_restore $client is newer than the server ($server): use the PostgreSQL $server client." >&2; exit 1; }
root="$(cd "$(dirname "$0")/.." && pwd)"
cache="$root/e2e/.cache"
dump="${E2E_DUMP_FILE:-$cache/latest.dump}"
src="s3://pfat-e2e-fixtures/cms"

if [ -z "${E2E_DUMP_FILE:-}" ]; then
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-${SCW_ACCESS_KEY:-}}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-${SCW_SECRET_KEY:-}}"
    export AWS_DEFAULT_REGION=fr-par AWS_ENDPOINT_URL=https://s3.fr-par.scw.cloud
    mkdir -p "$cache"
    remote_sha="$(aws s3 cp --only-show-errors "$src/latest.sha256" -)" || {
        echo "No anonymised dump at $src yet, or no read access to it." >&2
        echo "Run the 'E2E dump' workflow once, or restore a local file with E2E_DUMP_FILE=path." >&2
        exit 1
    }
    if [ "$(shasum -a 256 "$dump" 2>/dev/null | cut -d' ' -f1)" = "$remote_sha" ]; then
        echo "Dump already up to date ($dump)"
    else
        echo "Downloading the latest anonymised dump"
        aws s3 cp --only-show-errors "$src/latest.dump" "$dump"
        [ "$(shasum -a 256 "$dump" | cut -d' ' -f1)" = "$remote_sha" ] \
            || { echo "Checksum mismatch, the dump changed during the download: run again" >&2; exit 1; }
    fi
fi

echo "Restoring $dump"
# Empty schema rather than pg_restore --clean: tables left by another
# branch's migrations would otherwise survive and break `migrate`.
psql -q -v ON_ERROR_STOP=1 "$db_url" -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
pg_restore --no-owner --no-privileges --exit-on-error -d "$db_url" "$dump"

echo "Running the post-deploy steps"
cd "$root/apps/cms"
export DJANGO_SETTINGS_MODULE=cms.settings.e2e
uv run bash manage_jobs.sh
# The dump has no search index (built from raw content): rebuild it.
uv run python manage.py update_index > /dev/null
# The dump has no usable password: the tests log in as e2e / e2e.
DJANGO_SUPERUSER_PASSWORD=e2e uv run python manage.py createsuperuser \
    --noinput --username e2e --email e2e@example.test
# Wagtail routes by hostname: serve the production site on localhost.
psql -q -v ON_ERROR_STOP=1 "$db_url" \
    -c "UPDATE wagtailcore_site SET hostname = 'localhost', port = ${E2E_PORT:-8765} WHERE is_default_site"
echo "Ready: just e2e-serve"
