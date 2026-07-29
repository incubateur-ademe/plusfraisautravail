import json
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent

# Cache-Control header applied to media served/uploaded via S3.
# Ported from sites-conformes PR #537 (not yet released upstream).
# 1 day, not 1 year+immutable: Wagtail can overwrite an existing image's file
# in place on re-upload without changing its filename, so a very long-lived
# immutable cache risks serving stale content after an editor swaps an image.
MEDIA_CACHE_CONTROL = os.environ.get("MEDIA_CACHE_CONTROL", "public, max-age=86400")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = json.loads(os.environ.get("ALLOWED_HOSTS", "[]"))
# Matches upstream sites-conformes' default (opt-in via env var, not
# force-enabled) - Scaleway's proxy layer hasn't been confirmed to set
# X-Forwarded-Host correctly, so don't trust it until verified.
USE_X_FORWARDED_HOST = os.environ.get("USE_X_FORWARDED_HOST", "false").lower() == "true"

# sites_conformes' {% root_url %} tag reads this directly (defaults to Django's
# None when unset), so header/footer home links rendered "None/" without it.
FORCE_SCRIPT_NAME = ""

INSTALLED_APPS = [
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "cms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PROJECT_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cms.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(default=os.environ.get("DATABASE_URL", "")),
}
CONN_HEALTH_CHECKS = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    PROJECT_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

WAGTAIL_SITE_NAME = "Plus Frais Au Travail"
WAGTAILADMIN_BASE_URL = "http://example.com"
WAGTAILDOCS_EXTENSIONS = [
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Matches upstream sites-conformes' default admin path.
WAGTAILADMIN_PATH = "cms-admin/"
WAGTAIL_I18N_ENABLED = True

# Upstream disables this by default too: "They can clash with Whitenoise and
# are normally not useful as we serve the statics from a trusted source."
# Confirmed independently here - django-dsfr 3.5.2's bundled
# dsfr.min.css/utility.min.css don't match the SHA-384 hashes hardcoded in
# its own checksums.py, so browsers silently blocked all DSFR styling on
# integrity mismatch with no server-side error.
DSFR_USE_INTEGRITY_CHECKSUMS = False

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# wagtail.contrib.settings' context processor supplies the `settings`
# template variable that sites_conformes' header/footer overrides read
# CmsDsfrConfig from (site title, tagline, logo, etc.) - without it those
# all silently render empty instead of raising, which is why the header
# logo was missing and text fell back to whatever hardcoded English strings
# exist in the DSFR/sites_conformes templates rather than the DB-configured
# French content.
TEMPLATES[0]["OPTIONS"]["context_processors"].extend(
    [
        "wagtail.contrib.settings.context_processors.settings",
        "wagtailmenus.context_processors.wagtailmenus",
        "sites_conformes.core.context_processors.skiplinks",
        "sites_conformes.core.context_processors.mega_menus",
    ]
)

INSTALLED_APPS.extend(
    [
        "dsfr",
        # Override sites_conformes_core/blocks/footer.html and header.html - must come
        # before "sites_conformes" (which ships those same template paths) so Django's
        # app_directories loader (first INSTALLED_APPS match wins) picks these
        # templates over the upstream ones.
        "sites_conformes_footer_partners",
        "sites_conformes_header_logo",
        "sites_conformes_posthog",
        "sites_conformes",
        "sites_conformes.blog",
        "sites_conformes.core",
        "sites_conformes.events",
        "sites_conformes.forms",
        "sites_conformes.menus",
        "wagtail.contrib.settings",
        "wagtail.contrib.typed_table_block",
        "wagtail.contrib.routable_page",
        "wagtail_modeladmin",
        "wagtail_honeypot",
        "wagtailmenus",
        "wagtailmarkdown",
        "sites_conformes.proconnect",
        "cms.media_tools",
        "wagtail_notion_form",
        "sites_conformes_rgaa",
    ]
)

HOST_URL = "localhost"
HOST_PROTO = "http"
PROCONNECT_ACTIVATED = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Matches upstream sites-conformes' pattern of deriving CSRF_TRUSTED_ORIGINS
# from ALLOWED_HOSTS. Skipped while ALLOWED_HOSTS is the "*" wildcard (see
# TODO in .github/workflows/terraform-apply.yml) since "*" isn't a valid
# origin and Django requires a scheme+host per entry.
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ("*", "127.0.0.1", "localhost")
]
