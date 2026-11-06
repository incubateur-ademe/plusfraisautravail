"""The "tag links" setting: on by default, off it turns every tag into plain text and takes the
tag pages down, while the tag filters of the listing pages keep working."""

import json
import re
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import ProgrammingError, connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from sites_conformes.blog.models import BlogIndexPage
from sites_conformes.core.models import CatalogIndexPage, Tag
from sites_conformes.events.models import EventEntryPage, EventsIndexPage
from wagtail.models import Site

from cms.pages.models import BlogEntryPage, ContentPage, TagSettings, warn_missing_table

pytestmark = pytest.mark.django_db

TAG_LINK = "https://example.org/lien-du-tag"
TAG_BLOCK = {
    "type": "tag",
    "value": {
        "label": "Tag de bloc",
        "link": {"link_type": "external_url", "external_url": TAG_LINK},
    },
}
BODY = json.dumps(
    [
        {"type": "tags_list", "value": [TAG_BLOCK]},
        {
            "type": "card",
            "value": {
                "title": "Carte",
                "top_detail_badges_tags": [{"type": "tags", "value": [TAG_BLOCK]}],
            },
        },
    ]
)


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.DEBUG = False
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


def tagged(parent, page):
    parent.add_child(instance=page)
    page.tags.add("Chaleur")
    page.save_revision().publish()
    return page


@pytest.fixture
def site():
    root = Site.objects.get(is_default_site=True).root_page
    catalog = root.add_child(
        instance=CatalogIndexPage(
            title="Catalogue",
            slug="catalogue",
            filter_by_tag=True,
            filter_selection=CatalogIndexPage.SINGLE_FILTER,
            body=BODY,
        )
    )
    blog = root.add_child(instance=BlogIndexPage(title="Blog", slug="blog", filter_by_tag=True))
    events = root.add_child(
        instance=EventsIndexPage(title="Agenda", slug="agenda", filter_by_tag=True)
    )
    now = timezone.now()
    return {
        "content": tagged(root, ContentPage(title="Page", slug="page", body=BODY)),
        "catalog": catalog,
        "catalog_entry": tagged(catalog, ContentPage(title="Fiche", slug="fiche")),
        "blog": blog,
        "entry": tagged(blog, BlogEntryPage(title="Billet", slug="billet")),
        "events": events,
        "event": tagged(
            events,
            EventEntryPage(
                title="Atelier",
                slug="atelier",
                event_date_start=now + timedelta(days=1),
                event_date_end=now + timedelta(days=2),
            ),
        ),
    }


def turn_links_off():
    # Through load(): rendering a page, as publishing does, may already have created the row.
    tag_settings = TagSettings.load()
    tag_settings.links_enabled = False
    tag_settings.save()


@pytest.fixture
def links_off():
    turn_links_off()


@pytest.fixture(params=["on", "off"])
def either_position(request):
    if request.param == "off":
        turn_links_off()


@pytest.fixture
def no_table():
    """DROP TABLE is transactional in Postgres: the transaction of the test brings it back."""
    warn_missing_table.cache_clear()
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE cms_pages_tagsettings")
    yield
    warn_missing_table.cache_clear()


PAGE_TAG_LINKS = [
    ("content", 'href="/tags/chaleur/"'),
    ("entry", 'href="/blog/?tag=chaleur"'),
    ("event", 'href="/agenda/?tag=chaleur"'),
]


def test_links_are_enabled_by_default():
    assert TagSettings.load().links_enabled is True


def test_tagged_pages_keep_their_links_while_the_table_is_missing(client, site, no_table):
    response = client.get(site["content"].url)
    assert response.status_code == 200
    assert 'href="/tags/chaleur/"' in response.content.decode()
    assert client.get(reverse("global_tags_list")).status_code == 200


def test_publishing_a_tag_block_works_while_the_table_is_missing(site, no_table):
    # save() renders the body to fill the empty SEO description, inside the add_child transaction.
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title="Nouvelle", slug="nouvelle", body=BODY)
    root.add_child(instance=page)
    page.save_revision().publish()

    page.refresh_from_db()
    assert page.live
    assert "Tag de bloc" in page.search_description


def test_missing_table_warns_once(client, site, no_table, caplog):
    for _ in range(2):
        client.get(site["content"].url)

    assert [r.getMessage() for r in caplog.records if r.name == "cms.pages.models"] == [
        "cms_pages_tagsettings table missing: tag links stay on until migration 0006 runs"
    ]


def test_other_database_errors_are_not_hidden(site):
    TagSettings.load()
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE cms_pages_tagsettings RENAME COLUMN links_enabled TO renamed_column"
        )

    with pytest.raises(ProgrammingError):
        TagSettings.links_on()


def test_a_request_reads_the_setting_once(client, site):
    with CaptureQueriesContext(connection) as queries:
        client.get(site["content"].url)

    assert len([q for q in queries if "cms_pages_tagsettings" in q["sql"]]) == 1


def test_admin_turns_the_links_off_with_a_french_help_text(client, site):
    client.force_login(get_user_model().objects.create_superuser("admin", "a@example.org", "x"))
    url = reverse("wagtailsettings:edit", args=["cms_pages", "tagsettings", TagSettings.load().pk])
    assert "Décochez pour afficher les tags" in client.get(url).content.decode()

    assert client.post(url, {}).status_code == 302
    client.logout()

    assert TagSettings.load().links_enabled is False
    assert client.get(reverse("global_tags_list")).status_code == 404


@pytest.mark.parametrize("name, href", PAGE_TAG_LINKS)
def test_page_tags_are_links_by_default(client, site, name, href):
    assert href in client.get(site[name].url).content.decode()


@pytest.mark.parametrize("name, href", PAGE_TAG_LINKS)
def test_page_tags_are_plain_text_when_links_are_off(client, site, links_off, name, href):
    html = client.get(site[name].url).content.decode()
    assert href not in html
    assert '<p class="fr-tag">Chaleur</p>' in html


def test_tag_blocks_and_cards_keep_their_link_by_default(client, site):
    assert client.get(site["content"].url).content.decode().count(f'<a href="{TAG_LINK}"') == 2


def test_tag_blocks_and_cards_are_plain_text_when_links_are_off(client, site, links_off):
    html = client.get(site["content"].url).content.decode()
    assert TAG_LINK not in html
    assert html.count('<p class="fr-tag">Tag de bloc</p>') == 2


def test_tag_block_without_template_context_follows_the_setting(client, site, links_off):
    # catalog_index_page.html renders {{ page.body }}: its blocks get neither context nor request.
    html = client.get(site["catalog"].url).content.decode()
    assert TAG_LINK not in html
    assert '<p class="fr-tag">Tag de bloc</p>' in html


def tag_page_urls(site):
    return [
        reverse("global_tags_list"),
        reverse("global_tag", args=["chaleur"]),
        f"{site['blog'].url}tags/",
        f"{site['catalog'].url}tags/",
    ]


def test_tag_pages_are_online_by_default(client, site):
    for url in tag_page_urls(site):
        assert client.get(url).status_code == 200, url


def test_tag_pages_answer_404_when_links_are_off(client, site, links_off):
    for url in tag_page_urls(site):
        assert client.get(url).status_code == 404, url


def test_other_routes_of_the_index_pages_stay_online_when_links_are_off(client, site, links_off):
    for url in [f"{site['blog'].url}rss/", f"{site['blog'].url}categories/", site["blog"].url]:
        assert client.get(url).status_code == 200, url


@pytest.mark.parametrize("name", ["catalog", "blog"])
def test_filter_breadcrumb_links_to_the_tag_list_by_default(client, site, name):
    url = site[name].url
    assert f'href="{url}tags/"' in client.get(f"{url}?tag=chaleur").content.decode()


@pytest.mark.parametrize("name", ["catalog", "blog"])
def test_filter_breadcrumb_drops_the_dead_link_when_links_are_off(client, site, links_off, name):
    url = site[name].url
    html = client.get(f"{url}?tag=chaleur").content.decode()
    assert f'href="{url}tags/"' not in html
    assert f'class="fr-breadcrumb__link" href="{url}"' in html


@pytest.mark.parametrize(
    "name, entry", [("catalog", "Fiche"), ("blog", "Billet"), ("events", "Atelier")]
)
def test_tag_filters_keep_working_when_links_are_off(client, site, links_off, name, entry):
    url = site[name].url
    listing = client.get(url).content.decode()
    assert f"{url}?tag=chaleur" in listing

    filtered = client.get(f"{url}?tag=chaleur")
    assert filtered.status_code == 200
    assert entry in filtered.content.decode()


def test_sitemap_lists_no_tag_page(client, site, either_position):
    sitemap = client.get(reverse("xml_sitemap")).content
    assert b"/page/" in sitemap
    assert b"/tags/" not in sitemap


@pytest.mark.parametrize("feed", ["rss", "atom"])
def test_feeds_list_no_tag(client, site, either_position, feed):
    content = client.get(f"{site['blog'].url}{feed}/").content
    assert b"Billet" in content
    assert b"Chaleur" not in content


@pytest.mark.parametrize("url", ["/tags", "/tags/chaleur", "/blog/tags", "/catalogue/tags"])
def test_urls_without_slash_lead_to_the_tag_pages(client, site, url):
    response = client.get(url, follow=True)
    assert response.redirect_chain == [(f"{url}/", 301)]
    assert response.status_code == 200


@pytest.mark.parametrize("url", ["/tags", "/tags/chaleur", "/blog/tags", "/catalogue/tags"])
def test_urls_without_slash_lead_to_the_404_when_links_are_off(client, site, links_off, url):
    response = client.get(url, follow=True)
    assert response.redirect_chain == [(f"{url}/", 301)]
    assert response.status_code == 404


def test_recent_entries_blocks_keep_their_tag_filters(client, site, either_position):
    # Set block by block, like the filters of the listing pages are set page by page.
    tag = Tag.objects.get(slug="chaleur")
    filters = {"tag_filter": tag.pk, "show_filters": True}
    page = ContentPage(
        title="Accueil",
        slug="accueil",
        body=json.dumps(
            [
                {"type": "blog_recent_entries", "value": {"blog": site["blog"].pk, **filters}},
                {
                    "type": "events_recent_entries",
                    "value": {"index_page": site["events"].pk, **filters},
                },
            ]
        ),
    )
    Site.objects.get(is_default_site=True).root_page.add_child(instance=page)

    html = client.get(page.url).content.decode()
    assert re.search(r'class="fr-tag"\s+href="/blog/\?tag=chaleur', html)
    assert re.search(r'class="fr-tag"\s+href="/agenda/\?tag=chaleur', html)


@pytest.fixture
def catalog_named_tags():
    root = Site.objects.get(is_default_site=True).root_page
    rubric = root.add_child(instance=ContentPage(title="Rubrique", slug="rub"))
    catalog = rubric.add_child(
        instance=CatalogIndexPage(
            title="Catalogue tags",
            slug="tags",
            filter_by_tag=True,
            filter_selection=CatalogIndexPage.SINGLE_FILTER,
        )
    )
    tagged(catalog, ContentPage(title="Fiche", slug="fiche"))
    return catalog


def breadcrumb_hrefs(html):
    return re.findall(r'class="fr-breadcrumb__link" href="([^"]+)"', html)


def test_catalog_named_tags_keeps_its_breadcrumb_link(client, catalog_named_tags, links_off):
    assert client.get("/rub/tags/tags/").status_code == 404
    html = client.get("/rub/tags/?tag=chaleur").content.decode()
    assert breadcrumb_hrefs(html) == ["/", "/rub/", "/rub/tags/"]


def test_catalog_named_tags_keeps_its_tag_list_by_default(client, catalog_named_tags):
    html = client.get("/rub/tags/?tag=chaleur").content.decode()
    assert breadcrumb_hrefs(html) == ["/", "/rub/", "/rub/tags/", "/rub/tags/tags/"]
