from functools import partial

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.db import connection
from django.http import HttpResponse
from django.urls import include, path
from django.views.defaults import page_not_found, server_error
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


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
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

# Django only auto-loads a root-level 404.html/500.html; sites-conformes ships its
# DSFR error pages under sites_conformes_core/, so they must be wired explicitly
# (mirrors upstream config/urls.py).
handler404 = partial(page_not_found, template_name="sites_conformes_core/404.html")
handler500 = partial(server_error, template_name="sites_conformes_core/500.html")
