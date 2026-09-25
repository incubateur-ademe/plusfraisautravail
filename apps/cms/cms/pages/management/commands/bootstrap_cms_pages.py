"""One-off for a database that predates the ContentPage swap.

``migrate`` refuses to run there: sites_conformes_core's migrations now
depend on ``cms_pages.0001_initial`` (``swappable_dependency``) but were
applied before it existed, so Django raises InconsistentMigrationHistory.
Migration state can't even be rendered for that history, so this bypasses
it: create the two tables from the model classes (what ``--run-syncdb``
does for unmigrated apps) and record 0001 as applied. The regular
``migrate`` then passes and runs 0002 (data adoption).

No-op once 0001 is applied. Drop this command and its manage_jobs.sh line
after the prod deploy.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from cms.pages.models import ContentPage, TagContentPage

TARGET = ("cms_pages", "0001_initial")


class Command(BaseCommand):
    help = "Apply cms_pages.0001_initial on a DB that predates the ContentPage swap"

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        if TARGET in recorder.applied_migrations():
            self.stdout.write("cms_pages.0001_initial already applied - nothing to do")
            return
        with connection.schema_editor() as editor:
            editor.create_model(ContentPage)
            editor.create_model(TagContentPage)
        recorder.record_applied(*TARGET)
        self.stdout.write(self.style.SUCCESS("Applied cms_pages.0001_initial"))
