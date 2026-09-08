from wagtail.models import Page

from wagtail_daisIE.pages import StyledPageMixin


class HomePage(StyledPageMixin):
    content_panels = StyledPageMixin.content_panels

    subpage_types = ["blog.BlogIndexPage"]

    parent_page_types = ["wagtailcore.Page"]
