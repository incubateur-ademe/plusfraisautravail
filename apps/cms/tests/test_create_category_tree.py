"""create_category_tree builds the sector and region trees and leaves the pages alone."""

import pytest
from django.core.management import call_command
from sites_conformes.core.models import Category
from wagtail.models import Site

from cms.pages.management.commands.seed_categories_from_tags import CATEGORY_TREE
from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


def test_creates_the_trees_without_categorising_pages():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Chantier", slug="chantier")
    page.tags.add("BTP")
    root.add_child(instance=page)

    call_command("create_category_tree")
    call_command("create_category_tree")  # idempotent

    expected = len(CATEGORY_TREE) + sum(len(children) for children in CATEGORY_TREE.values())
    assert Category.objects.count() == expected
    assert Category.objects.get(name="BTP").parent.name == "Secteur d'activités"
    assert not ContentPage.objects.get(pk=page.pk).categories.exists()


def test_dry_run_changes_nothing():
    call_command("create_category_tree", dry_run=True)

    assert not Category.objects.exists()
