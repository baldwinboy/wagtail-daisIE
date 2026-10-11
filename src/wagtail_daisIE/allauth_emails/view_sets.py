from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AllauthEmailOverride


class AllauthEmailOverrideViewSet(SnippetViewSet):
    icon = "lock"
    menu_label = "Authentication emails"
    model = AllauthEmailOverride
    menu_hook = "register_email_submenu"
