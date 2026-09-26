# Model detail pages

A **detail page** is generated automatically from a model record and kept in
sync with it: creating, updating or deleting the record creates, refreshes or
deletes its page. The page's design is controlled from a single **shared design
page**, so styling every record means editing one page.

This builds on [context models](context-models.md) and uses the URL-binding
machinery (path parameters) to view the current record.

## Declaring detail pages

```python
# settings.py
WAGTAIL_DAISIE_DETAIL_PAGES = {
    "bread": {
        "label": "Bread",
        "model": "blog.Bread",
        "page_type": "blog.BreadDetailPage",  # your Page subclass
        "parent": "blog.BreadDetailTemplate",  # where new pages are added
        "template_page": "blog.BreadDetailTemplate",  # shared design (optional)
        "lookup_field": "slug",
        "lookup_in": "path",
        "publish_field": "is_available",
        "title_source": "name",
        "slug_source": "name",
    },
}
```

| Key | Description |
|-----|-------------|
| `model` | `"app_label.ModelName"` or dotted path. |
| `page_type` | The `ModelDetailPage` subclass to create. |
| `parent` | The page (or its model) new pages are added under. |
| `template_page` | The page whose design is inherited (defaults to `parent`). |
| `lookup_field` / `lookup_in` | How `{{ key }}` resolves on the page (see above). |
| `publish_field` | Publish the page only when this model field is truthy. |
| `title_source` / `slug_source` | Model attributes used for the page title/slug. |
| `on_delete` | `"page"` (default), `"unlink"` or `"ignore"`. |

## Defining the page types

```python
from wagtail_daisIE.detail_pages.models import ModelDetailPage, ModelDetailTemplate


class BreadDetailTemplate(ModelDetailTemplate):
    template = "blog/bread_detail_template.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BreadDetailPage"]


class BreadDetailPage(ModelDetailPage):
    template = "blog/bread_detail_page.html"
    parent_page_types = ["blog.BreadDetailTemplate"]
    subpage_types = []
```

Add a reverse link on the model so admins can jump to the page and links resolve
automatically:

```python
from django.contrib.contenttypes.fields import GenericRelation


class Bread(models.Model):
    # ...
    detail_pages = GenericRelation(
        "blog.BreadDetailPage",
        content_type_field="source_content_type",
        object_id_field="source_object_id",
        related_query_name="bread_detail_pages",
    )

    def get_absolute_url(self):
        page = self.detail_pages.filter(live=True).first()
        return page.get_url() if page else f"/breads/#bread-{self.pk}"
```

`url_for_object()` already falls back to `get_absolute_url()`, so
`{{ bread.url }}` links start working with no template changes.

## The shared design page

`ModelDetailTemplate` is a normal `StyledPageMixin` page: give it a theme,
background, **Page default design**, body blocks and **Context bindings** (for
example a `bread` binding with `lookup_in: path`). Every generated page inherits
that design at request time, so editing the template restyles all instances.

Each generated page has a **Use shared design** toggle; turn it off to give one
page its own theme/design/bindings.

## Lifecycle

* **Create** — the page is created as a draft, then published only when
  `publish_field` is truthy.
* **Update** — the same page is refreshed; `post_save` never clobbers editorial
  changes beyond the title, slug and source link.
* **Delete** — the page is deleted in `pre_delete` (via `Page.delete()`), so the
  Wagtail tree stays consistent even though `GenericRelation` cascades.

## Admin

Generated pages are not creatable by hand (`is_creatable = False`). Page listings
gain an **Edit source record** button, and snippet listings gain a **View detail
page** button.
