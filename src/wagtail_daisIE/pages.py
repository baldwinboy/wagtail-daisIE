from django.db import OperationalError, ProgrammingError, models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from wagtail_daisIE.base_blocks import (
    AudienceBlock,
    BackgroundStreamBlock,
    PageDesignBlock,
)
from wagtail_daisIE.blocks.content import ContentBlock
from wagtail_daisIE.models import DaisyUITheme

from .base_blocks.audience import PageAudienceMixin
from .dynamic.blocks import CONTEXT_BINDING_BLOCKS
from .dynamic.mixins import DaisieContextMixin


def get_default_theme_id():
    """Return the primary key of the default DaisyUI theme, if one exists.

    Used as a lazy FK default so new pages offer the default theme in the
    admin without querying the database at import time.

    The schema editor evaluates concrete field defaults while applying
    migrations, so this must tolerate the theme table/column not existing yet.
    """
    try:
        return (
            DaisyUITheme.objects.filter(default=True)
            .values_list("pk", flat=True)
            .first()
        )
    except (OperationalError, ProgrammingError):
        return None


class StyledPageMixin(PageAudienceMixin, DaisieContextMixin, Page):
    """
    Optional per-page background overrides. If empty, the page inherits the
    site-wide background from the DaisyUI theme.
    """

    page_theme = models.ForeignKey(
        DaisyUITheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        default=get_default_theme_id,
        help_text=_("Select a DaisyUI theme to style this page"),
    )

    page_background = StreamField(
        BackgroundStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text=_(
            "Add background blocks to override the site-wide design for this page.",
        ),
    )

    page_design = StreamField(
        [("defaults", PageDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Page default design"),
        help_text=_(
            "Default container, text, button and media styles applied to every "
            "block on this page. Per-block settings are applied on top."
        ),
    )

    body = StreamField(
        ContentBlock(),
        blank=True,
        use_json_field=True,
        help_text=_("Add content blocks to build out the page body."),
    )

    context_bindings = StreamField(
        CONTEXT_BINDING_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name=_("Context bindings"),
        help_text=_(
            "Expose configured context models to this page, either from the URL "
            "or pinned to a specific instance."
        ),
    )

    audience = StreamField(
        [("audience", AudienceBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Audience"),
        help_text=_("Only allow access to the selected audiences."),
    )
    audience_denied = models.CharField(
        max_length=10,
        choices=[
            ("403", _("Show a 403 page")),
            ("404", _("Show a 404 page")),
            ("redirect", _("Redirect to a page")),
        ],
        default="403",
        verbose_name=_("When access is denied"),
    )
    audience_denied_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Redirect target"),
        help_text=_("Used when the denial behaviour is redirect."),
    )

    class Meta:
        abstract = True

    content_panels = [
        *Page.content_panels,
        FieldPanel("page_theme"),
        FieldPanel("page_background"),
        FieldPanel("page_design"),
        FieldPanel("audience"),
        MultiFieldPanel(
            [
                FieldPanel("audience_denied"),
                FieldPanel("audience_denied_page"),
            ],
            heading=_("Audience access"),
            classname="collapsed",
        ),
        FieldPanel("context_bindings"),
        FieldPanel("body"),
    ]

    def get_daisyui_theme(self):
        return self.page_theme or DaisyUITheme.objects.filter(default=True).first()

    def get_page_background_css(self):
        """Return the CSS ``background`` value for this page's background layers."""
        if not self.page_background:
            return ""
        return BackgroundStreamBlock().get_css(self.page_background)

    def get_page_design_css(self):
        """Return a ``{category: css}`` mapping for this page's default design."""
        first = self.page_design[0].value if self.page_design else None
        if not first:
            return {}
        return PageDesignBlock().get_default_css(first)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["daisyui_theme"] = self.get_daisyui_theme()
        context["daisyui_page_background_css"] = self.get_page_background_css()
        context["page_audience_allowed"] = self.page_audience_allowed(request)
        for category, css in self.get_page_design_css().items():
            context[f"{category}_css"] = css
        self.add_daisie_context(request, context)
        return context
