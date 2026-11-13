"""seed_categories_from_tags replaces the mapped tags of the pages by categories, in the page
and in its latest revision, and switches their index pages to the category filter."""

import pytest
from django.core.management import call_command
from sites_conformes.core.models import CatalogIndexPage, Category
from taggit.models import Tag
from wagtail.models import Site

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def index():
    root = Site.objects.get(is_default_site=True).root_page
    index = CatalogIndexPage(
        title="Inspirations", slug="inspirations", filter_by_tag=True, filter_by_category=False
    )
    root.add_child(instance=index)
    index.save_revision().publish()
    return index


@pytest.fixture
def tagged_page(index):
    page = ContentPage(title="Chantier", slug="chantier")
    page.tags.add("BTP", "Entreprise", "Sans catégorie")
    index.add_child(instance=page)
    page.save_revision().publish()
    page.title = "Chantier (brouillon)"
    page.save_revision()  # pending draft: it must get the change too
    return ContentPage.objects.get(pk=page.pk)


def category(root_name, name):
    return Category.objects.get(name=name, parent__name=root_name, parent__parent=None)


def test_replaces_the_mapped_tags_by_categories(tagged_page):
    call_command("seed_categories_from_tags")

    expected = {category("Secteur d'activités", "BTP"), category("Type de structure", "Entreprise")}
    page = ContentPage.objects.get(pk=tagged_page.pk)
    assert set(page.categories.all()) == expected
    assert [tag.name for tag in page.tags.all()] == ["Sans catégorie"]
    draft = page.latest_revision.content
    assert draft["title"] == "Chantier (brouillon)"
    assert draft["categories"] == sorted(c.pk for c in expected)
    assert [item["tag"] for item in draft["tagged_items"]] == [
        Tag.objects.get(name="Sans catégorie").pk
    ]


def test_cleans_the_tags_of_revisions_saved_before_the_swap(tagged_page):
    revision = tagged_page.latest_revision
    content = dict(revision.content)
    content["contentpage_tags"] = content.pop("tagged_items")
    revision.content = content
    revision.save()

    call_command("seed_categories_from_tags")

    draft = ContentPage.objects.get(pk=tagged_page.pk).latest_revision.content
    assert "tagged_items" not in draft
    assert [item["tag"] for item in draft["contentpage_tags"]] == [
        Tag.objects.get(name="Sans catégorie").pk
    ]


def test_switches_the_index_from_the_tag_to_the_category_filter(tagged_page, index):
    call_command("seed_categories_from_tags")

    index = CatalogIndexPage.objects.get(pk=index.pk)
    assert (index.filter_by_tag, index.filter_by_category) == (False, True)
    content = index.latest_revision.content
    assert (content["filter_by_tag"], content["filter_by_category"]) == (False, True)
    assert index.show_filters


def test_reuses_the_categories_the_editors_created(index):
    levier = Category.add_root(name="Levier")
    batiments = levier.add_child(name="🏢 Bâtiments")
    page = ContentPage(title="Isoler", slug="isoler")
    page.tags.add(Tag.objects.create(name="🏢 Bâtiments", slug="batiments"))
    index.add_child(instance=page)

    call_command("seed_categories_from_tags")

    assert Category.objects.filter(name="Levier").count() == 1
    assert list(ContentPage.objects.get(pk=page.pk).categories.all()) == [batiments]


def test_is_idempotent(tagged_page):
    call_command("seed_categories_from_tags")
    count = Category.objects.count()
    call_command("seed_categories_from_tags")

    assert Category.objects.count() == count
    assert ContentPage.objects.get(pk=tagged_page.pk).categories.count() == 2


def test_dry_run_changes_nothing(tagged_page, index):
    call_command("seed_categories_from_tags", dry_run=True)

    assert not Category.objects.exists()
    assert ContentPage.objects.get(pk=tagged_page.pk).tags.count() == 3
    assert CatalogIndexPage.objects.get(pk=index.pk).filter_by_tag is True
