"""Approval workflow callables for the demo."""

from datetime import date


def approve_bread_suggestion(suggestion):
    from blog.models import Bread

    bread, _created = Bread.objects.get_or_create(
        name=suggestion.title,
        defaults={
            "description": suggestion.description,
            "added_on": date.today(),
            "is_available": True,
        },
    )
    return bread
