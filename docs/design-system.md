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

## Inheritance (`merge_block_css`)

```python
def merge_block_css(parent_context, own):
    inherited = (parent_context or {}).get("block_css", "")
    return build_class(inherited, own)
```

Any block that sets `block_css` prepends the inherited value. This lets a menu
apply `item_design` to every descendant while each block still contributes its
own settings. Pages simply have no inherited `block_css`.

## Adding a design primitive

1. Add the field(s) to a new `StructBlock` in `base_blocks/`.
2. Add a `build_*_css` function in `base_blocks/css.py` and register it in
   `_DESIGN_BUILDERS` under the group's key.
3. Add the group to the relevant composite in `base_blocks/design.py`.
4. Add a `get_context` that uses `merge_block_css(parent_context, ...)` if the
   primitive is also usable standalone.
