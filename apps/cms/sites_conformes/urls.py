from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def healthz(request):
    return HttpResponse("ok")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
]
