from wagtail.models import Page

from wagtail_daisIE.pages import StyledPageMixin


class HomePage(StyledPageMixin):
    content_panels = StyledPageMixin.content_panels

    subpage_types = [
        "blog.BlogIndexPage",
        "blog.BreadSuggestionFormPage",
        "home.DemoPage",
    ]

    parent_page_types = ["wagtailcore.Page"]


class DemoPage(StyledPageMixin):
    """A generic page used to demonstrate the editor's features."""

    content_panels = StyledPageMixin.content_panels

    template = "home/demo_page.html"

    parent_page_types = ["home.HomePage"]
    subpage_types = []
