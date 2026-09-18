from django.db import OperationalError, ProgrammingError, models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from wagtail_daisIE.base_blocks import BackgroundStreamBlock, PageDesignBlock
from wagtail_daisIE.blocks.content import ContentBlock
from wagtail_daisIE.models import DaisyUITheme


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


class StyledPageMixin(Page):
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

    class Meta:
        abstract = True

    content_panels = [
        *Page.content_panels,
        FieldPanel("page_theme"),
        FieldPanel("page_background"),
        FieldPanel("page_design"),
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
        for category, css in self.get_page_design_css().items():
            context[f"{category}_css"] = css
        return context
