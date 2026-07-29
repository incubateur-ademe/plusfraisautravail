from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SitesConformesRgaaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sites_conformes_rgaa"
    verbose_name = _("RGAA accessibility helpers")

    def ready(self):
        from . import publish_hook  # noqa: F401
