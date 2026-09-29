from wagtail.snippets.views.snippets import SnippetViewSet

from .models import DaisyUIFavicon, DaisyUIIconSource


class DaisyUIIconSourceViewSet(SnippetViewSet):
    icon = "image"
    menu_label = "Icon Sources"
    model = DaisyUIIconSource


class DaisyUIFaviconViewSet(SnippetViewSet):
    icon = "site"
    menu_label = "Favicon"
    model = DaisyUIFavicon
    list_display = ["site", "app_name", "theme_color"]
    search_fields = ["app_name", "short_name"]
