from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AllauthPageOverride


class AllauthPageOverrideViewSet(SnippetViewSet):
    icon = "lock"
    menu_label = "Allauth pages"
    model = AllauthPageOverride
