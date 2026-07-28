"""Backfill Cache-Control headers on existing S3 media objects.

Ported from sites-conformes PR #537 (not yet released), adapted to this
project's AWS_* S3 settings instead of upstream's S3_* env vars.

Usage::

    python manage.py set_s3_cache_control --dry-run
    python manage.py set_s3_cache_control
"""

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Set Cache-Control headers on all existing S3 media objects."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--cache-control", default="")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        header_value = options["cache_control"] or getattr(
            settings, "MEDIA_CACHE_CONTROL", "public, max-age=3600"
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        if not bucket:
            raise CommandError("AWS_STORAGE_BUCKET_NAME is not configured.")

        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME or None,
        )

        self.stdout.write(f"S3 bucket: {bucket}")
        self.stdout.write(f"Cache-Control value: {header_value}")
        self.stdout.write("")

        updated = skipped = errors = 0
        paginator = client.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    try:
                        head = client.head_object(Bucket=bucket, Key=key)
                    except ClientError as e:
                        errors += 1
                        self.stderr.write(self.style.ERROR(f"  Error reading {key}: {e}"))
                        continue

                    if head.get("CacheControl", "") == header_value:
                        skipped += 1
                        continue

                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] Would update: {key}")
                        updated += 1
                        continue

                    try:
                        client.copy_object(
                            Bucket=bucket,
                            Key=key,
                            CopySource={"Bucket": bucket, "Key": key},
                            MetadataDirective="REPLACE",
                            CacheControl=header_value,
                            ContentType=head.get("ContentType", "application/octet-stream"),
                        )
                        updated += 1
                        self.stdout.write(f"  Updated: {key}")
                    except ClientError as e:
                        errors += 1
                        self.stderr.write(self.style.ERROR(f"  Error updating {key}: {e}"))
        except ClientError as e:
            raise CommandError(f"Failed to list objects: {e}") from e

        self.stdout.write("")
        prefix = "[DRY RUN] Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {updated} object(s), {skipped} already correct, {errors} error(s)."
            )
        )
