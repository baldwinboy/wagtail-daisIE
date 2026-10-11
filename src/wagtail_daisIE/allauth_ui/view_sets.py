from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AllauthPageOverride


class AllauthPageOverrideViewSet(SnippetViewSet):
    icon = "lock"
    menu_label = "Authentication pages"
    model = AllauthPageOverride
    menu_hook = "register_daisyui_design_menu_item"
