"""The API's settings, read once from the ``PFAT_API`` dict of the Django settings."""

from types import SimpleNamespace

from django.conf import settings as django_settings

DEFAULTS = {
    "vigilance_app_id": None,
    "rte_client_id": None,
    "rte_client_secret": None,
    "rte_use_sandbox": False,
    "climadiag_api_url": "https://staging.plusfraichemaville.fr/api/external-search-climadiag-info",
    "climadiag_api_token": None,
    "cache_ttl_seconds": 3600,
    "cache_alias": "default",
}

settings = SimpleNamespace(**{**DEFAULTS, **getattr(django_settings, "PFAT_API", {})})
