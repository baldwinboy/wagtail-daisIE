# Context models and dynamic values

Context models let authors reference project data from any block — text, rich
text, images and links — without a developer templating each page.

## Declaring context models

```python
# settings.py
WAGTAIL_DAISIE_CONTEXT_MODELS = {
    "user": {
        "label": "Current user",
        "model": "users.User",
        "source": "request.user",
        "select_related": ["profile"],
    },
    "meeting": {
        "label": "Meeting",
        "model": "meetings.Meeting",
        "source": "url",
        "lookup_field": "slug",
        "url_source": "get_absolute_url",
    },
}
```

Each entry supports:

| Key | Description |
|-----|-------------|
| `label` | Name shown in the admin. |
| `model` | `"app_label.ModelName"` or a dotted import path. |
| `source` | `"request.<attr>"`, `"url"`, `"page"`, or a dotted callable `(request, page) -> instance`. |
| `lookup_field` | URL keyword used with the `url` source (default `pk`). |
| `url_source` | How `{{ key.url }}` is derived: a field name, `"get_absolute_url"`, or a dotted callable. |
| `select_related` / `prefetch_related` | Eager loading for url-sourced lookups. |
| `queryset` | Optional dotted callable (or callable) `(request, page) -> QuerySet` used by data blocks to scope/filter rows (e.g. live posts for the blog feed). |
| `filters` | Optional typed filters for feeds (choice/boolean/date/date range/number range/search) — see [data-components.md](data-components.md#filtering). |
| `fields` | Optional allow-list used by the help panel. |

The configured values are resolved at render time and injected into the page
context. Blocks render with their own context, so `wagtail_daisIE` copies the
values into nested blocks automatically.

## Using values in content

Anywhere a block renders text you can use `{{ key.field }}`:

```html
<p>Welcome back, {{ user.first_name|default:"friend" }}!</p>
<p>{{ meeting.title }} starts at {{ meeting.scheduled_at|date:"H:i" }}.</p>
```

Only `{{ ... }}` variable expressions with Django filters are supported;
template tags are shown literally.

### Date and time formatting

Use Django's `date`/`time` filters:

```html
{{ now|date:"j F Y" }}
{{ meeting.scheduled_at|date:"D d M Y H:i" }}
```

See the [date filter reference](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date).

## Images

The **Image** block has an **Image source** setting:

* **Static image** — choose a Wagtail image as usual.
* **From context** — enter an expression such as `{{ user.profile.image }}` or
  `{{ meeting.cover_url }}`.

Dynamic expressions resolve to:

1. a Wagtail `Image` (rendered as a responsive rendition), or
2. an object with a `.url`, or
3. a URL string.

The `alt` text falls back to the object's `alt`/`title`.

## Links

A link destination can be dynamic. Use the **Dynamic URL** option and enter an
expression such as `{{ meeting.url }}`. The value may resolve to a page,
document, object with `.url`/`get_absolute_url()`, or a plain URL string.
For safety only `http`, `https`, `mailto` and `tel` schemes are allowed
(relative URLs are fine); anything else renders an empty `href`.

## Bindings

Each configured model has a **source** that determines how its value is found:

* **Automatic** — `request.*`, `page`, or a project callable. No binding is
  needed; the value is always available (`{{ user.username }}`,
  `{{ site.hostname }}`).
* **From the URL** — the model is looked up from a URL keyword
  (`lookup_field`). A binding chooses the keyword (or uses the model default).
* **Specific instance** — a binding pins the value to one instance, chosen
  inline by searching the model's records.

Add bindings in one of two places:

* **Page** — the **Context bindings** panel on any page using `StyledPageMixin`.
* **Menu** — the **Context bindings** panel on a `DaisyUIMenu`, so items can use
  `{{ user.username }}` and friends.

`ErrorPage` bodies do not have a binding panel, and error rendering does not
inject configured context-model values. See
[Themes and fallbacks](error-pages.md#themes-and-fallbacks) for the standalone
error-page context.

Each binding row names the value and shows an inline, model-aware help panel
with the source in use, ready-to-paste examples (`{{ meeting.title }}`) and the
model's fields. Only the fields relevant to the chosen source are shown —
automatic values have no source, URL values show the URL keyword, and pinned
values show the instance picker.

The instance picker is a searchable chooser: type to filter, use **Show all**
to browse (up to 500 results), and use the arrow keys and Enter to select. It is
a labelled combobox and works with the keyboard alone.

### Blog feed example

The demo's blog index uses a **Model list** bound to the `blog_post` context
model, with its `queryset` set to `blog.feed.live_posts` so only live posts
under that index appear. See [data-components.md](data-components.md).

### Fallbacks

A binding can define a **Fallback** string used when the value cannot be
resolved — for example when nobody is signed in or a pinned record was deleted.
With a `user` binding whose fallback is `Guest`, `{{ user }}` renders `Guest`
instead of empty. (A missing or anonymous user triggers the fallback.)

Resolution never raises; values that cannot be resolved simply render empty
unless a fallback is set. You can also use Django's own filter for individual
fields, e.g. `{{ user.first_name|default:"there" }}`.

## Audience gating

Audience rules (`WAGTAIL_DAISIE_AUDIENCE_RULES`) work for both content blocks
and whole pages:

* Blocks: the **Audience** setting in the block's settings panel.
* Pages: the page-level **Audience** field, plus **When access is denied**
  (show a 403, show a 404, or redirect to a chosen page). See
  [Audience-gated pages](error-pages.md#audience-gated-pages).

When empty, content is visible to everyone. Multiple selected audiences are a
logical OR.

```python
WAGTAIL_DAISIE_AUDIENCE_RULES = {
    "members": {"label": "Members", "rule": "myapp.audience.is_member"},
}
```

Rules are callables `(request) -> bool`. For campaigns, a rule may also declare
a `queryset` — see [notifications.md](notifications.md#audiences).
