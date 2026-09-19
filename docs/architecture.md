# Architecture

This document maps the package for developers and AI agents.

## Layers

```
choices/        Plain constants: Tailwind/DaisyUI class choices
base_blocks/    Reusable design primitives and the block CSS pipeline
blocks/         Public block composition built on base_blocks
models/         Snippets: DaisyUITheme, DaisyUIMenu, DaisyUIIconSource
icons/          Icon provider registry, chooser field/block/widget
emails/         MJML email templates (see docs/emails.md)
templates/      Block, tag, admin and preview templates
```

### `choices/`

Pure data: `DAISYUI_BG_COLOR_CHOICES`, `FONT_SIZE_CHOICES`, `PADDING_CHOICES`,
etc. No Django imports beyond `gettext`.

### `base_blocks/`

Design primitives that can be composed into any block:

- `size.py` — width/height/size and media aspect.
- `box.py` — padding, margin, border, rounded corners, shadow, spacing.
- `background.py` — background colour/image mode.
- `typography.py` — `TypographyBlock` (colour, font family, size, weight,
  alignment, line height, letter spacing).
- `background_layer.py` — gradient/solid/image layers for page backgrounds.
- `audience.py` — `AudienceBlock` plus `evaluate_audience`.
- `link.py` — `LinkDestinationBlock`, `AbstractLinkBlock`, `link_url`.
- `design.py` — the design composites (`DesignBlock`, `TypographyDesignBlock`,
  `MenuItemDesignBlock`, ...) and the `Themed*Block` bases that produce
  `block_css` and `audience_allowed`.
- `css.py` — pure functions that turn design values into class strings, plus
  `merge_block_css`.
- `mjml.py` — email counterpart of `css.py`: turns design values into literal
  CSS declarations for MJML output (see [emails.md](emails.md)).
- `fields.py` — `ColorChoiceBlock`, `FontFamilyChoiceBlock`.
- `widgets.py`, `utils.py` — helpers.

### `blocks/`

Composes `base_blocks` into editor-facing blocks: `content.py` (`ContentBlock`),
`cards.py`, `inline.py`, `link.py`, `layout.py`, `marquee.py`, `media.py`,
`spaced.py`, `accordion.py`, `blockquote.py`, `menu_items.py`.

## The `block_css` pipeline

1. A block's `Meta` declares a `design` field made of primitives.
2. `ThemedBlock.get_context` calls `build_design_css(value["design"])` to get a
   space-separated class string, then merges it with any `block_css` inherited
   from `parent_context`.
3. The block template receives `block_css` and renders it into `class`.

Menu defaults use this: `DaisyUIMenu.get_item_css()` returns the classes for
`item_design`, and the menu templates wrap their item loop in
`{% with block_css=menu_item_css %}`. Each item then appends its own classes.
Because both are plain utility classes, per-item classes come last and win
where stylesheet order allows.

## Page rendering

`StyledPageMixin` adds `page_theme`, `page_background`, `page_design`, and
`body`. Its `get_context` injects `daisyui_theme`, `daisyui_page_background_css`
and the per-category default channels (`container_css`, `text_css`,
`button_css`, `media_css`) built from `PageDesignBlock`. Each `ThemedBlock`
inherits only its own category channel, keeping defaults isolated. Page
templates render `{% daisyui_theme_full_css daisyui_theme %}` in `<head>` and
apply `daisyui_page_background_css` to the body; body blocks must be rendered
with `{% include_block %}` (as `home_page.html` does) so they receive the page
context.

## Menus

`DaisyUIMenu` is a `ClusterableModel` snippet with revisions and preview. It
stores `branding`, `item_design`, and `body`, and is rendered by the
`daisyui_menu` inclusion tag. See [menus.md](menus.md).

## Icons

Provider-based registry; see [icons.md](icons.md).

## Invariants

See `AGENTS.md`. The most important are: no database queries at import time, and
nesting a `StreamBlock` inside a `StructBlock` by using the block instance
(never `StreamField`, which is a model field).

## Tests

`tests/` runs against `wagtail_daisIE.test.settings` (package only). Tests that
need the demo `home`/`blog` apps live in `demo/`.
