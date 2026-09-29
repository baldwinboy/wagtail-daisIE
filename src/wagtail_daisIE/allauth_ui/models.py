"""Admin-designed django-allauth account pages.

An :class:`AllauthPageOverride` binds an account view (e.g. ``account_login``)
to a DaisyUI-designed page: theme, background, page defaults, chrome menus and
a full body composed of normal content blocks plus ``auth_form`` / ``auth_field``
blocks. Authors control the look only; allauth owns the fields and validation.

Only the ``account`` view set is supported for now — see
``docs/allauth-pages.md``.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import PreviewableMixin

from ..base_blocks import BackgroundStreamBlock, PageDesignBlock
from .blocks import ALLAUTH_FORM_ID, ALLAUTH_PAGE_BLOCKS
from .catalogue import get_allauth_view_choices, sample_form


class AllauthPageOverride(PreviewableMixin, ClusterableModel):
    """Per-view, per-site design for an allauth account page."""

    view = models.CharField(
        max_length=128,
        unique=True,
        choices=get_allauth_view_choices,
        verbose_name=_("Account page"),
        help_text=_("The allauth account view this design applies to."),
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Active"),
        help_text=_("Only active overrides are used."),
    )
    site = models.ForeignKey(
        "wagtailcore.Site",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Site"),
        help_text=_("Leave empty to use this as the global fallback."),
    )
    theme = models.ForeignKey(
        "wagtail_daisIE.DaisyUITheme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Theme"),
        help_text=_("Theme used to style this page. Falls back to the default."),
    )
    page_background = StreamField(
        BackgroundStreamBlock(),
        blank=True,
        verbose_name=_("Background"),
        help_text=_("Background layers for this page."),
    )
    page_design = StreamField(
        [("defaults", PageDesignBlock())],
        blank=True,
        max_num=1,
        verbose_name=_("Page default design"),
        help_text=_(
            "Default container, text, button and media styles applied to every "
            "block on this page."
        ),
    )
    header_menu = models.ForeignKey(
        "wagtail_daisIE_menus.DaisyUIMenu",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Header menu"),
    )
    footer_menu = models.ForeignKey(
        "wagtail_daisIE_menus.DaisyUIMenu",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Footer menu"),
    )
    body = StreamField(
        ALLAUTH_PAGE_BLOCKS,
        blank=True,
        verbose_name=_("Body"),
        help_text=_(
            "Compose the page. Place an Account form block for the form and "
            "individual form fields anywhere between content blocks."
        ),
    )

    panels = [
        FieldPanel("view"),
        MultiFieldPanel(
            [FieldPanel("is_active"), FieldPanel("site")],
            heading=_("Settings"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("theme"),
                FieldPanel("page_background"),
                FieldPanel("page_design"),
                FieldPanel("header_menu"),
                FieldPanel("footer_menu"),
            ],
            heading=_("Design"),
            classname="collapsed",
        ),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = _("Allauth page override")
        verbose_name_plural = _("Allauth page overrides")
        ordering = ["view"]

    def __str__(self):
        return self.get_view_display() or self.view

    @classmethod
    def ensure_defaults(cls):
        """Create an (inactive) row for every discovered account view."""
        for view, _label in get_allauth_view_choices():
            cls.objects.get_or_create(view=view)

    @classmethod
    def get_active(cls, view, site=None):
        """Return the active override for ``view``/``site``, or ``None``."""
        if not view:
            return None
        queryset = cls.objects.filter(view=view, is_active=True)
        if site is not None:
            row = queryset.filter(site=site).first()
            if row is not None:
                return row
        return queryset.filter(site__isnull=True).first()

    # -- design helpers (mirror StyledPageMixin) --------------------------

    def get_background_css(self):
        if not self.page_background:
            return ""
        return BackgroundStreamBlock().get_css(self.page_background)

    def get_page_design_css(self):
        first = self.page_design[0].value if self.page_design else None
        if not first:
            return {}
        return PageDesignBlock().get_default_css(first)

    # -- previewing -------------------------------------------------------

    def get_preview_template(self, request, mode_name):
        return "wagtail_daisIE/allauth/preview.html"

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context.update(
            {
                "override": self,
                "form": sample_form(self.view),
                "form_id": ALLAUTH_FORM_ID,
                "request": request,
            }
        )
        return context
