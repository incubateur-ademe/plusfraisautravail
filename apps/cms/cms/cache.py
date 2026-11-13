"""Shared-cache headers for public pages, after torchbox.com (tbx/core/utils/cache.py).

Public responses get `Cache-Control: public, s-maxage=…, stale-while-revalidate=…`,
which the nginx proxy (infra/scalingo-proxy) honours: it serves the page from its
cache for s-maxage seconds, then a stale copy while it refreshes in the background.
`s-maxage` only applies to shared caches, so browsers still revalidate each time.

There is no purge on publish: a published change shows within s-maxage seconds.
Logged-in editors never see a cached page (the proxy bypasses its cache for them).
"""

from functools import wraps

from django.conf import settings
from django.utils.cache import add_never_cache_headers, patch_cache_control


def add_public_cache_headers(response):
    # Errors and redirects keep whatever they had: only a rendered page is shared.
    if response.status_code != 200:
        return response
    patch_cache_control(
        response,
        public=True,
        s_maxage=settings.CACHE_CONTROL_S_MAXAGE,
        stale_while_revalidate=settings.CACHE_CONTROL_STALE_WHILE_REVALIDATE,
    )
    return response


def public_cache(func):
    """Decorate a view, or a method returning a response such as Page.serve."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return add_public_cache_headers(func(*args, **kwargs))

    return wrapper


class PrivateResponseMiddleware:
    """Never share a response that is personal to its viewer.

    A logged-in user's page carries their identity (Wagtail userbar, PostHog
    identify), and a page with a form carries the viewer's CSRF token. Must sit
    after CsrfViewMiddleware in MIDDLEWARE, so it reads the CSRF flag before
    that middleware resets it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        is_personal = (user is not None and user.is_authenticated) or request.META.get(
            "CSRF_COOKIE_NEEDS_UPDATE"
        )
        if is_personal and "public" in response.get("Cache-Control", ""):
            del response["Cache-Control"]
            add_never_cache_headers(response)
        return response
