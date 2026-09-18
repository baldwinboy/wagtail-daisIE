# Design system

The design system turns editor choices into DaisyUI/Tailwind utility classes.
All primitives live in `wagtail_daisIE.base_blocks`.

## Design composites

| Composite | Fields | Used by |
|-----------|--------|---------|
| `DesignBlock` | size, background, border, padding, margin, box | `ThemedBlock` |
| `MediaDesignBlock` | as `DesignBlock`, with media size/aspect | images, embeds |
| `SpacedDesignBlock` | as `DesignBlock`, plus gap spacing | sections, rows |
| `TypographyDesignBlock` | typography, size, background, border, padding, margin, box | text blocks |
| `ButtonDesignBlock` | as `InlineSpacedDesignBlock`, plus button appearance | buttons |
| `MenuItemDesignBlock` | `TypographyDesignBlock` + spacing | `DaisyUIMenu.item_design` |
| `PageDesignBlock` | container, text, button and media defaults | `StyledPageMixin.page_design` |

`ThemedBlock` subclasses pair a composite with a `form_layout`. Concrete blocks
add their own content fields and a `template`.

## Producing class strings

`build_design_css(value)` walks the design groups present on the value and joins
each group's builder output. Each builder lives in `base_blocks/css.py` and
returns a space-separated string, e.g. `build_typography_css` returns
`text-primary-content font-heading text-xl`.

Font families store the theme role (or custom name) and render as
`font-<role>`, matching the `--font-<role>` custom properties emitted by
`{% daisyui_theme_font_css %}`.

## Inheritance (category channels)

Inheritance is per element category and strictly isolated. Each `ThemedBlock`
declares a `default_css_key` (`container`, `text`, `button` or `media`) and
reads/writes the matching `<category>_css` context channel:

```python
key = f"{self.default_css_key}_css"
channel = parent_context.get(key, "")
own = build_design_css(value.get("design"))
context["block_css"] = build_class(
    channel, parent_context.get("menu_default_css", ""), own
)
context[key] = build_class(channel, own)
```

- `block_css` is render-only; templates write it into `class`.
- A category's classes only ever reach descendants of the same category, so a
  container's styles cannot bleed into text, buttons or media.
- `MenuItemDesignBlock` is the exception: menu templates set the
  `menu_default_css` channel, which every category inherits, so
  `DaisyUIMenu.item_design` still applies to every menu item.

`StyledPageMixin.get_context` seeds the four channels from
`PageDesignBlock` (see [architecture.md](architecture.md#page-rendering)), so
page-wide defaults are applied per category without cross-category leakage.

`merge_block_css` remains available for the standalone design primitives
(`base_blocks/box.py`, `size.py`, `background.py`, `typography.py`); the
composite `ThemedBlock` pipeline no longer uses it.

## Adding a design primitive

1. Add the field(s) to a new `StructBlock` in `base_blocks/`.
2. Add a `build_*_css` function in `base_blocks/css.py` and register it in
   `_DESIGN_BUILDERS` under the group's key.
3. Add the group to the relevant composite in `base_blocks/design.py`.
4. Add a `get_context` that uses `merge_block_css(parent_context, ...)` if the
   primitive is also usable standalone.
