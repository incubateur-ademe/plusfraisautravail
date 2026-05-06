#!/usr/bin/env bash
set -euo pipefail

APP="sf-plusfraisautravail"

# Direction: "up" = local -> S3, "down" = S3 -> local
DIRECTION="${1:-}"
LOCAL_DIR="${2:-}"
DRY_RUN="${3---dryrun}"  # pass empty string as 3rd arg to actually run

if [[ -z "$DIRECTION" || -z "$LOCAL_DIR" ]]; then
  cat >&2 <<EOF
Usage: $0 <up|down> <local-dir> [--dryrun|""]

  up      sync local-dir  ->  s3
  down    sync s3         ->  local-dir
  3rd arg defaults to --dryrun. Pass "" to actually transfer.

Examples:
  $0 up   ./media                  # dry-run upload
  $0 up   ./media ""               # real upload
  $0 down ./media-from-prod ""     # real download
EOF
  exit 1
fi

# Pull S3 creds from Scalingo env (one call, parsed locally - no values printed)
echo "Fetching S3 credentials from Scalingo app: $APP ..."
ENV_DUMP="$(scalingo --app "$APP" env)"

get_var() {
  local name="$1"
  echo "$ENV_DUMP" | awk -F= -v k="$name" '$1==k { sub(/^[^=]+=/,""); print; exit }'
}

S3_HOST="$(get_var S3_HOST)"
S3_PROTOCOL="$(get_var S3_PROTOCOL)"
S3_BUCKET_NAME="$(get_var S3_BUCKET_NAME)"
S3_KEY_ID="$(get_var S3_KEY_ID)"
S3_KEY_SECRET="$(get_var S3_KEY_SECRET)"
S3_BUCKET_REGION="$(get_var S3_BUCKET_REGION)"
S3_LOCATION="$(get_var S3_LOCATION)"

: "${S3_PROTOCOL:=https}"

for v in S3_HOST S3_BUCKET_NAME S3_KEY_ID S3_KEY_SECRET S3_BUCKET_REGION; do
  if [[ -z "${!v}" ]]; then
    echo "ERROR: $v not set in Scalingo env." >&2
    exit 1
  fi
done

ENDPOINT="${S3_PROTOCOL}://${S3_HOST}"
S3_PATH="s3://${S3_BUCKET_NAME}"
if [[ -n "$S3_LOCATION" ]]; then
  S3_PATH="${S3_PATH}/${S3_LOCATION}"
fi

echo "Endpoint : $ENDPOINT"
echo "Region   : $S3_BUCKET_REGION"
echo "Bucket   : $S3_BUCKET_NAME"
echo "Prefix   : ${S3_LOCATION:-(none)}"
echo "Local    : $LOCAL_DIR"
echo "Mode     : ${DRY_RUN:-EXECUTE}"
echo

case "$DIRECTION" in
  up)   SRC="$LOCAL_DIR"; DST="$S3_PATH" ;;
  down) SRC="$S3_PATH";   DST="$LOCAL_DIR" ;;
  *)    echo "ERROR: direction must be 'up' or 'down'" >&2; exit 1 ;;
esac

AWS_ACCESS_KEY_ID="$S3_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$S3_KEY_SECRET" \
AWS_DEFAULT_REGION="$S3_BUCKET_REGION" \
aws s3 sync "$SRC" "$DST" \
  --endpoint-url "$ENDPOINT" \
  --exclude '.DS_Store' --exclude '*/.DS_Store' \
  --delete \
  ${DRY_RUN}
