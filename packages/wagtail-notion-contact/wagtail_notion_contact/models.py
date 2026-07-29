from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting


@register_setting(icon="mail")
class NotionContactSettings(BaseGenericSetting):
    """Picks which contact FormPage's submissions get synced to Notion.

    The form must have exactly 4 fields, in this order: name, email,
    subject, message - matching the Notion database columns Nom / Email /
    Sujet / Message.
    """

    form_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Contact form page"),
        help_text=_(
            "The form page to sync. Must have exactly 4 fields, in this order: "
            "name, email, subject, message."
        ),
    )

    notion_database_id = models.CharField(
        _("Notion database ID"),
        max_length=100,
        blank=True,
        default="",
        help_text=_("The UUID found in the Notion database's URL. Share it with your integration."),
    )

    panels = [
        HelpPanel(
            content=_(
                "Requires the NOTION_TOKEN environment variable to be set to a "
                "Notion internal integration token."
            )
        ),
        FieldPanel("form_page"),
        FieldPanel("notion_database_id"),
    ]

    class Meta:
        verbose_name = _("Notion contact sync")
