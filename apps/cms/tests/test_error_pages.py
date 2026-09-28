import pytest


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
