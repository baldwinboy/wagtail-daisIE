"""Public URLs for notifications. Include from the project's ``urls.py``::

path("newsletter/", include("wagtail_daisIE.notifications.urls")),
"""

from django.urls import path

from . import views


app_name = "wagtail_daisIE_notifications"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
]
