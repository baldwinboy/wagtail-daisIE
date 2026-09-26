"""Abstract page types for model detail pages and shared design templates."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page

from ..dynamic.resolvers import parse_bindings, resolve_context_models
from ..pages import StyledPageMixin


class ModelDetailTemplate(StyledPageMixin):
    """One page whose design is reused by a detail type's generated pages."""

    detail_key = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_("Detail type"),
        help_text=_("The key from WAGTAIL_DAISIE_DETAIL_PAGES this design serves."),
    )

    content_panels = StyledPageMixin.content_panels + [FieldPanel("detail_key")]

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class ModelDetailPage(StyledPageMixin):
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
    design_template = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Shared design page"),
    )
    use_template_design = models.BooleanField(
        default=True,
        verbose_name=_("Use shared design"),
        help_text=_(
            "Inherit theme, background, layout and bindings from the shared "
            "design page."
        ),
    )

    content_panels = StyledPageMixin.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("design_template"),
                FieldPanel("use_template_design"),
            ],
            heading=_("Detail page"),
            classname="collapsed",
        ),
    ]

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["detail_key", "source_content_type", "source_object_id"],
                name="%(app_label)s_%(class)s_unique_detail_source",
            )
        ]

    def get_design_source(self):
        """Return the page whose design this page renders with."""
        if self.use_template_design:
            template = self.design_template
            if template is not None and template.pk != self.pk:
                return template.specific
        return self

    def get_context(self, request, *args, **kwargs):
        request.daisie_path_params = {
            "pk": str(self.source_object_id or ""),
            "slug": self.slug,
            **(getattr(request, "daisie_path_params", None) or {}),
        }
        context = super().get_context(request, *args, **kwargs)
        source = self.get_design_source()
        if source is not self:
            context["daisyui_theme"] = source.get_daisyui_theme()
            context["daisyui_page_background_css"] = source.get_page_background_css()
            for category, css in source.get_page_design_css().items():
                context[f"{category}_css"] = css
            bindings = {**parse_bindings(source), **parse_bindings(self)}
            context.update(resolve_context_models(request, self, bindings=bindings))
        return context
