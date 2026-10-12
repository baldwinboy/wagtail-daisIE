"""A transparent block that renders a reusable email-content snippet.

Unlike the web reusable block there is no wrapper element: an ``mj-body`` only
accepts ``mj-section``/``mj-wrapper``/``mj-hero``/``mj-raw`` children, so this
simply inlines the referenced snippet's stored MJML blocks. The default
``StructBlock`` context copies ``parent_context``, which carries ``email_theme``,
the shared ``mjml_styles`` registry and the placeholder values into the inlined
blocks.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ...base_blocks.compact import DaisieStructBlock


class EmailReusableBlockBlock(DaisieStructBlock):
    reusable = SnippetChooserBlock("wagtail_daisIE_notifications.EmailReusableBlock")

    class Meta:
        icon = "mail"
        label = _("Reusable content")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/reusable.html"
        form_layout = blocks.BlockGroup(children=["reusable"])
