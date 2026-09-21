# Wagtail DaisyUI Interface Editor

<p>
  <a href="https://github.com/baldwinboy/wagtail-daisIE/actions/workflows/test.yml?branch=main">
    <img src="https://github.com/baldwinboy/wagtail-daisIE/actions/workflows/test.yml/badge.svg?branch=main" alt="CI — lint &amp; tests" />
  </a>
</p>

Create reusable [DaisyUI](https://daisyui.com/) themes through Wagtail, apply
them to pages, and build navigation menus from the same block components.

## Links

- [Documentation](https://github.com/baldwinboy/wagtail-daisIE/blob/main/README.md)
- [Developer docs](docs/architecture.md)
- [Emails](docs/emails.md) · [Context models](docs/context-models.md) ·
  [Forms](docs/forms.md) · [Data components](docs/data-components.md) ·
  [Notifications](docs/notifications.md) · [django-allauth](docs/allauth.md)
- [Changelog](https://github.com/baldwinboy/wagtail-daisIE/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/baldwinboy/wagtail-daisIE/blob/main/CONTRIBUTING.md)

## Supported versions

This package supports Wagtail 7.3 and up, and all [compatible versions of Python and Django](https://docs.wagtail.org/en/stable/releases/upgrading.html#compatible-django-python-versions).

## Installation

```bash
uv add wagtail-daisIE
poetry add wagtail-daisIE
pip install wagtail-daisIE
```

### 1. Add to `INSTALLED_APPS`

```python
# myproject/settings.py
INSTALLED_APPS = [
    "wagtail_daisIE",
    # ...
    "wagtail",
    # ...
    "wagtail.contrib.table_block",
    # ...
    "colorfield",
]
```

### 2. Run migrations

```bash
python manage.py migrate
```

### 3. Build the global stylesheet

The package ships a compiled Tailwind v4 + DaisyUI stylesheet. If you change
`source.css`, rebuild it:

```bash
npm run compile-global-css
```

## Quick start

### Create a theme

In the Wagtail admin, open **Design → Themes** and create a theme. Configure:

- **Name** — a unique identifier (used as the `data-theme` value).
- **Set as default** / **Set as default dark theme** — fallbacks.
- **Color scheme** — `light`, `dark`, or `normal`.
- **Colors** — primary, secondary, accent, neutral, base surfaces, semantic colors.
- **Border radii**, **Sizes**, **Effects** — DaisyUI design tokens.
- **Background** — solid, gradient, or image layers.
- **Fonts** — font families by role (`heading`, `body`, `subheading`, `code`, or
  custom) with fallbacks, base font size and line height.
- **Font CDNs** — stylesheet links for webfonts (e.g. Google Fonts).

### Use the page mixin

`StyledPageMixin` adds a theme, per-page background layers, and a content body
`StreamField` to any Wagtail page:

```python
from wagtail_daisIE.pages import StyledPageMixin


class MyPage(StyledPageMixin):
    content_panels = (
        StyledPageMixin.content_panels
        + [
            # Add any custom panels here
        ]
    )
```

This mixin adds:

- `page_theme` — a `ForeignKey(DaisyUITheme)` (defaults to the default theme).
- `page_background` — background layers that override the theme for this page.
- `body` — a `StreamField` of content blocks.
- `get_daisyui_theme()` — returns `page_theme` or the default theme.
- Context variables `daisyui_theme` and `daisyui_page_background_css`.

### Render the theme in your templates

```html
{% load wagtailcore_tags wagtail_daisIE_tags %}
<!DOCTYPE html>
<html{% if daisyui_theme %} data-theme="{{ daisyui_theme.name }}"{% endif %}>
    <head>
        <link rel="stylesheet" href="{% daisyui_global_css %}" />
        {% daisyui_theme_full_css daisyui_theme %}
        {% daisyui_icon_assets %}
    </head>
    <body{% if daisyui_page_background_css %} style="background: {{ daisyui_page_background_css }}"{% endif %}>
        {% block content %}{% endblock %}
    </body>
</html>
```

`{% daisyui_global_css %}` returns the URL of the bundled Tailwind/DaisyUI
stylesheet; remove conflicting stylesheets (Bootstrap, other Tailwind builds).

`{% daisyui_theme_full_css theme %}` emits the theme's color, radius, size,
effect, background, font, and font-CDN CSS. Finer-grained tags are listed below.

## Menus

`DaisyUIMenu` is a reusable snippet rendered with the `{% daisyui_menu %}` tag.
Menus reuse the same blocks as page bodies, so content components behave
identically in both contexts.

```django
{% load wagtail_daisIE_tags %}
{% daisyui_menu "Main navigation" %}
{% daisyui_menu "Footer" css_class="bg-base-200" %}
```

Each menu has:

- **Layout** — `navbar`, `footer`, `sidebar`, `horizontal`, or `vertical`.
- **Branding** — a logo and/or wordmark, optionally wrapped in one destination
  link (page, URL, document, email, or phone).
- **Search** — an optional search box with configurable URL, parameter, and
  placeholder.
- **Theme** — a `menu_theme` (falls back to the default theme) plus an optional
  light/dark toggle.
- **Item defaults** (`item_design`) — default typography, background, spacing,
  size, border and box styles applied to every item. Each item's own settings
  are appended on top, so per-block design still wins.
- **Menu items** — links, buttons, search boxes, inline cards, accordions, link
  lists, headers, text, and newsletters.

## Blocks and design

Design primitives live in `wagtail_daisIE.base_blocks` and are composed into the
public blocks in `wagtail_daisIE.blocks`. Every themed block resolves a
`block_css` class string from its design settings, merging any inherited
`block_css` from its parent context. This is what lets menu-level `item_design`
defaults cascade into items without any menu-specific block code.

Any block with a `typography` group (a `TypographyBlock`) exposes a **Font
family** picker populated from the current theme's font-family roles. The stored
value is the role (or custom name) and renders as `font-<role>`.

## Audience restrictions

Content blocks expose an `audience` field so editors can restrict content.
Audiences are declared in settings and evaluated at render time.

```python
# mysite/settings/base.py
WAGTAIL_DAISIE_AUDIENCE_RULES = {
    "adults": {"label": "Adults", "rule": "home.audience.is_adult"},
    "verified": {"label": "Verified users", "rule": "home.audience.is_verified"},
}
```

```python
# mysite/home/audience.py
def is_adult(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and getattr(user, "age", 0) >= 18)
```

Each rule is a dotted path to a callable invoked as `rule(request)` returning a
boolean. Selecting multiple audiences is a logical **OR**. If
`WAGTAIL_DAISIE_AUDIENCE_RULES` is empty, the audience field is hidden.

For campaigns (which have no request) a rule may also declare a `queryset`
returning a User queryset — see [docs/notifications.md](docs/notifications.md).

## Context models and dynamic content

Expose project models so authors can reference them from any block:

```python
WAGTAIL_DAISIE_CONTEXT_MODELS = {
    "user": {"label": "Current user", "model": "users.User", "source": "request.user"},
    "meeting": {
        "label": "Meeting",
        "model": "meetings.Meeting",
        "source": "url",
        "lookup_field": "slug",
        "url_source": "get_absolute_url",
    },
}
```

Then use `{{ user.first_name }}`, `{{ meeting.url }}` in text, rich text,
**Image** blocks (dynamic source) and **link** destinations. Pages can pin a
value to a specific instance or resolve it from the URL. Full guide:
[docs/context-models.md](docs/context-models.md).

## Data components

Render project data and trigger actions with reusable components:

- **Feeds** — a snippet (Design → Feeds) that lists a context model with
  admin-designed item cards, typed filters (choice/multi, boolean, date, date
  range, price range, search), AJAX filtering and optional infinite scroll.
- **Action button** — posts to a developer-defined action
  (`WAGTAIL_DAISIE_ACTIONS`), e.g. *Add to basket*.
- **Calendar** — a [Cally](https://cally.dev) date picker showing each day's
  events as designed cards.

```python
WAGTAIL_DAISIE_ACTIONS = {
    "basket.add": {
        "label": "Add to basket",
        "handler": "myapp.actions.add_to_basket",
    },
}
```

```python
# urls.py
(path("daisie/", include("wagtail_daisIE.dynamic.urls")),)
```

Full guide: [docs/data-components.md](docs/data-components.md).

## Emails and notifications

Build responsive MJML emails from the same design primitives and edit them in
Wagtail, with `{{ payload.* }}` placeholders and an admin help panel listing
what's available:

- Emails: [docs/emails.md](docs/emails.md)
- Bridges, audiences and scheduled campaigns:
  [docs/notifications.md](docs/notifications.md)
- django-allauth pages, forms and email overrides:
  [docs/allauth.md](docs/allauth.md)

```python
WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
    "booking_requested": {
        "label": "Booking requested",
        "template": "Booking requested",
        "signal": "myapp.signals.booking_requested",
        "sender": "myapp.models.MeetingRequest",
    },
}
```

## Form pages

`DaisieFormPage` renders DaisyUI forms and can create a configured model
instance from a submission, with an optional approval flag so new records start
unapproved. See [docs/forms.md](docs/forms.md).

## Icons

Icons are stored as `"<prefix>:<name>"` (e.g. `mdi:home`) or as raw CSS classes
(e.g. `fa-solid fa-home`). Four providers ship with the package:

| Provider | Prefix example | Notes |
|----------|----------------|-------|
| `wagtail` | `wagtail:home` | Built-in Wagtail admin icons, rendered inline. |
| `iconify` | `mdi:home` | On-demand icons from Iconify (cached server-side). |
| `font` | `fa6-solid:house` | Any webfont rendered via CSS classes. |
| `custom` | `brand:mark` | A project-supplied IconifyJSON or name-to-SVG manifest. |

Icon sources are managed under **Design → Icon Sources**. Render an icon with
`{% daisyui_icon value %}` and include provider assets with
`{% daisyui_icon_assets %}` (or the `icon_assets` context processor).

```python
from wagtail import hooks


@hooks.register("register_icon_providers")
def register_icon_providers(providers):
    return providers + [MyIconProvider()]
```

## Template tags

| Tag | Type | Output |
|-----|------|--------|
| `{% daisyui_global_css %}` | Simple | URL of the bundled Tailwind/DaisyUI stylesheet |
| `{% daisyui_theme_css theme %}` | Inclusion | Inline `<style>` with color/radius/size/effect variables |
| `{% daisyui_theme_inline_css theme %}` | Simple | Raw theme CSS string |
| `{% daisyui_theme_background_css theme %}` | Inclusion | Inline `<style>` for background layers |
| `{% daisyui_theme_background_inline_css theme %}` | Simple | Raw background CSS string |
| `{% daisyui_theme_font_css theme %}` | Inclusion | Inline `<style>` with `--font-*` variables |
| `{% daisyui_theme_font_cdns theme %}` | Inclusion | `<link>` tags for font CDNs |
| `{% daisyui_theme_full_css theme %}` | Inclusion | Font CDNs + colors + background + fonts |
| `{% daisyui_theme_full_inline_css theme %}` | Simple | Raw combined CSS string |
| `{% daisyui_menu "Name" %}` | Inclusion | Renders a `DaisyUIMenu` snippet |
| `{% daisyui_icon value %}` | Simple | Renders a stored icon value |
| `{% daisyui_icon_assets %}` | Inclusion | Provider scripts/styles for `<head>` |
| `{{ item\|is_active:request }}` | Filter | Whether a menu item points at the current path |

## Settings

No Django settings are required. The following are optional:

```python
# settings.py
WAGTAIL_DAISIE_ICONS = {
    "iconify": {
        "api": "https://api.iconify.design",  # or a self-hosted API
        "mode": "cached-svg",  # or "component"
        "collections": ["mdi", "fa6-solid", "lucide"],
        "timeout": 3,
    },
    "cache_timeout": 604800,
}

WAGTAIL_DAISIE_AUDIENCE_RULES = {
    "adults": {"label": "Adults", "rule": "home.audience.is_adult"},
}

WAGTAIL_DAISIE_CONTEXT_MODELS = {
    "user": {"label": "Current user", "model": "users.User", "source": "request.user"},
}

WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
    "booking_requested": {
        "label": "Booking requested",
        "template": "Booking requested",
        "signal": "myapp.signals.booking_requested",
        "sender": "myapp.models.MeetingRequest",
    },
}

# Requires the [allauth] extra.
WAGTAIL_DAISIE_ALLAUTH_UI = True

WAGTAIL_DAISIE_ACTIONS = {
    "basket.add": {"label": "Add to basket", "handler": "myapp.actions.add"},
}

# Optional: self-hosted Cally for the calendar block.
WAGTAIL_DAISIE_CALLY_URL = "https://unpkg.com/cally"
```

## Demo

The `demo/` project is a DaisyUI-styled Wagtail site. Run it with `just demo`
(migrate, load data, collect static, runserver) or load only the data with
`just load_initial_data`.

The loader reads `demo/fixtures/content.json` and
`demo/fixtures/media/original_images/`, then seeds themes and menus
programmatically. It is idempotent (use `--force` to recreate content). See
[`demo/fixtures/README.md`](demo/fixtures/README.md) for the fixture schema.

The demo also showcases the notification, context-model, form and allauth
features:

- **Context and components** page — context models plus feedback/data-input
  blocks.
- **Members only** page — audience-gated with a designed 403 error page.
- **Suggest a bread** — a `DaisieFormPage` that creates an unapproved
  `BreadSuggestion` for review.
- **Newsletter** in the footer — posts to the Daisie subscribe endpoint and
  populates the *Newsletter* audience.
- **Breads and basket** — a `Model list` of the `Bread` model with an
  *Add to basket* action button, a session basket list, and a *Clear basket*
  action (a cart parallel).
- **Bread calendar** — the breads grouped by `added_on` in a Cally calendar.
- **Blog feed** — the blog index renders a filterable feed (tag/author/date) of
  live posts with AJAX pagination.
- **Blog post published** — a notification bridge emailing that audience.
- **Account pages** at `/accounts/` — DaisyUI allauth pages and emails, with
  sample *Account confirmation* and *Password reset* email templates.
- Admin user `admin` / `changeme`.


## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/](docs/architecture.md).

```bash
just install     # Install Python and Node.js dependencies
just demo        # Run the demo site
just test        # Run tests
just lint        # Run all linters
```

## License

`wagtail-daisIE` is licensed under the BSD 3-Clause License.
