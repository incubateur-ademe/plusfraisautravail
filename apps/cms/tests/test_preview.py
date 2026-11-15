from django.http import HttpResponse

from cms.settings.preview import noindex


def test_a_preview_asks_not_to_be_indexed(rf):
    response = noindex(lambda request: HttpResponse())(rf.get("/"))

    assert response["X-Robots-Tag"] == "noindex"
