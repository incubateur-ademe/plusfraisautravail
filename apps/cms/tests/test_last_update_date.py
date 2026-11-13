"""Content pages show their update date at the end of the content, unless hidden."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from wagtail.models import Site

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def page():
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Végétaliser", slug="vegetaliser")
    root.add_child(instance=page)
    return page


def test_shows_the_last_publication_date(client, page):
    page.save_revision().publish()
    # 23:30 UTC is already the next day in Paris.
    page.last_published_at = datetime(2026, 10, 20, 23, 30, tzinfo=ZoneInfo("UTC"))
    page.save(update_fields=["last_published_at"])

    html = client.get(page.url).content.decode()

    assert '<time datetime="2026-10-21">21 octobre 2026</time>' in html
    assert "Mis à jour le" in html


def test_shows_no_date_on_a_page_never_published(page):
    page.live = False
    page.save()

    assert page.last_published_at is None
    response = page.make_preview_request()
    assert "Mis à jour le" not in response.render().content.decode()


def test_the_editor_date_wins_over_the_publication_date(client, page):
    page.last_update_date = date(2026, 6, 26)
    page.save_revision().publish()

    html = client.get(page.url).content.decode()

    assert '<time datetime="2026-06-26">26 juin 2026</time>' in html


def test_shows_the_date_after_the_content(client, page):
    page.body = '[{"type": "paragraph", "value": "<p>Végétaliser la cour.</p>", "id": "p"}]'
    page.save_revision().publish()

    html = client.get(page.url).content.decode()

    assert html.index("Végétaliser la cour.") < html.index("Mis à jour le")


def test_editors_can_hide_the_date(client, page):
    page.show_update_date = False
    page.save_revision().publish()

    assert "Mis à jour le" not in client.get(page.url).content.decode()
