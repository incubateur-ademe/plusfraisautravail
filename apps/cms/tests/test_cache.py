"""Shared-cache headers (cms/cache.py): public pages cached by the proxy, nothing
personal ever marked public."""

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory
from wagtail.models import Site

from cms.cache import PrivateResponseMiddleware, add_public_cache_headers
from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    settings.CACHE_CONTROL_S_MAXAGE = 300
    settings.CACHE_CONTROL_STALE_WHILE_REVALIDATE = 30


@pytest.fixture
def page():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Chaleur", slug="chaleur")
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def test_anonymous_page_is_public(client, page):
    response = client.get(page.url)
    assert response.status_code == 200
    assert response["Cache-Control"] == "public, s-maxage=300, stale-while-revalidate=30"


def test_logged_in_page_is_never_shared(client, page):
    user = get_user_model().objects.create_user("editor", password="x")
    client.force_login(user)
    cache_control = client.get(page.url)["Cache-Control"]
    assert "public" not in cache_control
    assert "private" in cache_control


def test_not_found_is_not_public(client):
    response = client.get("/wp-config.php.bak")
    assert response.status_code == 404
    assert "public" not in response.get("Cache-Control", "")


def test_admin_is_not_public(client):
    assert "public" not in client.get("/cms-admin/login/").get("Cache-Control", "")


def test_robots_is_public(client):
    assert "public" in client.get("/robots.txt")["Cache-Control"]


def test_csrf_token_makes_a_response_private():
    request = RequestFactory().get("/")
    request.META["CSRF_COOKIE_NEEDS_UPDATE"] = True
    middleware = PrivateResponseMiddleware(lambda r: add_public_cache_headers(HttpResponse()))
    assert "public" not in middleware(request)["Cache-Control"]
