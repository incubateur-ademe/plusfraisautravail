from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SitesConformesFooterPartnersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sites_conformes_footer_partners"
    verbose_name = _("Footer partners")
