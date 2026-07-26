from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = "django-insecure-dev-only-key-do-not-use-in-production"

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.extend(["debug_toolbar"])  # noqa: F405

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
