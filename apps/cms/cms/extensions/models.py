from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images import get_image_model_string
from wagtail.models import Orderable


@register_setting(icon="site")
class FooterPartnersSettings(ClusterableModel, BaseSiteSetting):
    """Sitewide "ils nous soutiennent" partner logos, rendered in the footer
    of every page (DSFR fr-footer__partners block)."""

    def clean(self):
        super().clean()
        if self.main_partner_logo and not self.main_partner_alt:
            raise ValidationError(
                {"main_partner_alt": _("Required when a main partner logo is set.")}
            )

    title = models.CharField(
        _("Title"),
        max_length=200,
        default="",
        blank=True,
        help_text=_('Example: "Ce site est développé et financé par" or "Ils nous soutiennent".'),
    )

    main_partner_logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Main partner logo"),
    )
    main_partner_alt = models.CharField(
        _("Main partner logo alt text"),
        max_length=200,
        blank=True,
        default="",
        help_text=_("Required if a main partner logo is set. Must be the partner's name."),
    )
    main_partner_url = models.URLField(
        _("Main partner link"),
        max_length=2000,
        blank=True,
        default="",
    )

    logo_height = models.DecimalField(
        _("Logo height (rem)"),
        max_digits=4,
        decimal_places=3,
        default="5.625",
        help_text=_("Applied to every logo for a uniform height, as recommended by the DSFR."),
    )

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(
            [
                FieldPanel("main_partner_logo"),
                FieldPanel("main_partner_alt"),
                FieldPanel("main_partner_url"),
            ],
            heading=_("Main partner"),
        ),
        InlinePanel("sub_partners", label=_("Other partners")),
        FieldPanel("logo_height"),
    ]

    class Meta:
        verbose_name = _("Footer partners")


class PartnerLogo(Orderable):
    settings = ParentalKey(
        FooterPartnersSettings, on_delete=models.CASCADE, related_name="sub_partners"
    )

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
        help_text=_("Must be the partner's name."),
    )
    url = models.URLField(
        _("Link"),
        max_length=2000,
        blank=True,
        default="",
    )

    panels = [
        FieldPanel("logo"),
        FieldPanel("alt"),
        FieldPanel("url"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = _("Partner logo")
        verbose_name_plural = _("Partner logos")
