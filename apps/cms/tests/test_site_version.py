"""Public pages: shared-cache headers (sites-conformes' PublicCacheMiddleware) and
ETag revalidation against the site version (cms/site_version.py)."""

import pytest
from django.contrib.auth import get_user_model
from wagtail.log_actions import log
from wagtail.models import Site

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    settings.SF_PUBLIC_CACHE_MAX_AGE = 60


@pytest.fixture
def page():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Chaleur", slug="chaleur")
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def test_anonymous_page_is_public_with_an_etag(client, page):
    response = client.get(page.url)
    assert response.status_code == 200
    assert response["Cache-Control"] == "public, max-age=60"
    assert response["ETag"]


def test_unchanged_site_answers_304_in_one_query(client, page, django_assert_max_num_queries):
    etag = client.get(page.url)["ETag"]
    with django_assert_max_num_queries(2):
        response = client.get(page.url, headers={"if-none-match": etag})
    assert response.status_code == 304
    assert response["ETag"] == etag
    assert response["Cache-Control"] == "public, max-age=60"


def test_publishing_any_page_changes_the_version(client, page):
    etag = client.get(page.url)["ETag"]
    other = ContentPage(title="Autre", slug="autre")
    page.get_parent().add_child(instance=other)
    other.save_revision().publish()
    response = client.get(page.url, headers={"if-none-match": etag})
    assert response.status_code == 200
    assert response["ETag"] != etag


def test_editing_a_snippet_or_setting_changes_the_version(client, page):
    etag = client.get(page.url)["ETag"]
    user = get_user_model().objects.create_user("editor")
    log(instance=user, action="wagtail.edit")  # what the admin logs on any model edit
    assert client.get(page.url, headers={"if-none-match": etag}).status_code == 200


def test_logged_in_page_is_private_without_etag(client, page):
    client.force_login(get_user_model().objects.create_user("editor"))
    response = client.get(page.url)
    assert "private" in response["Cache-Control"]
    assert not response.has_header("ETag")


def test_not_found_has_no_etag(client):
    response = client.get("/wp-config.php.bak")
    assert response.status_code == 404
    assert not response.has_header("ETag")


def test_admin_is_not_public(client):
    response = client.get("/cms-admin/login/")
    assert "public" not in response.get("Cache-Control", "")
    assert not response.has_header("ETag")
