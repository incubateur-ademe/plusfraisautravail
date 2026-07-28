import os

from .base import *  # noqa: F403

DEBUG = False

STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # noqa: F405
STORAGES["default"]["BACKEND"] = "storages.backends.s3.S3Storage"  # noqa: F405

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "")
# Bucket is public-read (see infra: object-bucket module's public_read=true
# for cms_media) so URLs can be stable instead of presigned. A presigned URL
# gets a new signature+timestamp on every render, so the browser never
# requests the same URL twice and Cache-Control can't produce a cache hit
# no matter how long max-age is.
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": os.environ.get("S3_CACHE_CONTROL", MEDIA_CACHE_CONTROL)}  # noqa: F405

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
