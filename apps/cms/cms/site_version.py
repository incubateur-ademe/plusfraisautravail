"""ETag revalidation of public pages against one site-wide version.

sites-conformes' PublicCacheMiddleware lets the nginx proxy and browsers keep a
public page for SF_PUBLIC_CACHE_MAX_AGE seconds. When that expires they send
the ETag back (If-None-Match); while the site has not changed, this middleware
answers 304 before any routing or rendering, with two small queries.

A page shows more than itself (menus, footer, FAQ snippets, the cards of child
pages), so the version covers the whole site: the last action logged by the
Wagtail admin (pages, snippets, images, documents, settings), today's date (for
date-dependent listings) and the build (templates and code). Any of them
changing invalidates every page at once.

Not covered: the alert API, which serves outside data on its own lifetime.
"""

import hashlib
import os

from django.conf import settings
from django.db.models import Max
from django.http import HttpResponseNotModified
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.utils.http import parse_etags, quote_etag
from wagtail.models import ModelLogEntry, PageLogEntry


def site_version() -> str:
    latest = [
        PageLogEntry.objects.aggregate(latest=Max("timestamp"))["latest"],
        ModelLogEntry.objects.aggregate(latest=Max("timestamp"))["latest"],
    ]
    parts = [
        os.environ.get("BUILD_SHA", ""),
        timezone.localdate().isoformat(),
        max((t for t in latest if t), default=""),
    ]
    return hashlib.md5(str(parts).encode(), usedforsecurity=False).hexdigest()


class SiteVersionMiddleware:
    """Must come first in MIDDLEWARE, before PublicCacheMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_prefixes = (
            "/api/",
            settings.STATIC_URL,
            "/" + settings.WAGTAILADMIN_PATH,
        )

    def __call__(self, request):
        if not self._applies(request):
            return self.get_response(request)

        etag = quote_etag(site_version())
        if etag in parse_etags(request.headers.get("If-None-Match", "")):
            response = HttpResponseNotModified()
            response["ETag"] = etag
            # The 304 renews the cached copy for another lifetime.
            patch_cache_control(response, public=True, max_age=settings.SF_PUBLIC_CACHE_MAX_AGE)
            return response

        response = self.get_response(request)
        # Only on what PublicCacheMiddleware made public: never a page with a
        # form (CSRF cookie) or for a logged-in user.
        if (
            response.status_code == 200
            and "public" in response.get("Cache-Control", "")
            and not response.has_header("ETag")
        ):
            response["ETag"] = etag
        return response

    def _applies(self, request) -> bool:
        return (
            request.method in ("GET", "HEAD")
            and settings.SESSION_COOKIE_NAME not in request.COOKIES
            and not request.path.startswith(self.excluded_prefixes)
        )
