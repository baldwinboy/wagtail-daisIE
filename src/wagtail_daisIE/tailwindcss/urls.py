"""URLs for content-addressed Tailwind CSS artifacts."""

from django.urls import path

from . import views


app_name = "wagtail_daisIE_tailwind"

urlpatterns = [
    path("artifact/<str:token>.css", views.artifact, name="artifact"),
    path("input/<str:token>.css", views.input, name="input"),
]
