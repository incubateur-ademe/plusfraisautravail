from django.apps import AppConfig


class WagtailNotionContactConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_notion_contact"
    verbose_name = "Notion contact sync"

    def ready(self):
        from . import signals  # noqa: F401
