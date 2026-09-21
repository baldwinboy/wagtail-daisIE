from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel,
    HelpPanel,
    MultiFieldPanel,
)
from wagtail.fields import StreamField
from wagtail.models import (
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
)

from ..base_blocks import MenuItemDesignBlock
from ..blocks.menu_items import MenuBranding, MenuItemStreamBlock
from ..dynamic.blocks import CONTEXT_BINDING_BLOCKS
from ..dynamic.resolvers import parse_bindings, resolve_context_models
from ..notifications.context import build_context
from .theme import DaisyUITheme


LAYOUT_CHOICES = [
    ("navbar", _("Navbar")),
    ("footer", _("Footer")),
    ("sidebar", _("Sidebar")),
    ("horizontal", _("Horizontal menu")),
    ("vertical", _("Vertical menu")),
]


class DaisyUIMenu(
    LockableMixin,
    RevisionMixin,
    PreviewableMixin,
    ClusterableModel,
):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Name"),
        help_text=_(
            "A unique name used to render this menu in templates, e.g. "
            '{% daisyui_menu "Main navigation" %}.'
        ),
    )
    layout = models.CharField(
        max_length=32,
        choices=LAYOUT_CHOICES,
        default="navbar",
        verbose_name=_("Layout"),
        help_text=_(
            "How the menu is rendered: a top navbar, a footer, a sidebar "
            "drawer, or a standalone horizontal/vertical list."
        ),
    )

    # Branding
    branding = StreamField(
        [("branding", MenuBranding())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Branding"),
        help_text=_("Logo and/or wordmark, optionally wrapped in a link."),
    )

    # Search
    show_search = models.BooleanField(
        default=False,
        verbose_name=_("Show search box"),
        help_text=_("Display a search form in the navbar."),
    )
    search_url = models.CharField(
        max_length=255,
        blank=True,
        default="/search/",
        verbose_name=_("Search URL"),
        help_text=_("URL the search form submits to."),
    )
    search_parameter = models.CharField(
        max_length=64,
        blank=True,
        default="query",
        verbose_name=_("Search parameter"),
        help_text=_("Query-string parameter used for the search term."),
    )
    search_placeholder = models.CharField(
        max_length=128,
        blank=True,
        default=_("Search"),
        verbose_name=_("Search placeholder"),
    )

    # Theme
    menu_theme = models.ForeignKey(
        DaisyUITheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Menu theme"),
        help_text=_("Theme applied to this menu. Falls back to the default theme."),
    )
    show_theme_toggle = models.BooleanField(
        default=False,
        verbose_name=_("Show theme toggle"),
        help_text=_("Display a light/dark theme toggle in the navbar."),
    )
    alt_menu_theme = models.ForeignKey(
        DaisyUITheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Alternate theme"),
        help_text=_("Theme applied when the toggle is switched on."),
    )

    # Styling (settings panel)
    item_design = StreamField(
        [("item", MenuItemDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Menu item defaults"),
        help_text=_(
            "Default font, colour, background and spacing applied to every item. "
            "Per-item settings are applied on top."
        ),
    )
    sticky = models.BooleanField(
        default=False,
        verbose_name=_("Sticky navbar"),
        help_text=_("Keep the navbar fixed to the top of the viewport."),
    )

    body = StreamField(
        MenuItemStreamBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Menu items"),
        help_text=_("Add links, buttons, accordions and other menu components."),
    )

    context_bindings = StreamField(
        CONTEXT_BINDING_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name=_("Context bindings"),
        help_text=_(
            "Expose context models to this menu's items, e.g. the current user."
        ),
    )

    revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="daisyui_menu",
        for_concrete_model=False,
    )

    panels = [
        HelpPanel(template="wagtail_daisIE/admin/menu_help.html"),
        FieldPanel("name"),
        FieldPanel("layout"),
        FieldPanel("branding"),
        MultiFieldPanel(
            [
                FieldPanel("show_search"),
                FieldPanel("search_url"),
                FieldPanel("search_parameter"),
                FieldPanel("search_placeholder"),
            ],
            heading=_("Search"),
            classname="collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_theme_toggle"),
                FieldPanel("alt_menu_theme"),
            ],
            heading=_("Theme toggle"),
            classname="collapsed",
        ),
        FieldPanel("body"),
        FieldPanel("context_bindings"),
    ]

    styling_panels = [
        FieldPanel("menu_theme"),
        FieldPanel("item_design"),
        FieldPanel("sticky"),
    ]

    class Meta:
        verbose_name = _("DaisyUI Menu")
        verbose_name_plural = _("DaisyUI Menus")

    def __str__(self):
        return self.name

    def get_theme(self):
        """Return this menu's theme, falling back to the default theme."""
        return self.menu_theme or DaisyUITheme.objects.filter(default=True).first()

    def get_item_css(self):
        """Return the CSS classes contributed by ``item_design``."""
        from ..base_blocks.css import build_design_css

        first = self.item_design[0].value if self.item_design else None
        return build_design_css(first)

    def get_preview_template(self, request, mode_name):
        return "wagtail_daisIE/previews/menu.html"

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        theme = self.get_theme()
        context["menu"] = self
        context["menu_items"] = self.body
        context["request"] = request
        context["daisyui_theme"] = theme
        context["menu_theme"] = theme
        context["menu_item_css"] = self.get_item_css()
        context.update(build_context(request=request))
        context.update(
            resolve_context_models(
                request,
                bindings=parse_bindings(self),
            )
        )
        return context
