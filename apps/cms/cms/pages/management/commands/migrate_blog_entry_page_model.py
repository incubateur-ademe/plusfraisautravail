"""Move existing blog entries from sites_conformes_blog.BlogEntryPage to the
swapped-in cms_pages.BlogEntryPage, without copying a row.

Same recipe as migrate_content_page_model. It must run before ``migrate`` on
any database that already holds blog entries: ``migrate`` would otherwise create
empty cms_pages tables, and the existing entries would keep pointing at a
model that is swapped out. Idempotent: a no-op unless the legacy table exists
and the new one does not.
"""

from django.apps import apps
from django.core.management.base import BaseCommand

from cms.pages.management.commands.migrate_content_page_model import adopt


class Command(BaseCommand):
    help = "Adopt sites_conformes_blog.BlogEntryPage rows as cms_pages.BlogEntryPage (idempotent)."

    def handle(self, *args, **options):
        page_model = apps.get_model("cms_pages", "BlogEntryPage")
        adopt(
            self,
            "sites_conformes_blog",
            page_model,
            [
                apps.get_model("cms_pages", "TagEntryPage"),
                apps.get_model("cms_pages", "CategoryEntryPage"),
                page_model.authors.through,
            ],
            "0002_blogentrypage",
        )
