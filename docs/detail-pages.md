# Model detail pages

A **detail page** is generated automatically from a model record and kept in
sync with it: creating, updating or deleting the record creates, refreshes or
deletes its page. The page's design is controlled from a single **shared design
page**, so styling every record means editing one page.

This builds on [context models](context-models.md) and uses the URL-binding
machinery (path parameters) to view the current record.

A detail type uses three pages:

| Role | Page type | Purpose |
|------|-----------|---------|
| Feed / listing | a normal `StyledPageMixin` page (e.g. `BreadIndexPage`) | Navigable page under Home that lists records with a Feed block and links to generated pages. Also the parent of those pages, so URLs are `/breads/<slug>/`. |
| Shared design | a `ModelDetailTemplate` subclass | Non-navigable, slug-less page under Home holding the theme, background, design, body and bindings. |
| Generated detail | a `ModelDetailPage` subclass | One page per record, created and kept in sync automatically. |

## Declaring detail pages

```python
# settings.py
WAGTAIL_DAISIE_DETAIL_PAGES = {
    "bread": {
        "label": "Bread",
        "model": "blog.Bread",
        "page_type": "blog.BreadDetailPage",  # your Page subclass
        "parent": "blog.BreadIndexPage",  # where new pages are added
        "template_page": "blog.BreadDetailTemplate",  # shared design
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
| `parent` | The page (or its model) new pages are added under. The design page's **Generated pages live under** chooser overrides it. |
| `template_page` | The page whose design is inherited (defaults to `parent`). |
| `lookup_field` / `lookup_in` | How `{{ key }}` resolves on the page (see above). |
| `publish_field` | Publish the page only when this model field is truthy. |
| `title_source` / `slug_source` | Model attributes used for the page title/slug. |
| `on_delete` | `"page"` (default), `"unlink"` or `"ignore"`. |

## Defining the page types

```python
from wagtail_daisIE.detail_pages.models import ModelDetailPage, ModelDetailTemplate
from wagtail_daisIE.pages import StyledPageMixin


class BreadIndexPage(StyledPageMixin):
    """Navigable listing: holds a Feed block and links to each record."""

    template = "blog/bread_index_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BreadDetailPage"]


class BreadDetailTemplate(ModelDetailTemplate):
    """Shared, non-navigable design for the generated pages."""

    template = "blog/bread_detail_template.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = []


class BreadDetailPage(ModelDetailPage):
    template = "blog/bread_detail_page.html"
    parent_page_types = ["blog.BreadIndexPage"]
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

`ModelDetailTemplate` is a `StyledPageMixin` page, but it is a **design container
only**: give it a theme, background, **Page default design**, body blocks and
**Context bindings** (for example a `bread` binding with `lookup_in: path`).

It is deliberately **not navigable**: `get_url_parts()` returns `None` (so it has
no URL and nothing links to it), a direct request raises `404`, and its slug is
hidden and auto-generated from the title. Use its **Generated pages live under**
chooser to pick the feed/listing page; generated pages are added there, so their
URLs are the listing page's (e.g. `/breads/<slug>/`). When the chooser is empty,
the settings `parent` is used.

Every generated page inherits the template's design at request time, so editing
the template restyles all instances. Each generated page has a **Use shared
design** toggle; turn it off to give one page its own theme/design/bindings.

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
