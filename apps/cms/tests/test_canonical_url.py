"""The canonical and og:url tags, on a page reached the way production reaches it: through the
Scalingo proxy (infra/scalingo-proxy), with a Site record on port 443."""

import pytest
from django.core.cache import cache
from django.template import Context, Template
from wagtail.models import Site

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db

PUBLIC_HOST = "plusfraisautravail.beta.gouv.fr"
PROXY_HEADERS = {
    "Host": "cms.example.functions.fnc.fr-par.scw.cloud",
    "X-Forwarded-Host": PUBLIC_HOST,
    "X-Forwarded-Proto": "https",
    "X-Forwarded-For": "203.0.113.7",
}


@pytest.fixture(autouse=True)
def behind_the_proxy(settings):
    settings.USE_X_FORWARDED_HOST = True
    settings.ALLOWED_HOSTS = [PUBLIC_HOST]
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def public_site():
    site = Site.objects.get(is_default_site=True)
    home = ContentPage(title="Accueil", slug="accueil")
    site.root_page.add_child(instance=home)
    home.add_child(instance=ContentPage(title="Solutions", slug="solutions"))
    site.root_page = home
    site.hostname = PUBLIC_HOST
    site.port = 443
    site.save()
    yield site
    # Site.save() refreshed Wagtail's cached root paths; the rollback does not restore them.
    cache.clear()


@pytest.mark.parametrize("path", ["/", "/solutions/"])
def test_canonical_url_omits_the_https_default_port(client, public_site, path):
    response = client.get(path, headers=PROXY_HEADERS)

    assert response.status_code == 200
    html = response.content.decode()
    assert f'<link rel="canonical" href="https://{PUBLIC_HOST}{path}" />' in html
    assert f'<meta property="og:url" content="https://{PUBLIC_HOST}{path}" />' in html
    assert ":443" not in html


def test_canonical_url_drops_the_query_string(client, public_site):
    response = client.get("/solutions/?utm_source=x", headers=PROXY_HEADERS)

    assert f'<link rel="canonical" href="https://{PUBLIC_HOST}/solutions/" />' in (
        response.content.decode()
    )


def test_canonical_url_follows_wagtail_on_a_non_default_port(client, public_site):
    public_site.port = 8000
    public_site.save()

    response = client.get("/", headers=PROXY_HEADERS)

    assert f'<link rel="canonical" href="http://{PUBLIC_HOST}:8000/"' in response.content.decode()


def test_canonical_url_names_the_site_rather_than_the_request_host(client, public_site, settings):
    proxy_host = "plusfraisautravail-proxy.osc-fr1.scalingo.io"
    settings.ALLOWED_HOSTS = [proxy_host]

    response = client.get("/", headers={**PROXY_HEADERS, "X-Forwarded-Host": proxy_host})

    assert f'<link rel="canonical" href="https://{PUBLIC_HOST}/"' in response.content.decode()


def test_canonical_url_is_empty_without_a_request():
    # Through the template engine: importing cms.pages.canonical here would register the tag and
    # hide a missing PagesConfig.ready().
    template = Template("{% load wagtail_dsfr_tags %}{% canonical_url %}")

    assert template.render(Context()) == ""
