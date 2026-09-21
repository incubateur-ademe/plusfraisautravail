"""migrate_content_page_model adopts legacy sites_conformes_core.ContentPage
rows as cms_pages.ContentPage. The test rebuilds the legacy state on the
fresh test database (tables renamed back, content type relabelled, migration
record removed), then runs the command and checks the pages come back
untouched and the migration history is consistent again."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from wagtail.models import Page, Site

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


def make_legacy_state(page):
    """Put the database back the way a pre-swap deployment left it."""
    with connection.cursor() as cur:
        cur.execute("DROP TABLE sites_conformes_core_tagcontentpage")
        # Upstream's migrations do not flag the historical model as swappable,
        # so a fresh database also carries this empty table.
        cur.execute("DROP TABLE sites_conformes_core_contentpage")
        cur.execute(
            "ALTER TABLE cms_pages_tagcontentpage RENAME TO sites_conformes_core_tagcontentpage"
        )
        cur.execute("ALTER TABLE cms_pages_contentpage RENAME TO sites_conformes_core_contentpage")
    # A fresh database also gets a content type for the swapped-out model.
    ContentType.objects.filter(app_label="sites_conformes_core", model="contentpage").delete()
    ContentType.objects.filter(app_label="cms_pages", model="contentpage").update(
        app_label="sites_conformes_core"
    )
    ContentType.objects.clear_cache()
    MigrationRecorder.Migration.objects.filter(app="cms_pages", name="0001_initial").delete()


@pytest.fixture
def legacy_page():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Page héritée", slug="page-heritee")
    page.tags.add("chaleur")
    root.add_child(instance=page)
    page.save_revision().publish()
    make_legacy_state(page)
    return page


def test_history_is_inconsistent_before_and_consistent_after(legacy_page):
    with pytest.raises(Exception, match="cms_pages.0001_initial"):
        MigrationLoader(connection).check_consistent_history(connection)

    call_command("migrate_content_page_model")

    MigrationLoader(connection).check_consistent_history(connection)


def test_pages_tags_and_revisions_survive(legacy_page):
    call_command("migrate_content_page_model")

    page = Page.objects.get(pk=legacy_page.pk).specific
    assert isinstance(page, ContentPage)
    assert [t.name for t in page.tags.all()] == ["chaleur"]
    assert page.revisions.count() == 1
    assert page.revisions.first().as_object().title == "Page héritée"
    # Saving still works: the phantom upstream tag table is back.
    page.save_revision().publish()


def test_command_is_idempotent(legacy_page):
    call_command("migrate_content_page_model")
    call_command("migrate_content_page_model")
    assert ContentPage.objects.filter(pk=legacy_page.pk).exists()
