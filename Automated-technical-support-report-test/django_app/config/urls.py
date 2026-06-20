from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap


def ping(request):
    return JsonResponse({"status": "alive"})

sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path('admin/',               admin.site.urls),
    path('health/',               ping),
    path('',                     include('apps.dashboard.urls')),
    path('reports/',             include('apps.reports.urls')),
    path('customers/',           include('apps.customers.urls')),
    path('agents/',              include('apps.agents.urls')),
    path('users/',               include('apps.users.urls')),
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps},name="django.contrib.sitemaps.views.sitemap",),
]
