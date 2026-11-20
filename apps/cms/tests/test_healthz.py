import pytest


@pytest.mark.django_db
def test_healthz_answers_the_build_of_the_image(client, monkeypatch):
    monkeypatch.setenv("BUILD_SHA", "sha-abc123")

    response = client.get("/healthz/")

    assert response.status_code == 200
    assert response.content == b"sha-abc123"
