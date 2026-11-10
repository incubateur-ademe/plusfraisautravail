import pytest


@pytest.mark.django_db
def test_robots_txt_is_served(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert b"Sitemap: http://testserver/sitemap.xml" in response.content
