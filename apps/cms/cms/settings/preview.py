"""Preview of a pull request (infra/envs/preview): production settings on its
own database and bucket, without mail, Sentry, PostHog, Notion or API keys
(none of them is given to the container)."""

from .production import *  # noqa: F403
from .production import MIDDLEWARE


def noindex(get_response):
    """A public URL, posted on a public pull request."""

    def middleware(request):
        response = get_response(request)
        response["X-Robots-Tag"] = "noindex"
        return response

    return middleware


MIDDLEWARE = ["cms.settings.preview.noindex", *MIDDLEWARE]
# No Sentry here: a 500 leaves its traceback in the container logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR"}},
}
