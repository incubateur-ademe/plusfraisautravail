"""seed_categories_from_tags builds the sector and region trees and categorises the
content pages that carry the matching tags, in the page and in its latest revision."""

import pytest
from django.core.management import call_command
from sites_conformes.core.models import Category
from wagtail.models import Site

from cms.pages.management.commands.seed_categories_from_tags import CATEGORY_TREE
from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def tagged_page():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Chantier", slug="chantier")
    page.tags.add("BTP")
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def test_creates_the_trees_and_categorises_tagged_pages(tagged_page):
    call_command("seed_categories_from_tags")

    sectors = Category.objects.get(name="Secteur d'activités", parent=None)
    btp = Category.objects.get(name="BTP", parent=sectors)
    page = ContentPage.objects.get(pk=tagged_page.pk)
    assert list(page.categories.all()) == [btp]
    assert page.latest_revision.content["categories"] == [btp.pk]
    regions = Category.objects.get(name="Régions", parent=None)
    assert regions.get_children().count() == len(CATEGORY_TREE["Régions"])


def test_is_idempotent(tagged_page):
    call_command("seed_categories_from_tags")
    call_command("seed_categories_from_tags")

    assert Category.objects.filter(name="BTP").count() == 1
    assert ContentPage.objects.get(pk=tagged_page.pk).categories.count() == 1


def test_dry_run_changes_nothing(tagged_page):
    call_command("seed_categories_from_tags", dry_run=True)

    assert not Category.objects.filter(name="BTP").exists()
    assert ContentPage.objects.get(pk=tagged_page.pk).categories.count() == 0
