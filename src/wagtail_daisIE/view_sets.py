from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .assets.view_sets import DaisyUIFaviconViewSet, DaisyUIIconSourceViewSet
from .feeds.view_sets import FeedViewSet
from .menus.view_sets import DaisyUIMenuViewSet
from .models import DaisyUITheme


class DaisyUIThemeViewSet(SnippetViewSet):
    icon = "cogs"
    menu_label = "Themes"
    model = DaisyUITheme


class DaisyUIViewSetGroup(SnippetViewSetGroup):
    items = (
        DaisyUIThemeViewSet,
        DaisyUIMenuViewSet,
        DaisyUIIconSourceViewSet,
        DaisyUIFaviconViewSet,
        FeedViewSet,
    )
    menu_icon = "palette"
    menu_label = "Design"
    menu_name = "design"
    add_to_admin_menu = True
