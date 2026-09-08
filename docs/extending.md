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

## Test settings

Package tests use `src/wagtail_daisIE/test/settings.py`. Tests that need the
demo `home`/`blog` apps belong in `demo/` (CI runs `demo test home`).
