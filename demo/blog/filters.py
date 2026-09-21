"""Filter option callables for the demo blog feed."""

from blog.models import Person
from taggit.models import Tag


def tags(request=None, page=None):
    return [
        {"value": tag.slug, "label": tag.name}
        for tag in Tag.objects.all().order_by("name")
    ]


def authors(request=None, page=None):
    return [
        {"value": person.pk, "label": str(person)}
        for person in Person.objects.all().order_by("last_name", "first_name")
    ]
