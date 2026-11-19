from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Feed


class FeedViewSet(SnippetViewSet):
    icon = "list-ul"
    menu_label = "Feeds"
    model = Feed
    list_display = ["title", "name", "context_model", "layout"]
    search_fields = ["title", "name"]
