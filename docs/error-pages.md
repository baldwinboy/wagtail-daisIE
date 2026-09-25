# Error pages

`ErrorPage` is a Wagtail snippet for status-specific content. Editors manage
one page per supported HTTP status under **Errors → Error pages**; projects opt
in to Django's error handlers from their root URL configuration.

## Create an error page

1. Open **Errors → Error pages** in the Wagtail admin.
2. Add an error page and select its HTTP status.
3. Add an optional title and any `ContentBlock` instances for the body.
4. Choose a theme, or leave it empty to use the default theme.
5. Leave **Active** enabled, save the snippet, and wire the relevant handler as
   described below.

Create at most one snippet for each status. `status_code` is unique, and there
is no second configured page to fall back to when the first one is inactive.

## Fields

| Field | Purpose |
|-------|---------|
| `status_code` | Unique HTTP status: 400, 401, 403, 404, 429 or 500. |
| `title` | Optional page heading; the document title falls back to the status code. |
| `page_theme` | Optional `DaisyUITheme`; deleting it restores default-theme resolution. |
| `body` | Optional stream of the same `ContentBlock` types used by page bodies. |
| `is_active` | Only active snippets are selected for rendering. |

An active snippet with a blank body renders its title over the themed page
background. An inactive or missing snippet uses the bundled fallback described
in [Themes and fallbacks](#themes-and-fallbacks).

## Wire up Django handlers

The package does not replace a project's error handlers automatically. Import
the handlers that apply in the project's root `urls.py`:

```python
from wagtail_daisIE.errors.handlers import (
    handler400,
    handler403,
    handler404,
    handler500,
)
```

The module-level names tell Django to use the package's response. Projects can
select a subset; for example, the demo imports the dotted handler paths for
403, 404 and 500 from `demo/demo/urls.py`.

Django does not automatically dispatch 401 or 429 responses. Render those
statuses explicitly from the view that produces them:

```python
from wagtail_daisIE.errors.handlers import render_error_page


def rate_limited(request):
    return render_error_page(request, 429)
```

The same function is available for any custom status page. It preserves the
status passed to it and renders either the active `ErrorPage` or the bundled
fallback.

## Status behavior

| Status | Package entry point | How it is reached |
|--------|---------------------|-------------------|
| 400 | `handler400` | Django handles `BadRequest`. |
| 401 | `handler401` or `render_error_page()` | A custom view calls it explicitly. |
| 403 | `handler403` or `render_error_page()` | Django handles `PermissionDenied`, or page audience gating calls it directly. |
| 404 | `handler404` | Django handles `Http404`. |
| 429 | `handler429` or `render_error_page()` | A custom view calls it explicitly. |
| 500 | `handler500` | Django handles an unhandled server error. |

Returning an ordinary response such as `HttpResponse(status=429)` does not run
Django's exception handlers. The view must call `render_error_page()` when it
wants designed content for that status.

When `DEBUG=True`, Django can show its technical 404 or 500 page instead of
calling the configured handler. Test those paths with `DEBUG=False`. A 403
rendered directly by page audience gating does not depend on Django's 404/500
debug-page behavior.

## Themes and fallbacks

Theme selection follows this order:

1. The error page's `page_theme`.
2. The first `DaisyUITheme` marked as the default.
3. No theme, if neither a selected nor default theme is available.

The standalone error template loads the bundled global stylesheet and the
resolved theme's full CSS. It does not extend the project's base template, so
it has no normal site header, footer, menus or page background. It also does not
load icon-provider assets or inject page context-model bindings. See
[Context models and dynamic values](context-models.md) for the supported page
and menu binding paths.

If there is no active `ErrorPage` for the status, or its database lookup cannot
complete, rendering falls back to this response:

* the same HTTP status;
* an `Error {status}` heading;
* the text `Something went wrong.`

The configured status is never converted into a successful 200 response.

## Audience-gated pages

Pages using `StyledPageMixin` can choose how audience denial is handled under
**Audience access**:

* **Show a 403 page** calls `render_error_page(request, 403)` directly and
  returns the active 403 snippet. This path also works while `DEBUG=True`.
* **Show a 404 page** raises `Http404`, allowing the configured 404 handler to
  decide how it is rendered.
* **Redirect to a page** redirects to the selected page. If the setting is
  `redirect` without a target, the implementation falls back to the 403 page.

Audience-gated blocks inside an error body keep their normal block audience
settings. They are evaluated against the request that received the error, so a
block may be visible on a general 404 while hidden when the same 403 page is
returned to a denied user. See
[Audience gating](context-models.md#audience-gating) for rule behavior.

## Testing caveats

`just demo` runs with `DEBUG=True`. Its audience-gated **Members only** page
demonstrates the directly rendered 403, but a missing URL or unhandled server
error will show Django's debug response rather than the seeded 404 or 500.
Exercise the latter paths with a non-debug, production-like settings module.

The demo loader creates active 403, 404 and 500 snippets. It does not create
400, 401 or 429 snippets, so configure those in the admin before testing them.

The package tests call `render_error_page()`, `handler404` and `handler500`
directly. They verify status preservation and the inactive-page fallback, but
do not cover complete root-URLconf dispatch, body-block rendering, theme
resolution or the 400, 401 and 403 handlers. Integration tests should cover:

* the root URLconf invoking each configured handler;
* both the response status and expected body content;
* explicit-theme and default-theme selection;
* inactive and missing snippets;
* direct audience-denied 403 rendering;
* custom 401 or 429 rendering from a view.

`ErrorPage` does not provide a separate admin preview, so verify final content
through a real handler path or an audience-gated page.
