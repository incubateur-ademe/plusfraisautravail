from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SitesConformesHeaderLogoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sites_conformes_header_logo"
    verbose_name = _("Header logo")
