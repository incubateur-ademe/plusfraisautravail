"""Move existing content pages from sites_conformes_core.ContentPage to the
swapped-in cms_pages.ContentPage, without copying a row.

Run before ``migrate`` (see manage_jobs.sh): once SF_CONTENTPAGE_MODEL is set,
the core migrations depend on cms_pages.0001_initial, and Django refuses to
migrate a database where the former are applied and the latter is not.

Everything Wagtail keeps about a page's type goes through its content type
id (page rows, revisions, log entries, permissions, reference and search
indexes), and the page data lives in the concrete model's table. So adopting
the legacy pages is: rename the two tables, relabel the content type, and
record the initial migration as applied. Idempotent: a no-op unless the
legacy table exists and the new one does not.
"""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from wagtail.models import Page

LEGACY_PAGE_TABLE = "sites_conformes_core_contentpage"
LEGACY_TAG_TABLE = "sites_conformes_core_tagcontentpage"


class Command(BaseCommand):
    help = "Adopt sites_conformes_core.ContentPage rows as cms_pages.ContentPage (idempotent)."

    def handle(self, *args, **options):
        page_model = apps.get_model("cms_pages", "ContentPage")
        tag_model = apps.get_model("cms_pages", "TagContentPage")
        legacy_tag_model = apps.get_model("sites_conformes_core", "TagContentPage")
        tables = set(connection.introspection.table_names())

        if page_model._meta.db_table in tables:
            self.stdout.write("cms_pages tables already exist, nothing to do.")
            return
        if LEGACY_PAGE_TABLE not in tables:
            self.stdout.write("No legacy content page table, nothing to do.")
            return

        with transaction.atomic(), connection.schema_editor(atomic=False) as editor:
            editor.alter_db_table(page_model, LEGACY_PAGE_TABLE, page_model._meta.db_table)
            editor.alter_db_table(tag_model, LEGACY_TAG_TABLE, tag_model._meta.db_table)
            # Upstream keeps a (now empty) TagContentPage pointing at the swapped-in
            # model, and modelcluster queries it on every page save. Recreate it.
            editor.create_model(legacy_tag_model)

            # The running site may already have created the new content type
            # lazily (get_for_model on first use). It holds no pages: drop it so
            # the legacy row, which every page/revision/permission points at,
            # can take its label.
            stray = ContentType.objects.filter(app_label="cms_pages", model="contentpage").first()
            if stray:
                if Page.objects.filter(content_type=stray).exists():
                    raise CommandError("cms_pages.contentpage already has pages, refusing.")
                stray.delete()
            relabelled = ContentType.objects.filter(
                app_label="sites_conformes_core", model="contentpage"
            ).update(app_label="cms_pages")
            MigrationRecorder(connection).record_applied("cms_pages", "0001_initial")

        ContentType.objects.clear_cache()
        count = page_model.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Adopted {count} content pages ({relabelled} content type relabelled)."
            )
        )
