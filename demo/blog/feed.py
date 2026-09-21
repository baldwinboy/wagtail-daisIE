"""Queryset for the blog feed.

Used by the ``blog_post`` context model so the Model list block shows live
posts (scoped to the current index) rather than every row.
"""

from blog.models import BlogIndexPage, BlogPage


def live_posts(request=None, page=None):
    queryset = (
        BlogPage.objects.live()
        .order_by("-date_published")
        .select_related("image")
    )
    if isinstance(page, BlogIndexPage):
        queryset = queryset.descendant_of(page)
    return queryset
