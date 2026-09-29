from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import InlinePanel, ObjectList, TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Audience, EmailCampaign, EmailTemplate


class EmailViewSetGroup(SnippetViewSetGroup):
    menu_icon = "mail"
    menu_label = "Emails"
    menu_name = "emails"
    add_to_admin_menu = True
    submenu_hook = "register_email_submenu"


class EmailTemplateViewSet(SnippetViewSet):
    icon = "palette"
    menu_label = "Templates"
    model = EmailTemplate
    menu_hook = "register_email_submenu"

    edit_handler = TabbedInterface(
        [
            ObjectList(EmailTemplate.panels, heading=_("Content")),
            ObjectList(EmailTemplate.styling_panels, heading=_("Settings")),
        ]
    )


class AudienceViewSet(SnippetViewSet):
    icon = "group"
    menu_label = "Audiences"
    model = Audience
    menu_hook = "register_email_submenu"
    edit_handler = TabbedInterface(
        [
            ObjectList(Audience.panels, heading=_("Content")),
            ObjectList(
                [InlinePanel("members", label=_("Members"))],
                heading=_("Members"),
            ),
        ]
    )


class EmailCampaignViewSet(SnippetViewSet):
    icon = "mail"
    menu_label = "Campaigns"
    model = EmailCampaign
    menu_hook = "register_email_submenu"
