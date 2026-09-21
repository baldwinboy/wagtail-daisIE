from django.utils.translation import gettext_lazy as _
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import ErrorPage


class ErrorPageViewSet(SnippetViewSet):
    icon = "warning"
    menu_label = "Error pages"
    model = ErrorPage


class ErrorViewSetGroup(SnippetViewSetGroup):
    items = [ErrorPageViewSet]
    menu_icon = "warning"
    menu_label = _("Errors")
    menu_name = "errors"
    add_to_admin_menu = True
