"""migrate_blog_entry_page_model adopts legacy sites_conformes_blog.BlogEntryPage
rows as cms_pages.BlogEntryPage. Same approach as test_content_page_migration:
rebuild the legacy state on the fresh test database, run the command, and check
the entries come back untouched."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from sites_conformes.blog.models import BlogIndexPage, Category, Person
from wagtail.models import Page, Site

from cms.pages.models import BlogEntryPage

pytestmark = pytest.mark.django_db

TABLES = ["blogentrypage", "tagentrypage", "categoryentrypage", "blogentrypage_authors"]


def make_legacy_state():
    """Put the database back the way a pre-swap deployment left it."""
    with connection.cursor() as cur:
        for table in TABLES:
            cur.execute(f"ALTER TABLE cms_pages_{table} RENAME TO sites_conformes_blog_{table}")
    # A fresh database may also hold a content type for the swapped-out model.
    ContentType.objects.filter(app_label="sites_conformes_blog", model="blogentrypage").delete()
    ContentType.objects.filter(app_label="cms_pages", model="blogentrypage").update(
        app_label="sites_conformes_blog"
    )
    ContentType.objects.clear_cache()
    MigrationRecorder.Migration.objects.filter(app="cms_pages", name="0002_blogentrypage").delete()


@pytest.fixture
def legacy_entry():
    root = Site.objects.get(is_default_site=True).root_page
    blog = root.add_child(instance=BlogIndexPage(title="Actualités", slug="actualites"))
    entry = blog.add_child(instance=BlogEntryPage(title="Article hérité", slug="article-herite"))
    entry.tags.add("chaleur")
    entry.blog_categories.add(Category.objects.create(name="Canicule", slug="canicule"))
    entry.authors.add(Person.objects.create(name="Ada", role="Autrice"))
    entry.save_revision().publish()
    make_legacy_state()
    return entry


def test_entries_relations_and_revisions_survive(legacy_entry):
    call_command("migrate_blog_entry_page_model")

    entry = Page.objects.get(pk=legacy_entry.pk).specific
    assert isinstance(entry, BlogEntryPage)
    assert [t.name for t in entry.tags.all()] == ["chaleur"]
    assert [c.name for c in entry.blog_categories.all()] == ["Canicule"]
    assert [a.name for a in entry.authors.all()] == ["Ada"]
    assert list(entry.get_parent().specific.posts) == [entry]
    assert entry.revisions.first().as_object().title == "Article hérité"
    entry.save_revision().publish()
    assert MigrationRecorder.Migration.objects.filter(
        app="cms_pages", name="0002_blogentrypage"
    ).exists()


def test_command_is_idempotent(legacy_entry):
    call_command("migrate_blog_entry_page_model")
    call_command("migrate_blog_entry_page_model")
    assert BlogEntryPage.objects.filter(pk=legacy_entry.pk).exists()
