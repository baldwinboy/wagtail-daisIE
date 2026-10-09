# htmx

`wagtail-daisIE` progressively enhances its data components (feeds, action
forms and newsletter signup) with [htmx](https://htmx.org/) through the
[`django-htmx`](https://django-htmx.readthedocs.io/) integration. Every form and
link still has a plain `action`/`method`/`href`, so nothing breaks when
JavaScript is unavailable or the integration is disabled.

## Setup

`django-htmx` is a package dependency. Add the app and its middleware, then
enable the integration (it is on by default):

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_htmx",
    # ...
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
    # ...
]

WAGTAIL_DAISIE_HTMX = True  # default
WAGTAIL_DAISIE_HTMX_VERSION = 2  # default; 4 is also supported
```

Add the script to your base template's `<head>`:

```django
{% load wagtail_daisIE_tags %}
{% daisie_htmx %}
```

`{% daisie_htmx %}` renders the vendored htmx `<script>` (deferred). It returns
an empty string when `WAGTAIL_DAISIE_HTMX = False` or when `django_htmx` is not
installed, so templates stay portable. `WAGTAIL_DAISIE_HTMX_VERSION = 4` renders
the htmx 4 bundle from `django-htmx` instead.

Two system checks warn when the integration is enabled but not wired up:

| Check | Meaning |
|-------|---------|
| `wagtail_daisIE.W001` | `django_htmx` is not in `INSTALLED_APPS`. |
| `wagtail_daisIE.W002` | `django_htmx.middleware.HtmxMiddleware` is not in `MIDDLEWARE`. |

Disable the integration entirely with `WAGTAIL_DAISIE_HTMX = False`; the views
fall back to the non-htmx branch and no `<script>` is rendered.

## What is enhanced

### Feeds

The feed filter form posts with `hx-get` to
`wagtail_daisIE_dynamic:feed_items`, which returns a **body fragment**
(`wagtail_daisIE/blocks/data/feed_body.html`) that is swapped in place, so
filtering and pagination do not reload the page.

* **Filters** fire on `change` (and, for the search input, after a short typing
  delay).
* **Layout toggle** re-requests with `?layout=<value>` and re-renders the body;
  the chosen layout is reflected server-side (no `localStorage`).
* **Load more** requests the next slice with `?limit=<n>` and swaps the body;
  with **Infinite scroll** the same request fires when the button becomes
  visible.

Without htmx the filter form is a normal `GET` submission and **Load more** is a
real link: the page reloads and the server renders the same state.

### Action forms

The **Action form** block (`ActionFormBlock`) renders one `<form>` containing
the authored fields and the submit button. It posts with `hx-post` and supports
three behaviours, chosen per block (**After submit**):

| Behaviour | Result |
|-----------|--------|
| **Update in place** (default) | The confirmation is returned as an alert fragment and swapped into the block's `role="status"` area; the page does not navigate. |
| **Reload the page** | htmx refreshes the page (`HX-Refresh`). |
| **Follow the response** | A handler redirect becomes a client redirect (`HX-Redirect`); otherwise the page refreshes. |

The action endpoint (`dynamic/views.py`) decides between these using the
submitted `daisie_behaviour` value. A handler that returns a redirect is honoured
for the non-inline behaviours; in **Update in place** the redirect is ignored so
"saved on change" forms stay put.

Without htmx the form is a normal `POST`: the view adds the confirmation to
Django messages and redirects back, and `{% daisie_messages %}` renders it.

The button-only **Action** block is not htmx-enhanced; it posts normally and
relies on `{% daisie_messages %}`.

### Newsletter signup

The newsletter form posts with `hx-post` to the subscribe endpoint, which
returns a small DaisyUI alert fragment for the inline status area. Without htmx
it redirects back with `?subscribed=1` and the configured success message.

## Writing compatible views

The views branch on `django-htmx`'s `request.htmx` (guarded with `getattr`, so
the package works if the middleware is absent):

```python
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh


def my_view(request):
    if getattr(request, "htmx", False):
        return HttpResponseClientRefresh()
    return redirect("...")
```

`django_htmx.http` helpers used by the package: `HttpResponseClientRedirect`,
`HttpResponseClientRefresh`.

## CSP notes

The standard `hx-get`/`hx-post`/`hx-target`/`hx-swap` attributes used by the
package need no `unsafe-eval`. Avoid `hx-on:*` attributes (they compile with
`new Function`) under a strict CSP, and set `htmx.config.allowScriptTags = false`
if swapped fragments must never execute inline scripts.
