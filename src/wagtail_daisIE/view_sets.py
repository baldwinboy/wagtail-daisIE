from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import ObjectList, TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .dynamic.view_sets import FeedViewSet
from .models import DaisyUIIconSource, DaisyUIMenu, DaisyUITheme


class DaisyUIThemeViewSet(SnippetViewSet):
    icon = "cogs"
    menu_label = "Themes"
    model = DaisyUITheme


class DaisyUIMenuViewSet(SnippetViewSet):
    icon = "list-ul"
    menu_label = "Menus"
    model = DaisyUIMenu

    edit_handler = TabbedInterface(
        [
            ObjectList(DaisyUIMenu.panels, heading=_("Content")),
            ObjectList(DaisyUIMenu.styling_panels, heading=_("Settings")),
        ]
    )


class DaisyUIIconSourceViewSet(SnippetViewSet):
    icon = "image"
    menu_label = "Icon Sources"
    model = DaisyUIIconSource


class DaisyUIViewSetGroup(SnippetViewSetGroup):
    items = (
        DaisyUIThemeViewSet,
        DaisyUIMenuViewSet,
        DaisyUIIconSourceViewSet,
        FeedViewSet,
    )
    menu_icon = "palette"
    menu_label = "Design"
    menu_name = "design"
    add_to_admin_menu = True
