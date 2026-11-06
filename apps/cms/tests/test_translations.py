"""sites-conformes ships its .po files without their .mo, and translates its URLs.

The CI does not compile them, so these tests would stay red there and block every deploy.
There, the assertion in the Dockerfile fails the image build instead."""

import os

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import translation

pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="the CI does not compile the .mo; the image build checks them",
)


def test_the_sites_conformes_french_catalog_is_compiled():
    with translation.override(settings.LANGUAGE_CODE):
        assert translation.gettext("Filters") == "Filtres"


@pytest.mark.parametrize(
    "name, url",
    [("cms_search", "/recherche/"), ("readable_sitemap", "/plan-du-site/")],
)
def test_the_public_urls_stay_in_french(name, url):
    with translation.override(settings.LANGUAGE_CODE):
        assert reverse(name) == url
