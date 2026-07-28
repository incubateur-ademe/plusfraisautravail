from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.db import connection
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic.base import RedirectView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet

api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", PagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)


def healthz(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok")


def ping(request):
    """Diagnostic: static 200, no DB, no middleware-heavy logic."""
    return HttpResponse("pong")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("ping/", ping, name="ping"),
    path("sitemap.xml", sitemap, name="xml_sitemap"),
    path(settings.WAGTAILADMIN_PATH, include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("api/v2/", api_router.urls),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/dsfr/dist/favicon/favicon.ico", permanent=True),
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += i18n_patterns(
    path("", include("sites_conformes.core.urls")),
    prefix_default_language=False,
)
