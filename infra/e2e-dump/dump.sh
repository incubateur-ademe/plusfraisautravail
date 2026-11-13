#!/usr/bin/env bash
# Nightly e2e fixture, run by server.py (POST /run) in the private e2e-dump
# container (infra/envs/prod): dump the CMS database with a read-only user over
# the Private Network, anonymise it in a throwaway Postgres inside this
# container, then upload ONLY the anonymised dump. The raw data never leaves
# the container: the throwaway Postgres and every file are deleted after each run.
# Progress goes to stdout (returned to the caller), errors to stderr (container
# logs only).
set -euo pipefail

: "${SOURCE_DATABASE_URL:?read-only DSN of the CMS database}"
: "${E2E_DUMP_PREFIX:?destination prefix, e.g. s3://pfat-e2e-fixtures/cms}"

here="$(cd "$(dirname "$0")" && pwd)"
# Not /tmp: on Serverless Containers it can be held in memory, and count
# against the memory limit instead of the local storage.
work=/var/lib/e2e-dump
pgdata=$work/pgdata
out=$work/latest.dump
# Local throwaway server: unix socket only, trust auth. Masking runs as the
# postgres superuser, which anon refuses by default (anon.nosuperuser): fine
# here, nobody else can reach this server.
export PGHOST=/var/run/postgresql PGUSER=postgres PGDATABASE=e2e
psql() { command psql -v ON_ERROR_STOP=1 -q "$@"; }

# The container instance may serve several runs.
cleanup() {
    gosu postgres pg_ctl -D "$pgdata" -m immediate -s stop 2>/dev/null || true
    rm -rf "$work"
}
cleanup
trap cleanup EXIT
# Errors of the steps that handle raw data can quote a row (COPY context,
# constraint details): keep them out of the logs, print only the first
# line of each error (psql puts the row on the DETAIL line).
quietly() {
    "$@" 2>"$work/step.err" || {
        echo "Step failed: $1" >&2
        grep -i 'error' "$work/step.err" | grep -vE '^(DETAIL|CONTEXT|LINE|HINT)' | cut -c1-160 >&2 || true
        exit 1
    }
}

echo "Starting a local Postgres"
mkdir -p "$pgdata" "$PGHOST" && chown postgres "$work" "$pgdata" "$PGHOST"
gosu postgres initdb -D "$pgdata" --auth=trust >/dev/null
# Server log in a file, not the container logs: it quotes failing statements.
gosu postgres pg_ctl -D "$pgdata" -l "$work/postgres.log" -w -s start -o "-c listen_addresses='' -c shared_preload_libraries=anon -c anon.nosuperuser=off"
createdb e2e
# The dump (--schema=public) creates the schema itself.
psql -c 'DROP SCHEMA public'

echo "Copying the CMS database (rows of excluded tables stay in production)"
excludes=()
while read -r table; do
    [[ -z "$table" || "$table" == \#* ]] || excludes+=("--exclude-table-data=$table")
done < "$here/excluded-tables.txt"
quietly bash -o pipefail -c '
    pg_dump -Fc --schema=public --no-owner --no-privileges "${@:2}" "$1" \
        | pg_restore --no-owner --no-privileges --exit-on-error -d e2e
' _ "$SOURCE_DATABASE_URL" "${excludes[@]}"

echo "Anonymising"
psql -c 'CREATE EXTENSION anon CASCADE'
psql -f "$here/rules.sql"

echo "Checking that rules.sql declares every column of the production schema"
# Same list as the CI test, but on the schema actually deployed: a column
# added by a migration and missing from rules.sql stops here, unmasked data
# never gets out.
# Files, not process substitutions: a failing query must stop the run.
# pg_dump patterns (wagtail_localize_*) turned into regexes.
excluded_tables="$(grep -vE '^(#|$)' "$here/excluded-tables.txt" | sed 's/\*/[a-z0-9_]*/g' | paste -sd'|' -)"
psql -At -f "$here/columns-to-declare.sql" > "$work/columns.all"
{ grep -vE "^(${excluded_tables})\." "$work/columns.all" || true; } | LC_ALL=C sort > "$work/columns.to-declare"
psql -At -c "SELECT c.relname || '.' || a.attname FROM pg_seclabel s
    JOIN pg_class c ON c.oid = s.objoid
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = s.objsubid
    WHERE s.provider = 'anon' AND s.classoid = 'pg_class'::regclass" | LC_ALL=C sort > "$work/columns.declared"
[ -s "$work/columns.to-declare" ] || { echo "No column found: wrong database?" >&2; exit 1; }
undeclared="$(LC_ALL=C comm -23 "$work/columns.to-declare" "$work/columns.declared")"
if [ -n "$undeclared" ]; then
    echo "Columns missing from rules.sql, nothing uploaded:" >&2
    echo "$undeclared" >&2
    exit 1
fi

quietly psql -c 'SELECT anon.anonymize_database()' > /dev/null
psql -c 'DROP EXTENSION anon CASCADE' -c 'DROP SCHEMA e2e_masks CASCADE'
PGOPTIONS="-c e2e.excluded_tables=$excluded_tables" psql -f "$here/check.sql"

echo "Uploading the anonymised dump to $E2E_DUMP_PREFIX"
pg_dump -Fc --no-owner --no-privileges --no-security-labels -f "$out" e2e
sha256sum "$out" | cut -d' ' -f1 > "$out.sha256"
# Dump first, checksum last: a new checksum means a complete new dump.
aws s3 cp --only-show-errors "$out" "$E2E_DUMP_PREFIX/latest.dump"
aws s3 cp --only-show-errors "$out.sha256" "$E2E_DUMP_PREFIX/latest.sha256"
echo "Done ($(du -h "$out" | cut -f1))"
