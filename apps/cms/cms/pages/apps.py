from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms.pages"
    label = "cms_pages"
    verbose_name = "Pages"
