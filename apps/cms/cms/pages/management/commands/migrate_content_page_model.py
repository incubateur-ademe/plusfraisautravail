"""Move existing content pages from sites_conformes_core.ContentPage to the
swapped-in cms_pages.ContentPage, without copying a row.

Run once, by hand, before ``migrate`` on any database that predates the
swap (prod: 2026-09-28). Once SF_CONTENTPAGE_MODEL is set,
the core migrations depend on cms_pages.0001_initial, and Django refuses to
migrate a database where the former are applied and the latter is not.

Everything Wagtail keeps about a page's type goes through its content type
id (page rows, revisions, log entries, permissions, reference and search
indexes), and the page data lives in the concrete model's table. So adopting
the legacy pages is: rename the tables, relabel the content type, and
record the migration as applied. Idempotent: a no-op unless the
legacy table exists and the new one does not.
"""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from wagtail.models import Page


def adopt(command, legacy_app, page_model, related_models, migration):
    """Adopt the ``legacy_app`` tables of ``page_model`` and of its ``related_models``
    (through models), then record the cms_pages ``migration`` that would have created them."""
    model_name = page_model._meta.model_name
    tables = set(connection.introspection.table_names())
    # cms_pages keeps the upstream model names, so only the app prefix differs.
    legacy_tables = {
        model: model._meta.db_table.replace("cms_pages", legacy_app, 1)
        for model in [page_model, *related_models]
    }

    if page_model._meta.db_table in tables:
        command.stdout.write(f"cms_pages {model_name} tables already exist, nothing to do.")
        return
    if legacy_tables[page_model] not in tables:
        command.stdout.write(f"No legacy {model_name} table, nothing to do.")
        return

    with transaction.atomic(), connection.schema_editor(atomic=False) as editor:
        for model, legacy_table in legacy_tables.items():
            editor.alter_db_table(model, legacy_table, model._meta.db_table)

        # The running site may already have created the new content type
        # lazily (get_for_model on first use). It holds no pages: drop it so
        # the legacy row, which every page/revision/permission points at,
        # can take its label.
        stray = ContentType.objects.filter(app_label="cms_pages", model=model_name).first()
        if stray:
            if Page.objects.filter(content_type=stray).exists():
                raise CommandError(f"cms_pages.{model_name} already has pages, refusing.")
            stray.delete()
        relabelled = ContentType.objects.filter(app_label=legacy_app, model=model_name).update(
            app_label="cms_pages"
        )
        MigrationRecorder(connection).record_applied("cms_pages", migration)

    ContentType.objects.clear_cache()
    count = page_model.objects.count()
    command.stdout.write(
        command.style.SUCCESS(
            f"Adopted {count} {model_name} pages ({relabelled} content type relabelled)."
        )
    )


class Command(BaseCommand):
    help = "Adopt sites_conformes_core.ContentPage rows as cms_pages.ContentPage (idempotent)."

    def handle(self, *args, **options):
        adopt(
            self,
            "sites_conformes_core",
            apps.get_model("cms_pages", "ContentPage"),
            [apps.get_model("cms_pages", "TagContentPage")],
            "0001_initial",
        )
