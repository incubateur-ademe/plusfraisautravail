from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images import get_image_model_string


@register_setting(icon="site")
class HeaderLogoSettings(BaseSiteSetting):
    """Replaces the header's text service title with a logo image, when set.

    Not DSFR-conformant (the header's service title is meant to be text),
    but falls back to the standard text title when no logo is configured.
    """

    def clean(self):
        super().clean()
        if self.logo and not self.alt:
            raise ValidationError({"alt": _("Required when a logo is set.")})

    logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Logo"),
    )
    alt = models.CharField(
        _("Alt text"),
        max_length=200,
        blank=True,
        default="",
        help_text=_("Required if a logo is set. Must be the service's name."),
    )

    panels = [
        FieldPanel("logo"),
        FieldPanel("alt"),
    ]

    class Meta:
        verbose_name = _("Header logo")
