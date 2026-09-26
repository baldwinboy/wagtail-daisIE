from django.urls import path

from . import views


app_name = "wagtail_daisIE_favicon"

urlpatterns = [
    path("manifest.json", views.manifest, name="manifest"),
    path("browser-config.xml", views.browser_config, name="browser_config"),
    path("favicon.ico", views.favicon, name="favicon"),
]
