import logging
import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.contrib.forms.models import FormSubmission

from .models import NotionContactSettings
from .notion import ContactFormData, create_new_row_in_notion_table

logger = logging.getLogger(__name__)

# Order matters: matches the Notion database's Nom / Email / Sujet / Message
# columns, and the field order documented on NotionContactSettings.form_page.
EXPECTED_FIELD_COUNT = 4


@receiver(post_save, sender=FormSubmission)
def sync_contact_form_to_notion(sender, instance, created, **kwargs):
    if not created:
        return

    settings_instance = NotionContactSettings.load()
    if not settings_instance.form_page_id or instance.page_id != settings_instance.form_page_id:
        return

    if not settings_instance.notion_database_id:
        logger.error("Notion contact sync is enabled but no database id is configured")
        return

    form_fields = instance.page.specific.get_form_fields()
    if len(form_fields) != EXPECTED_FIELD_COUNT:
        logger.error(
            "Notion contact sync: form page %s has %d fields, expected %d - skipping",
            instance.page_id,
            len(form_fields),
            EXPECTED_FIELD_COUNT,
        )
        return

    field_names = [field.clean_name for field in form_fields]
    form_data = instance.get_data()
    name, email, subject, message = (form_data.get(field_name) for field_name in field_names)

    data = ContactFormData(name=name, email=email, subject=subject, message=message)
    create_new_row_in_notion_table(
        token=os.environ.get("NOTION_TOKEN", ""),
        database_id=settings_instance.notion_database_id,
        data=data,
    )
