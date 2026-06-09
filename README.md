# Wagtail DaisyUI Interface Editor

Create reusable [DaisyUI](https://daisyui.com/) themes through Wagtail and apply them to pages.

## Links

- [Documentation](https://github.com/baldwinboy/wagtail-daisIE/blob/main/README.md)
- [Changelog](https://github.com/baldwinboy/wagtail-daisIE/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/baldwinboy/wagtail-daisIE/blob/main/CONTRIBUTING.md)
- [Discussions](https://github.com/baldwinboy/wagtail-daisIE/discussions)
- [Security](https://github.com/baldwinboy/wagtail-daisIE/security)

## Supported versions

This package supports Wagtail 7.0 and up, and all [compatible versions of Python and Django](https://docs.wagtail.org/en/stable/releases/upgrading.html#compatible-django-python-versions).

## Installation

Pick the command for your preferred package installer:

```bash
uv add wagtail-daisIE
poetry add wagtail-daisIE
pip install wagtail-daisIE
```

## Quick start

### 1. Add to `INSTALLED_APPS`

```python
# myproject/settings.py
INSTALLED_APPS = [
    ...
    "wagtail_daisIE",
    "colorfield",
    ...
]
```

### 2. Run migrations

```bash
python manage.py migrate
```

### 3. Create a theme

In the Wagtail admin, navigate to Snippets > DaisyUI Themes and create a new theme. Configure:

- **Name**: A unique identifier (e.g. `my-theme`)
- **Set as default**: Check this to make it the fallback theme
- **Color scheme**: `light`, `dark`, or `normal`
- **Colors**: Primary, secondary, accent, neutral, base surfaces, semantic colors
- **Border radii**: Box, field, selector
- **Sizes**: Field, selector, border width
- **Effects**: Depth (3D) and noise toggle

### 4. Use the page mixin

Add `DaisyUIThemePageMixin` to any Wagtail Page model:

```python
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail_daisIE.models import DaisyUIThemePageMixin


class MyPage(DaisyUIThemePageMixin, Page):
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("daisyui_theme"),  # Add the theme selector
    ]
```

This mixin adds:

- A `daisyui_theme` ForeignKey field to `DaisyUITheme`
- Automatic injection of `daisyui_theme` into the page template context
- A `get_daisyui_theme()` method that returns the selected theme (or the default theme if none is selected)

### 5. Render the theme in your templates

Load the template tags and render the theme CSS in `<head>`:

```html
{% load wagtailcore_tags wagtail_daisIE_tags %}
<!DOCTYPE html>
<html{% if daisyui_theme %} data-theme="{{ daisyui_theme.name }}"{% endif %}>
    <head>
        ...
        {% daisyui_theme_css daisyui_theme %}
    </head>
    <body>
        {% block content %}{% endblock %}
    </body>
</html>
```

The `{% daisyui_theme_css %}` tag outputs an inline `<style>` block with all DaisyUI CSS custom properties for the theme.

Alternatively, use `{% daisyui_theme_inline_css %}` to get the raw CSS string for custom placement:

```html
<style>
{% daisyui_theme_inline_css daisyui_theme %}
</style>
```

### 6. Load DaisyUI and Tailwind CSS

Add DaisyUI and Tailwind CSS to your base template. For a quick setup, use the CDN:

```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
```

Or use [Django Tailwind CLI](https://django-tailwind-cli.readthedocs.io/latest/):

```python
# settings.py
STATICFILES_DIRS = [BASE_DIR / "assets"]
# Custom CSS paths
TAILWIND_CLI_SRC_CSS = "src/styles/main.css"
TAILWIND_CLI_DIST_CSS = "css/app.css"

# Enable DaisyUI
TAILWIND_CLI_USE_DAISY_UI = True

# Use an already-installed Tailwind binary (e.g. `brew install tailwindcss`)
TAILWIND_CLI_USE_SYSTEM_BINARY = True

# Auto-inject @source directives for editable-installed external apps (opt-in)
TAILWIND_CLI_AUTO_SOURCE_EXTERNAL_APPS = True
```

Or install via npm and build with your own pipeline:

```bash
npm install daisyui @tailwindcss/cli tailwindcss
```

## API reference

### `DaisyUIThemePageMixin`

An abstract Django model mixin for Wagtail Pages.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `daisyui_theme` | `ForeignKey(DaisyUITheme)` | The selected theme, or `None` |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_daisyui_theme()` | `DaisyUITheme \| None` | Returns the selected theme, or the default theme if none was selected |

**Context:**

| Variable | Type | Description |
|----------|------|-------------|
| `daisyui_theme` | `DaisyUITheme \| None` | Available in all page templates |

### Template tags

| Tag | Type | Output |
|-----|------|--------|
| `{% daisyui_theme_css theme %}` | Inclusion tag | Inline `<style>` block with DaisyUI CSS custom properties |
| `{% daisyui_theme_inline_css theme %}` | Simple tag | Raw CSS string for custom placement |

### `DaisyUITheme`

A snippet model representing a DaisyUI theme. Accessible via Snippets in the Wagtail admin.

**Properties:** name, default, prefers_dark, color_scheme, colors, radii, sizes, effects.

## Settings

No Django settings are required. The package works out of the box once added to `INSTALLED_APPS`.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution workflow.

Key commands (via `just`):

```bash
just install     # Install Python and Node.js dependencies
just demo        # Run the demo site
just test        # Run tests
just lint        # Run all linters
```

## License

`wagtail-daisIE` is licensed under the BSD 3-Clause License.
