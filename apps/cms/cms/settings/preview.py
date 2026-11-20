"""Preview of a pull request (infra/envs/preview): production settings on its
own database, without mail, Sentry, PostHog, Notion, API or bucket keys (none
of them is given to the container)."""

from .production import *  # noqa: F403
from .production import DATABASES, MIDDLEWARE, STORAGES

# Media in the preview's database, production's read from its public URL (cms/preview.py).
STORAGES = {
    **STORAGES,
    "default": {
        "BACKEND": "cms.preview.PreviewStorage",
        "OPTIONS": {"production_url": "https://plusfraisautravail.beta.gouv.fr/media/"},
    },
}


def noindex(get_response):
    """A public URL, posted on a public pull request."""

    def middleware(request):
        response = get_response(request)
        response["X-Robots-Tag"] = "noindex"
        return response

    return middleware


MIDDLEWARE = ["cms.settings.preview.noindex", *MIDDLEWARE]
# The instance is production's: hold none of its connections between requests.
DATABASES["default"]["CONN_MAX_AGE"] = 0
# No Sentry here: a 500 leaves its traceback in the container logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR"}},
}
