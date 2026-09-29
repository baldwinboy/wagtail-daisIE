"""In-admin editor guide ("DaisyUI Editor Guide").

Structured like Wagtail's own user guide: Getting started, Concepts, How-to and
Reference. Each topic is a separate page; the navigation and prev/next links are
derived from :data:`GUIDE_SECTIONS`.
"""

from django.apps import apps
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin


GUIDE_SECTIONS = [
    {
        "slug": "getting-started",
        "title": _("Getting started"),
        "pages": [
            {
                "slug": "overview",
                "title": _("Overview"),
                "summary": _("What the editor adds, and where to find every setting."),
            },
        ],
    },
    {
        "slug": "concepts",
        "title": _("Concepts"),
        "pages": [
            {
                "slug": "concepts-blocks",
                "title": _("Pages and blocks"),
                "summary": _("How page content is assembled from blocks."),
            },
            {
                "slug": "concepts-design",
                "title": _("Design and typography"),
                "summary": _(
                    "How size, spacing, colour and type settings work together."
                ),
            },
            {
                "slug": "concepts-themes",
                "title": _("Themes"),
                "summary": _("Site-wide colours and fonts, and dark mode."),
            },
            {
                "slug": "concepts-audiences",
                "title": _("Audiences"),
                "summary": _("Showing content only to some visitors."),
            },
            {
                "slug": "concepts-context",
                "title": _("Context values"),
                "summary": _("Using {{ … }} values from your site's data."),
            },
            {
                "slug": "concepts-data",
                "title": _("Feeds and data"),
                "summary": _("Listing records from a model on a page."),
                "requires": "wagtail_daisIE.feeds",
            },
            {
                "slug": "concepts-email",
                "title": _("Emails"),
                "summary": _("Templates, audiences and campaigns."),
                "requires": "wagtail_daisIE.notifications",
            },
        ],
    },
    {
        "slug": "how-to",
        "title": _("How-to guides"),
        "pages": [
            {
                "slug": "find-your-way",
                "title": _("Find your way around"),
                "summary": _("The page editor and the Design menu."),
            },
            {
                "slug": "build-a-page",
                "title": _("Build a page"),
                "summary": _("Add, reorder and remove blocks in a page body."),
            },
            {
                "slug": "style-a-block",
                "title": _("Style a block"),
                "summary": _("Use the Design and Typography panels."),
            },
            {
                "slug": "page-defaults",
                "title": _("Page defaults and layout"),
                "summary": _(
                    "Set page-wide defaults, the main container and background."
                ),
            },
            {
                "slug": "text-blocks",
                "title": _("Text"),
                "summary": _("Headings, text, rich text and quotes."),
            },
            {
                "slug": "media-blocks",
                "title": _("Media"),
                "summary": _("Images, embeds and galleries."),
            },
            {
                "slug": "layout-blocks",
                "title": _("Layout"),
                "summary": _("Rows, columns, grids, tabs, carousels and more."),
            },
            {
                "slug": "display-blocks",
                "title": _("Display"),
                "summary": _("Badges, avatars, stats, timelines and mockups."),
            },
            {
                "slug": "feedback-and-input-blocks",
                "title": _("Feedback and inputs"),
                "summary": _("Alerts, progress, and every form input block."),
            },
            {
                "slug": "buttons-and-actions",
                "title": _("Buttons and actions"),
                "summary": _("Links, buttons and record actions."),
            },
            {
                "slug": "menus",
                "title": _("Menus"),
                "summary": _("Build and style the site navigation."),
                "requires": "wagtail_daisIE.menus",
            },
            {
                "slug": "feeds",
                "title": _("Feeds"),
                "summary": _("List records with filters and custom cards."),
                "requires": "wagtail_daisIE.feeds",
            },
            {
                "slug": "calendar",
                "title": _("Calendars"),
                "summary": _("Show records on a calendar."),
                "requires": "wagtail_daisIE.feeds",
            },
            {
                "slug": "forms",
                "title": _("Forms"),
                "summary": _("Collect submissions and create records."),
            },
            {
                "slug": "emails",
                "title": _("Emails"),
                "summary": _("Design templates and send campaigns."),
                "requires": "wagtail_daisIE.notifications",
            },
            {
                "slug": "icons-and-favicon",
                "title": _("Icons and favicon"),
                "summary": _("Icon sources, the chooser, and site icons."),
                "requires": "wagtail_daisIE.assets",
            },
            {
                "slug": "error-pages",
                "title": _("Error pages"),
                "summary": _("Design 403, 404 and 500 pages."),
                "requires": "wagtail_daisIE.errors",
            },
            {
                "slug": "account-pages",
                "title": _("Account pages"),
                "summary": _("Style allauth sign-in and account screens."),
                "requires": "wagtail_daisIE.allauth_ui",
            },
            {
                "slug": "audiences",
                "title": _("Restrict content by audience"),
                "summary": _("One-page how-to for gating content."),
            },
            {
                "slug": "context-models",
                "title": _("Use context values"),
                "summary": _("One-page how-to for {{ … }} values."),
            },
        ],
    },
    {
        "slug": "reference",
        "title": _("Reference"),
        "pages": [
            {
                "slug": "block-reference",
                "title": _("Block reference"),
                "summary": _("Every block, grouped by category."),
            },
            {
                "slug": "design-reference",
                "title": _("Design reference"),
                "summary": _("Every design and typography option."),
            },
            {
                "slug": "theme-reference",
                "title": _("Theme reference"),
                "summary": _("Every theme setting."),
            },
            {
                "slug": "markup-and-placeholders",
                "title": _("Markup and placeholders"),
                "summary": _("Bold, italic, links and {{ … }} expressions."),
            },
            {
                "slug": "accessibility",
                "title": _("Accessibility"),
                "summary": _("Writing and designing accessible pages."),
            },
            {
                "slug": "glossary",
                "title": _("Glossary"),
                "summary": _("Key terms used in this guide."),
            },
        ],
    },
]


def _visible_sections():
    """Return GUIDE_SECTIONS with pages filtered by installed apps."""
    sections = []
    for section in GUIDE_SECTIONS:
        pages = [
            page
            for page in section["pages"]
            if not page.get("requires") or apps.is_installed(page["requires"])
        ]
        if pages:
            sections.append({**section, "pages": pages})
    return sections


def _index_pages(sections):
    return [(section, page) for section in sections for page in section["pages"]]


class GuideIndexView(WagtailAdminTemplateMixin, TemplateView):
    template_name = "wagtail_daisIE/help/index.html"
    page_title = _("DaisyUI Editor Guide")
    header_icon = "help"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "sections": _visible_sections(),
        }

    def get_breadcrumbs_items(self):
        return [
            *self.breadcrumbs_items,
            {
                "url": reverse("wagtail_daisIE:guide"),
                "label": _("DaisyUI Editor Guide"),
            },
        ]


class GuidePageView(WagtailAdminTemplateMixin, TemplateView):
    template_name = "wagtail_daisIE/help/page.html"
    header_icon = "help"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        index = _index_pages(_visible_sections())
        slugs = [page["slug"] for _section, page in index]
        slug = kwargs["slug"]
        if slug not in slugs:
            raise Http404
        position = slugs.index(slug)
        self.guide_index = index
        self.guide_position = position
        self.guide_section, self.guide_page = index[position]

    def get_context_data(self, **kwargs):
        position = self.guide_position
        index = self.guide_index
        context = {
            **super().get_context_data(**kwargs),
            "page_title": self.guide_page["title"],
            "guide_section": self.guide_section,
            "guide_page": self.guide_page,
            "sections": _visible_sections(),
            "page_template": (
                f"wagtail_daisIE/help/pages/{self.guide_page['slug']}.html"
            ),
            "prev_page": index[position - 1][1] if position else None,
            "next_page": (
                index[position + 1][1] if position + 1 < len(index) else None
            ),
        }
        if self.guide_page["slug"] == "block-reference":
            from .help_reference import build_block_reference

            context["block_reference"] = build_block_reference()
        return context

    def get_breadcrumbs_items(self):
        return [
            *self.breadcrumbs_items,
            {
                "url": reverse("wagtail_daisIE:guide"),
                "label": _("DaisyUI Editor Guide"),
            },
            {"label": self.guide_section["title"]},
            {"label": self.guide_page["title"]},
        ]
