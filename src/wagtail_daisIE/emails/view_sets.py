from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import ObjectList, TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import EmailTemplate


class EmailTemplateViewSet(SnippetViewSet):
    icon = "mail"
    menu_label = "Templates"
    model = EmailTemplate

    edit_handler = TabbedInterface(
        [
            ObjectList(EmailTemplate.panels, heading=_("Content")),
            ObjectList(EmailTemplate.styling_panels, heading=_("Settings")),
        ]
    )


class EmailViewSetGroup(SnippetViewSetGroup):
    items = [EmailTemplateViewSet]
    menu_icon = "mail"
    menu_label = "Emails"
    menu_name = "emails"
    add_to_admin_menu = True
