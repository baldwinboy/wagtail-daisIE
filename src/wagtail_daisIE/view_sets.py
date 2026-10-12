from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .assets.view_sets import DaisyUIFaviconViewSet, DaisyUIIconSourceViewSet
from .feeds.view_sets import FeedViewSet
from .menus.view_sets import DaisyUIMenuViewSet
from .models import DaisyUITheme
from .models.reusable import ReusableBlock


class DaisyUIThemeViewSet(SnippetViewSet):
    icon = "cogs"
    menu_label = "Themes"
    model = DaisyUITheme


class ReusableBlockViewSet(SnippetViewSet):
    icon = "doc-full-inverse"
    menu_label = "Reusable blocks"
    model = ReusableBlock
    search_fields = ["name"]
    list_display = ["name"]


class DaisyUIViewSetGroup(SnippetViewSetGroup):
    items = (
        DaisyUIThemeViewSet,
        DaisyUIMenuViewSet,
        ReusableBlockViewSet,
        DaisyUIIconSourceViewSet,
        DaisyUIFaviconViewSet,
        FeedViewSet,
    )
    menu_icon = "palette"
    menu_label = "Design"
    menu_name = "design"
    add_to_admin_menu = True
    submenu_hook = "register_daisyui_design_menu_item"
