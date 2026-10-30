"""Abstract page types for model detail pages and shared design templates."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TitleFieldPanel
from wagtail.models import Page, PanelPlaceholder

from ..dynamic.resolvers import parse_bindings, resolve_context_models
from ..pages import StyledPageMixin
from .exceptions import DetailPageConfigurationError


def _is_title_panel(panel):
    """True for the title panel, including ``Page``'s unexpanded placeholder."""
    return isinstance(panel, TitleFieldPanel) or (
        isinstance(panel, PanelPlaceholder) and panel.panel_class is TitleFieldPanel
    )


class ModelDetailTemplate(StyledPageMixin):
    """A non-navigable page holding the shared design for a detail type."""

    max_count = 1

    detail_key = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_("Detail type"),
        help_text=_("The key from WAGTAIL_DAISIE_DETAIL_PAGES this design serves."),
    )
    parent_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Generated pages live under"),
        help_text=_("Where pages generated for this detail type are added."),
    )

    content_panels = [
        FieldPanel("title"),
        *[
            panel
            for panel in StyledPageMixin.content_panels
            if not _is_title_panel(panel)
        ],
        FieldPanel("detail_key"),
        FieldPanel("parent_page"),
    ]

    # Hide the slug; Wagtail auto-generates it from the title
    # (_set_core_field_defaults, wagtail/models/pages.py:700-722).
    promote_panels = [
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("search_description")],
            _("For search engines"),
        ),
    ]

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def get_url_parts(self, request=None):
        """Return ``None``: the design page is never navigable."""
        return None

    def serve(self, request, *args, **kwargs):
        raise Http404


class GeneratedPagesIndexPage(Page):
    """Admin-only container for generated detail pages."""

    is_creatable = False
    max_count = 1

    class Meta:
        abstract = True

    def get_url_parts(self, request=None):
        """Return ``None``: the generated index is never navigable."""
        return None

    def serve(self, request, *args, **kwargs):
        raise Http404


class GeneratedPagesRouteMixin:
    """Route public URLs into a child generated-index page.

    Generated pages live under an admin-only index, so the public tree path
    would normally include that index. This mixin lets the listing page route
    ``/<detail-slug>/`` directly into the generated index's children.
    """

    def route(self, request, path_components):
        if path_components:
            for child in self.get_children().specific():
                if isinstance(child, GeneratedPagesIndexPage):
                    try:
                        return child.route(request, path_components)
                    except Http404:
                        continue
        return super().route(request, path_components)


class ModelDetailPage(Page):
    """A page generated from, and kept in sync with, a model instance."""

    is_creatable = False

    detail_key = models.CharField(max_length=64, db_index=True)
    source_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Source model"),
    )
    source_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Source record"),
    )
    source = GenericForeignKey("source_content_type", "source_object_id")

    content_panels = Page.content_panels

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["detail_key", "source_content_type", "source_object_id"],
                name="%(app_label)s_%(class)s_unique_detail_source",
            )
        ]

    def get_template_page(self):
        """Return the single shared template page, or raise."""
        from .registry import get_detail_page

        config = get_detail_page(self.detail_key)
        if config is None:
            raise DetailPageConfigurationError(
                f"No detail-page configuration for {self.detail_key!r}."
            )
        return config.get_template_page()

    def get_context(self, request, *args, **kwargs):
        request.daisie_path_params = {
            "pk": str(self.source_object_id or ""),
            "slug": self.slug,
            **(getattr(request, "daisie_path_params", None) or {}),
        }
        template = self.get_template_page()
        context = super().get_context(request, *args, **kwargs)
        context["detail_template"] = template
        context["detail_template_body"] = template.body
        context["daisyui_theme"] = template.get_daisyui_theme()
        context["daisyui_page_background_css"] = template.get_page_background_css()
        context["daisyui_main_css"] = template.get_main_design_css()
        context["daisyui_main_style"] = template.get_main_design_style()
        for category, css in template.get_page_design_css().items():
            context[f"{category}_css"] = css
        context.update(
            resolve_context_models(request, self, bindings=parse_bindings(template))
        )
        return context

    def serve(self, request, *args, **kwargs):
        template = self.get_template_page()
        if not template.page_audience_allowed(request):
            return template.audience_denied_response(request)
        return super().serve(request, *args, **kwargs)

    def get_url_parts(self, request=None):
        """Return the public URL parts, omitting the generated-index segment."""
        parent = self.get_parent()
        if parent is None:
            return None
        parent = parent.specific
        if not isinstance(parent, GeneratedPagesIndexPage):
            raise DetailPageConfigurationError(
                f"{self!r} must be a child of a GeneratedPagesIndexPage."
            )
        url_parent = parent.get_parent()
        if url_parent is None:
            return None
        parts = url_parent.specific.get_url_parts(request)
        if parts is None:
            return None
        site_id, root_url, page_path = parts
        return site_id, root_url, f"{page_path}{self.slug}/"
