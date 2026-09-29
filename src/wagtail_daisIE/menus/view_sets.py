from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import ObjectList, TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import DaisyUIMenu


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
