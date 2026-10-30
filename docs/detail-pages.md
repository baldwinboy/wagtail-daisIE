# Model detail pages

A **detail page** is generated automatically from a model record and kept in
sync with it: creating, updating or deleting the record creates, refreshes or
deletes its page. The page's content and design are controlled from a single
**shared template page**, so styling every record means editing one page.

This builds on [context models](context-models.md) and uses the URL-binding
machinery (path parameters) to view the current record.

A detail type uses four pages:

| Role | Page type | Purpose |
|------|-----------|---------|
| Listing / index | a normal `StyledPageMixin` page (e.g. `BreadIndexPage`) | Navigable page under Home that lists records with a Feed block. One per entity. |
| Shared template | a `ModelDetailTemplate` subclass | Non-navigable, slug-less page holding the theme, background, design, body and bindings. One per detail type. |
| Generated index | a `GeneratedPagesIndexPage` subclass | Admin-only container under the listing page. It is not publicly navigable. |
| Generated detail | a `ModelDetailPage` subclass | One page per public record, created under the generated index. |

Public detail URLs keep the listing prefix, for example `/breads/<slug>/`.
The generated-index segment is never part of the public URL.

## Declaring detail pages

```python
# settings.py
WAGTAIL_DAISIE_DETAIL_PAGES = {
    "bread": {
        "label": "Bread",
        "model": "blog.Bread",
        "page_type": "blog.BreadDetailPage",
        "parent": "blog.BreadIndexPage",
        "template_page": "blog.BreadDetailTemplate",
        "generated_index": "blog.BreadGeneratedPagesIndexPage",
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
| `parent` | The listing page model that owns the generated index. |
| `template_page` | The single `ModelDetailTemplate` page whose body and design are rendered. |
| `generated_index` | The single `GeneratedPagesIndexPage` under `parent`. |
| `lookup_field` / `lookup_in` | How `{{ key }}` resolves on the page. |
| `publish_field` | Create/publish the page only when this model field is truthy. |
| `title_source` / `slug_source` | Model attributes used for the page title/slug. |
| `on_delete` | `"page"` (default), `"unlink"` or `"ignore"`. |

`template_page` and `generated_index` are required. There are no fallbacks to
an index page or to the first available page.

## Defining the page types

```python
from wagtail_daisIE.detail_pages.models import (
    GeneratedPagesIndexPage,
    GeneratedPagesRouteMixin,
    ModelDetailPage,
    ModelDetailTemplate,
)
from wagtail_daisIE.pages import StyledPageMixin


class BreadIndexPage(GeneratedPagesRouteMixin, StyledPageMixin):
    """Navigable listing: holds a Feed block and links to each record."""

    template = "blog/bread_index_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BreadGeneratedPagesIndexPage"]
    max_count = 1


class BreadDetailTemplate(ModelDetailTemplate):
    """Shared, non-navigable content and design for the generated pages."""

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1


class BreadGeneratedPagesIndexPage(GeneratedPagesIndexPage):
    """Admin-only container for generated bread pages."""

    parent_page_types = ["blog.BreadIndexPage"]
    subpage_types = ["blog.BreadDetailPage"]


class BreadDetailPage(ModelDetailPage):
    template = "blog/bread_detail_page.html"
    parent_page_types = ["blog.BreadGeneratedPagesIndexPage"]
    subpage_types = []
```

`GeneratedPagesRouteMixin` should be applied to the base page class that hosts
listings (for example `ReservedSlugPage`), so requests to `/breads/<slug>/`
route into the generated index without exposing its segment.

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
`{{ bread.url }}` links start working with no template changes. The
model-context help panel lists `{{ bread.url }}` as a help-only dynamic value;
it is not a database field.

## The shared template page

`ModelDetailTemplate` is a `StyledPageMixin` page, but it is a **content and
design container only**: give it a theme, background, **Page default design**,
body blocks and **Context bindings** (for example a `bread` binding with
`lookup_in: path`).

It is deliberately **not navigable**:

- `get_url_parts()` returns `None`, so it has no URL and nothing links to it.
- A direct request raises `404`.
- Its slug is hidden and auto-generated from the title.

Generated pages render the template page's `body` and inherit its theme,
background, page design, main design and bindings at request time. Editing the
template restyles and rewrites every generated page.

Generated pages have **no body, background, page design, main design or context
bindings of their own**. They also have no audience fields; the template page's
audience rules gate the generated pages, and the project's source-visibility
hook decides whether the record itself may be viewed.

## Lifecycle

* **Create** — a page is created under the generated index only when
  `publish_field` is empty or truthy. Non-public records create no page.
* **Update** — the same page is refreshed. If the record becomes non-public,
  its generated page is deleted.
* **Delete** — the page is deleted in `pre_delete` (via `Page.delete()`), so the
  Wagtail tree stays consistent even though `GenericRelation` cascades.
* **Repair** — a sync moves a stale generated page under its configured
  generated index.

## Configuration errors

Configuration is validated exactly:

- exactly one index page per entity
- exactly one shared template page per detail type
- exactly one generated index per detail type
- the template page must be live
- the generated index must sit under its listing

A missing or duplicate configuration raises `DetailPageConfigurationError`
during the Django system check, bootstrap/seed, render time and model signals.
Signal errors are logged and re-raised, so a missing template breaks the model
save rather than producing a silently empty page.

Deployments must seed the detail-page structure before any process creates
users, meetings, reviews or other detail-backed records. See the project's
bootstrap command.

## Admin

Generated pages are not creatable by hand (`is_creatable = False`). Page
listings gain an **Edit source record** button, and snippet listings gain a
**View detail page** button. Generated indexes are admin-only containers and
cannot be served publicly.
