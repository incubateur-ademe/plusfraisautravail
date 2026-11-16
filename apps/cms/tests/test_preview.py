import io
import urllib.request
from urllib.error import HTTPError

import pytest
from django.core.files.base import ContentFile
from django.http import HttpResponse

from cms.preview import PreviewStorage
from cms.settings.preview import noindex

PRODUCTION = "https://production.test/media/"


def test_a_preview_asks_not_to_be_indexed(rf):
    response = noindex(lambda request: HttpResponse())(rf.get("/"))

    assert response["X-Robots-Tag"] == "noindex"


@pytest.fixture
def production(monkeypatch):
    """Files of production, keyed by URL: urlopen answers 404 for any other."""
    files = {}

    def urlopen(request, timeout):
        url = request if isinstance(request, str) else request.full_url
        if url not in files:
            raise HTTPError(url, 404, "Not Found", {}, None)
        return io.BytesIO(files[url])

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return files


@pytest.mark.django_db
def test_production_media_are_read_from_production(production):
    production[PRODUCTION + "original_images/a%20b.jpg"] = b"original"
    storage = PreviewStorage(PRODUCTION)

    assert storage.url("original_images/a b.jpg") == PRODUCTION + "original_images/a%20b.jpg"
    assert storage.exists("original_images/a b.jpg")
    assert storage.size("original_images/a b.jpg") == len(b"original")
    with storage.open("original_images/a b.jpg") as file:
        assert file.read() == b"original"


@pytest.mark.django_db
def test_an_upload_stays_in_the_preview_and_covers_no_production_file(production):
    production[PRODUCTION + "original_images/a.jpg"] = b"production"
    storage = PreviewStorage(PRODUCTION)

    name = storage.save("original_images/a.jpg", ContentFile(b"upload"))

    assert name != "original_images/a.jpg"
    assert storage.url(name).startswith("/storage/serve/")
    assert storage.open(name).read() == b"upload"
    assert not storage.exists("original_images/missing.jpg")
