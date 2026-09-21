"""Public URLs backing dynamic action buttons.

Include from the project's ``urls.py``::

    (path("daisie/", include("wagtail_daisIE.dynamic.urls")),)
"""

from django.urls import path

from . import views


app_name = "wagtail_daisIE_dynamic"

urlpatterns = [
    path("actions/<str:action_key>/", views.action, name="action"),
    path("feeds/<int:pk>/items/", views.feed_items, name="feed_items"),
]
