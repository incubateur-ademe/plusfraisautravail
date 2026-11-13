"""Settings for the e2e tests (e2e/restore.sh, `just e2e-serve`).

Production-like (DEBUG off, real templates and error pages) on a local
database restored from the nightly anonymised dump. No S3, Sentry or
PostHog; media and third-party calls are stubbed by Playwright.
"""

import os

# base.py derives ALLOWED_HOSTS, CSRF origins and absolute URLs from these:
# set them before importing it.
_port = os.environ.get("E2E_PORT", "8765")
os.environ.setdefault("DJANGO_SECRET_KEY", "e2e-only")
# Never the DATABASE_URL of .env: restore.sh empties this database.
os.environ["DATABASE_URL"] = os.environ.get("E2E_DATABASE_URL", "postgresql:///pfat_e2e")
os.environ["ALLOWED_HOSTS"] = '["localhost", "127.0.0.1"]'
os.environ["WAGTAILADMIN_BASE_URL"] = f"http://localhost:{_port}"
# Empty rather than unset: base.py runs load_dotenv(), which would refill an
# unset variable from .env (and send the test errors to production Sentry).
os.environ["SENTRY_DSN"] = ""

from .base import *  # noqa: E402, F403

DEBUG = False
# Serve static files from the apps' static dirs, no collectstatic needed.
WHITENOISE_USE_FINDERS = True
POSTHOG_KEY = ""
