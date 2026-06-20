from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return [
            "home",
            "reports_list",
            "monthly",
            "customers_list",
            "agents_list",
            "login",
        ]

    def location(self, item):
        return reverse(item)