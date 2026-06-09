from django.urls import include, path
from django.views.i18n import JavaScriptCatalog
from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import DaisyUITheme


class DaisyUIThemeViewSet(SnippetViewSet):
    model = DaisyUITheme


register_snippet(DaisyUIThemeViewSet)


@hooks.register("register_admin_urls")
def register_admin_urls():
    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["wagtail_daisIE"]),
            name="javascript_catalog",
        ),
        # Add other package-scoped URLs here so they are access-restricted to the admin.
    ]

    return [
        path(
            "wagtail_daisIE/",
            include(
                (urls, "wagtail_daisIE"),
                namespace="wagtail_daisIE",
            ),
        )
    ]
