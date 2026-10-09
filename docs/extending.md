# Extending

## Add a public block

```python
# src/wagtail_daisIE/blocks/my_block.py
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedBlock


class MyBlock(ThemedBlock):
    heading = blocks.CharBlock()

    class Meta:
        icon = "placeholder"
        group = _("My block")
        collapsed = True
        template = "wagtail_daisIE/blocks/my_block.html"
        form_layout = blocks.BlockGroup(
            children=["heading"],
            settings=["design", "audience"],
        )
```

Register it in a stream, for example `blocks/content.py`:

```python
from .my_block import MyBlock

ALL_CONTENT_BLOCKS = [..., ("my_block", MyBlock())]
```

> **Block bases and migrations.** `ThemedBlock` (and the other `Themed*`/`Design*`
> bases) already inherit `DaisieStructBlock`, so `MyBlock` is serialised in
> migrations by a stable registry key. A block that subclasses Wagtail's
> `blocks.StructBlock`/`blocks.StreamBlock` directly must instead subclass
> `wagtail_daisIE.base_blocks.DaisieStructBlock`/`DaisieStreamBlock` to get the
> same treatment. If you rename a registered block later, set
> `class Meta: migration_key = "<old key>"` first so existing migrations keep
> resolving. See [migrations.md](migrations.md).

Template:

```html
{% if audience_allowed %}
  <div class="{{ block_css }}">
    <h2>{{ value.heading }}</h2>
  </div>
{% endif %}
```

## Add an icon provider

Subclass `wagtail_daisIE.icons.providers.base.IconProvider` and register it:

```python
from wagtail import hooks


@hooks.register("register_icon_providers")
def register_icon_providers(providers):
    return providers + [MyProvider()]
```

Or create a `DaisyUIIconSource` snippet under **Design → Icon Sources**.

## Customise theme fonts

Add `DaisyUIThemeFontFamily` rows (one per role) to a theme's `DaisyUIThemeFonts`
and optional `DaisyUIThemeFontCDN` stylesheet links. The stored font role then
appears in every `TypographyBlock` picker and renders as `font-<role>`.

## Register a form field type

Add extra form field types (file/image uploads, or any Django form field) to
form pages via `WAGTAIL_DAISIE_FORM_FIELD_TYPES`; see
[File and image uploads](forms.md#file-and-image-uploads). Upload types require
a `handler` (per type or via `WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER`) that decides
where the file is stored and returns a JSON-safe reference:

```python
def store(*, page, form, field, file, request=None):
    return default_storage.url(default_storage.save(f"uploads/{file.name}", file))
```

`field` may be a class or a `(form_field, options) -> Field` factory, so a
project can ship its own multiple-file field.

## Bridge app-owned forms into an Action form block

A project can own a form's markup, validation and uploads while still letting
admins place a block by overriding the **Action form** template (project
template dirs take precedence over the package):

```django
{# myproject/templates/wagtail_daisIE/blocks/data/action_form.html #}
{% if value.action|slice:":9" == "settings." %}
  <div hx-get="{% url 'settings:section' key=value.action %}" hx-trigger="load" hx-swap="innerHTML">
    <a href="{% url 'settings:section' key=value.action %}">Open</a>
  </div>
{% else %}
  {# fall back to the plugin's default markup for other actions #}
  {% include "myproject/action_form_default.html" %}
{% endif %}
```

Name the project actions with a reserved prefix (for example `settings.*`) so
the override can distinguish them. The app view then renders and validates a
real Django form, returning a fragment for htmx and a normal redirect with
`{% daisie_messages %}` without it. This is how a single page can host several
independent, app-owned mini-forms inside a **Tab** block — see
[htmx.md](htmx.md) and [forms.md](forms.md#form-pages-vs-the-action-form-block).

## Test settings

Package tests use `src/wagtail_daisIE/test/settings.py`. Tests that need the
demo `home`/`blog` apps belong in `demo/` (CI runs `demo test home`).
