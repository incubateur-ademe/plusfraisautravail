import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import MEDIA_CACHE_CONTROL, STORAGES, WAGTAILADMIN_BASE_URL

# ponytail: base.py already reads DEBUG from env; removed the hardcoded
# False here so it can be flipped on prod (DEBUG=true) without a redeploy.

STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STORAGES["default"]["BACKEND"] = "storages.backends.s3.S3Storage"

# TLS terminates at the Scalingo proxy / Scaleway ingress; both forward the
# scheme in X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "")
# Media URLs are plain https://<site>/media/<key>: the bucket is public-read
# (infra: object-bucket public_read) and the Scalingo nginx proxy serves and
# caches /media/ from it. No signature, so browsers and nginx can cache.
# Override AWS_S3_CUSTOM_DOMAIN with the bucket host
# (pfat-cms-media.s3.fr-par.scw.cloud) to bypass the proxy, e.g. before the
# DNS cutover.
AWS_QUERYSTRING_AUTH = False
_site_host = urlsplit(WAGTAILADMIN_BASE_URL).netloc
if not _site_host:
    raise ImproperlyConfigured(
        f"WAGTAILADMIN_BASE_URL must be an absolute URL, got {WAGTAILADMIN_BASE_URL!r}"
    )
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", f"{_site_host}/media")
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": os.environ.get("S3_CACHE_CONTROL", MEDIA_CACHE_CONTROL)}

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
