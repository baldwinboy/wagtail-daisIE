from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import InlinePanel, ObjectList, TabbedInterface
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import AllauthEmailOverride, Audience, EmailCampaign


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


class AllauthEmailOverrideViewSet(SnippetViewSet):
    icon = "lock"
    menu_label = "Allauth emails"
    model = AllauthEmailOverride
    menu_hook = "register_email_submenu"
