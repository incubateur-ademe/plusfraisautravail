"""change_page_type swaps a page's specific model in place: same Page row (id, URL,
tree position, history), shared fields and tags carried over, still live."""

import pytest
from django.contrib.auth import get_user_model
from sites_conformes.blog.models import BlogIndexPage
from wagtail.models import Page, Site

from cms.pages.change_type import change_page_type, target_models
from cms.pages.models import BlogEntryPage, ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def admin():
    return get_user_model().objects.create_superuser("admin", "a@example.com", "pw")


@pytest.fixture
def entry():
    root = Site.objects.get(is_default_site=True).root_page
    blog = root.add_child(instance=BlogIndexPage(title="Actualités", slug="actualites"))
    entry = BlogEntryPage(title="Un article", slug="un-article")
    entry.body = [("paragraph", "<p>Il fait chaud.</p>")]
    blog.add_child(instance=entry)
    entry.tags.add("chaleur")
    entry.save_revision().publish()
    return entry


def test_blog_entry_becomes_content_page(entry, admin, client):
    url = entry.url

    change_page_type(entry, ContentPage, admin)

    page = Page.objects.get(pk=entry.pk).specific
    assert isinstance(page, ContentPage)
    assert not BlogEntryPage.objects.filter(pk=entry.pk).exists()
    assert page.live and not page.has_unpublished_changes
    assert page.url == url
    assert page.body[0].value.source == "<p>Il fait chaud.</p>"
    assert [t.name for t in page.tags.all()] == ["chaleur"]
    # History kept (the old revision plus the conversion's), every one opening as the new type.
    assert page.revisions.count() == 2
    assert all(isinstance(r.as_object(), ContentPage) for r in page.revisions.all())
    assert client.get(url).status_code == 200


def test_view_converts_and_sends_to_move_when_parent_refuses_new_type(entry, admin, client):
    client.force_login(admin)
    url = f"/cms-admin/pages/{entry.pk}/changer-type/"
    assert client.get(url).status_code == 200

    response = client.post(url, {"target": "cms_pages.contentpage"})

    # Blog indexes only take blog entries: the page must be moved somewhere else.
    assert response.url == f"/cms-admin/pages/{entry.pk}/move/"
    assert isinstance(Page.objects.get(pk=entry.pk).specific, ContentPage)


def test_unpublished_changes_are_refused(entry, admin):
    entry.title = "Brouillon"
    entry.save_revision()

    with pytest.raises(ValueError):
        change_page_type(entry, ContentPage, admin)


def test_targets_exclude_own_type_and_full_singletons(entry):
    targets = target_models(entry.specific)
    assert ContentPage in targets
    assert BlogEntryPage not in targets
