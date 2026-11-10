import types

import pytest
from django.urls import path


@pytest.mark.django_db
def test_404_uses_sites_conformes_template(client, settings):
    settings.DEBUG = False
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    response = client.get("/this-page-does-not-exist/")
    assert response.status_code == 404
    assert "sites_conformes_core/404.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_403_uses_sites_conformes_template(client, settings):
    from django.core.exceptions import PermissionDenied

    from cms import urls

    def forbidden(request):
        raise PermissionDenied

    # The project urlconf plus one view that raises PermissionDenied.
    urlconf = types.ModuleType("forbidden_urls")
    urlconf.urlpatterns = [path("forbidden/", forbidden), *urls.urlpatterns]
    urlconf.handler403 = urls.handler403

    settings.ROOT_URLCONF = urlconf
    settings.DEBUG = False
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    response = client.get("/forbidden/")
    assert response.status_code == 403
    assert b"fr-container" in response.content
