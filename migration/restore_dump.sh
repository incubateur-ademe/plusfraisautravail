#!/usr/bin/env bash
set -euo pipefail

DUMP_TARBALL="20260428013222_sf_plus_fra_967.tar.gz"
APP="sf-plusfraisautravail"

if [[ -z "${SCALINGO_POSTGRESQL_URL:-}" ]]; then
  echo "ERROR: SCALINGO_POSTGRESQL_URL is not set in the environment." >&2
  exit 1
fi

if [[ ! -f "$DUMP_TARBALL" ]]; then
  echo "ERROR: $DUMP_TARBALL not found in $(pwd)" >&2
  exit 1
fi

# Parse URL components without echoing the password.
# Expected: postgres://USER:PASSWORD@HOST:PORT/DBNAME?params
URL="$SCALINGO_POSTGRESQL_URL"
proto_stripped="${URL#*://}"
userinfo="${proto_stripped%%@*}"
hostpart="${proto_stripped#*@}"
DB_USER="${userinfo%%:*}"
DB_PASSWORD="${userinfo#*:}"
hostport_db="${hostpart%%\?*}"
DB_NAME="${hostport_db##*/}"
hostport="${hostport_db%/*}"
REMOTE_HOST="${hostport%%:*}"
REMOTE_PORT="${hostport##*:}"

echo "Target app : $APP"
echo "Remote DB  : $DB_NAME @ $REMOTE_HOST:$REMOTE_PORT (user: $DB_USER)"
echo "Dump file  : $DUMP_TARBALL"
echo

# Extract dump
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"; [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true' EXIT

echo "Extracting tarball into $WORKDIR ..."
tar -xzf "$DUMP_TARBALL" -C "$WORKDIR"
DUMP_FILE="$(find "$WORKDIR" -type f \( -name '*.pgsql' -o -name '*.dump' \) | head -n1)"
if [[ -z "$DUMP_FILE" ]]; then
  echo "ERROR: no .pgsql/.dump file found in tarball." >&2
  ls -R "$WORKDIR" >&2
  exit 1
fi
echo "Dump file extracted: $(basename "$DUMP_FILE") ($(du -h "$DUMP_FILE" | cut -f1))"
echo

# Open tunnel in background, capture output to parse local port
TUNNEL_LOG="$WORKDIR/tunnel.log"
echo "Opening db-tunnel ..."
scalingo --app "$APP" db-tunnel -i "$HOME/.ssh/id_ed25519" SCALINGO_POSTGRESQL_URL > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# Wait for tunnel to print the local port (max ~30s)
LOCAL_PORT=""
for _ in $(seq 1 30); do
  if grep -qE '127\.0\.0\.1:[0-9]+' "$TUNNEL_LOG" 2>/dev/null; then
    LOCAL_PORT="$(grep -oE '127\.0\.0\.1:[0-9]+' "$TUNNEL_LOG" | head -n1 | cut -d: -f2)"
    break
  fi
  sleep 1
done

if [[ -z "$LOCAL_PORT" ]]; then
  echo "ERROR: could not detect tunnel local port. Tunnel log:" >&2
  cat "$TUNNEL_LOG" >&2
  exit 1
fi
echo "Tunnel up on 127.0.0.1:$LOCAL_PORT"
echo

# Run pg_restore
echo "Running pg_restore (--clean --if-exists, this WILL wipe target data) ..."
echo
PGPASSWORD="$DB_PASSWORD" pg_restore \
  --clean --if-exists \
  --no-owner --no-privileges \
  --no-comments \
  -h 127.0.0.1 -p "$LOCAL_PORT" \
  -U "$DB_USER" -d "$DB_NAME" \
  -j 4 \
  --verbose \
  "$DUMP_FILE" 2>&1 | tail -n 200

echo
echo "Done. Closing tunnel."
