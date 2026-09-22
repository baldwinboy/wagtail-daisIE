# Data-driven components

Components let editors render project data and trigger actions without custom
templates: **Feeds** (filterable, AJAX-paginated lists), **Action buttons** and
**Calendars**. They use the context models declared in
`WAGTAIL_DAISIE_CONTEXT_MODELS` (see [context-models.md](context-models.md)) and
developer-defined actions.

Feeds, calendars and actions are content blocks, available in any page body.

## Action buttons

Actions are named callables declared in settings:

```python
WAGTAIL_DAISIE_ACTIONS = {
    "basket.add": {
        "label": "Add to basket",
        "handler": "myapp.actions.add_to_basket",
    },
}
```

A handler is called as `handler(request, data)` where `data` is the POST data.
Return an `HttpResponse` (for example a redirect or JSON), or `None` to redirect
back to the referring page.

```python
# myapp/actions.py
from django.shortcuts import redirect


def add_to_basket(request, data):
    pk = data.get("target")
    basket = request.session.setdefault("basket", [])
    if pk and int(pk) not in basket:
        basket.append(int(pk))
    return redirect(request.META.get("HTTP_REFERER", "/"))
```

The **Action button** block has **Action**, **Label**, **Button classes**, an
optional **Target expression** (resolved against the current item, e.g.
`bread.pk`) and **Confirmation text**.

Action buttons post with CSRF protection to the configured endpoint. Include the
Daisie URLs in your project:

```python
# urls.py
(path("daisie/", include("wagtail_daisIE.dynamic.urls")),)
```

## Feeds

A **Feed** is a reusable snippet (**Design → Feeds**) that renders instances of a
context model. Because it is server-side data, the endpoints needed for AJAX
filtering and infinite scroll can re-read the stored, admin-designed item
blocks.

Feed fields:

* **Model** — a key from `WAGTAIL_DAISIE_CONTEXT_MODELS`.
* **Order by**, **Items per page**, **Empty message**.
* **Infinite scroll** — load more on scroll; otherwise a **Load more** button.
* **Filters** — select and order the filters declared on the model (below).
* **Item design** — the blocks used for each item. This is the **same set as a
  page body** (sections, grids, cards, accordions, images, feedback, inputs,
  newsletter…) plus **Action buttons**, so items can use any Daisie block.

Inside the item blocks the instance is available under the model key, e.g.
`{{ bread.name }}`, `{{ bread.image }}` (with an image block in *From context*
mode), `{{ bread.url }}` and an action button with target `bread.pk`. Eager
loading (`select_related` / `prefetch_related`) and the model's `queryset` are
applied automatically.

A **Feed block** in a page or menu references a Feed snippet.

### Filtering

Filters are declared per context model (developers) and selected/ordered on the
Feed (admins):

```python
WAGTAIL_DAISIE_CONTEXT_MODELS = {
    "meeting": {
        "label": "Meeting",
        "model": "meetings.Meeting",
        "filters": {
            "language": {
                "label": "Language",
                "type": "choice",
                "field": "language",
                "choices": "myapp.filters.languages",  # (request, page) -> [{value,label}]
            },
            "topic": {
                "label": "Topic",
                "type": "choice",
                "multi": True,
                "field": "topics__slug",
                "choices": "myapp.filters.topics",
            },
            "starting": {
                "label": "Starts after",
                "type": "date_range",
                "field": "starts_at",
            },
            "price": {"label": "Price", "type": "number_range", "field": "price"},
            "available": {
                "label": "Available",
                "type": "boolean",
                "field": "is_available",
            },
            "text": {
                "label": "Search",
                "type": "search",
                "fields": ["title", "summary"],
            },
        },
    },
}
```

| Type | UI | Query |
|------|----|-------|
| `choice` (`multi: false`) | DaisyUI filter tabs (radio) | `field=value` |
| `choice` (`multi: true`) | checkbox buttons | `field__in=values` |
| `boolean` | Yes/No tabs | `field=True/False` |
| `date` | date input | `field__date=…` |
| `date_range` | two date inputs | `field__date__gte/__lte` |
| `number_range` | two number inputs (price) | `field__gte`/`__lte` |
| `search` | text input | `field__icontains` (OR over `fields`) |

`choices` may be a callable `(request, page) -> [{"value","label"}]`, a list of
`(value, label)` pairs, or a dotted path to such a callable. Invalid values are
ignored.

Each selected filter can be styled individually, and the controls offered
depend on the filter type:

* **Button filters** (choice, multi-choice, boolean) expose **Filter buttons**
  (`ButtonAppearanceBlock`) — colour, style, size, behaviour and modifier for the
  normal, hover and active states. The **selected** tab uses the configured
  active state (with DaisyUI’s `btn-active` as a fallback).
* **Input filters** (date, date range, price range, search) expose **Input
  design** (typography and input styling).
* All filters expose **Label design** (typography for the legend).

Date and date-range filters work with both `DateField` and `DateTimeField`
(datetimes are compared by date).

The Feed’s **Submit / Load more button** exposes the same button appearance,
styling the filter form’s Apply button and the Load more button.

### AJAX and infinite scroll

Filtering and pagination fetch items from
`wagtail_daisIE_dynamic:feed_items` and swap them in with JavaScript, so the page
does not reload and the URL query string is updated (shareable). Filters are a
real `GET` form and pagination a real link, so the feed still works without
JavaScript. With **Infinite scroll** enabled the next page loads as the visitor
scrolls (IntersectionObserver); otherwise a **Load more** button is shown.

### Example: a blog feed

The demo's blog index renders a feed bound to `blog_post` whose `queryset`
(`blog.feed.live_posts`) returns live posts scoped to the current index, with
`tag` (single) and `author` filters and a date-range filter. The item card uses a
dynamic image, title, introduction and a dynamic link.

### Example: a cart-style basket

A feed bound to a session-derived context model acts as a cart (`bread`/`basket`
in the demo); its items include an **Add to basket** / **Remove** action, with a
separate **Clear basket** action button on the page.

## Calendar

The **Calendar** block renders a [Cally](https://cally.dev) date picker and, for
the selected day, that day's events as admin-designed cards (the same block set
as feed items).

* **Model**, **Date field**, **Event card**, **Initial date**, **Maximum
  events**, **Empty message**.

All events are rendered server-side (one hidden panel per day) and the bundled
script toggles the correct panel when the date changes — no per-click request.
Cally is loaded from a URL you can override:

```python
WAGTAIL_DAISIE_CALLY_URL = "https://unpkg.com/cally"
```

## The demo

`just demo` seeds a **Bread** model, a blog feed and pages that demonstrate these
components:

* **Blog feed** — tag/author filters and a date range, AJAX-paginated.
* **Breads and basket** — a breads feed with **Add to basket**, a basket feed
  with **Remove**, and a **Clear basket** action.
* **Bread calendar** — breads grouped by `added_on`, with an add-to basket
  action per event card.

See `demo/blog/actions.py`, `demo/blog/filters.py`, `demo/blog/models.py` and
`demo/blog/management/commands/load_initial_data.py`.
