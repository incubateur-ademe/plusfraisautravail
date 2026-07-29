from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SitesConformesPosthogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sites_conformes_posthog"
    verbose_name = _("PostHog identification")
