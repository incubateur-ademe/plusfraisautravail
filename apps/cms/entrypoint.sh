#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for database..."
for i in $(seq 1 30); do
  if python -c "
import django; django.setup()
from django.db import connection
connection.cursor().execute('SELECT 1')
  " 2>/dev/null; then
    echo "Database ready."
    break
  fi
  echo "  attempt $i/30..."
  sleep 2
done

echo "Checking if database needs initial restore..."
NEEDS_RESTORE=0
python -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_user')\")
if not cursor.fetchone()[0]:
    exit(1)
" 2>/dev/null || NEEDS_RESTORE=1

if [ "$NEEDS_RESTORE" -eq 1 ]; then
  echo "Empty database — downloading dump..."
  python -c "
import boto3, os, tarfile, glob
s3 = boto3.client('s3',
  endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
  region_name=os.environ['AWS_S3_REGION_NAME'],
)
s3.download_file(
  os.environ['AWS_STORAGE_BUCKET_NAME'],
  'migration/20260726013540_sf_plusfrai_2200.tar.gz',
  '/tmp/dump.tar.gz',
)
with tarfile.open('/tmp/dump.tar.gz', 'r:gz') as tar:
    tar.extractall('/tmp/')
dump_file = glob.glob('/tmp/*.pgsql')[0]
with open('/tmp/dump_path.txt', 'w') as f:
    f.write(dump_file)
"
  DUMP_FILE=$(cat /tmp/dump_path.txt)
  echo "Restoring database from $DUMP_FILE..."
  pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" "$DUMP_FILE"
  rm -f /tmp/dump.tar.gz /tmp/dump_path.txt "$DUMP_FILE"
  echo "Restore complete."
fi

echo "Running app label migration..."
python manage.py migrate_from_sites_faciles --no-input

echo "Applying Django migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn..."
exec gunicorn cms.wsgi:application --bind 0.0.0.0:8080 --workers 2
