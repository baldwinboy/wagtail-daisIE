"""Filter option callables for the demo blog feed."""

from blog.models import Person
from taggit.models import Tag


def tags(request=None, page=None):
    return [
        {"value": tag.slug, "label": tag.name}
        for tag in Tag.objects.all().order_by("name")
    ]


def tag_queryset(request=None, page=None):
    """Queryset of all tags, used by the autocomplete block's model source."""
    return Tag.objects.all().order_by("name")


def tag_choices(field=None, context=None):
    """Choice callable for the demo ``tags`` form-field type."""
    return [{"value": tag.name, "label": tag.name} for tag in tag_queryset()]


def authors(request=None, page=None):
    return [
        {"value": person.pk, "label": str(person)}
        for person in Person.objects.all().order_by("last_name", "first_name")
    ]
