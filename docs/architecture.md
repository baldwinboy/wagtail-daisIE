# Architecture

This document maps the package for developers and AI agents.

## Layers

```
choices/        Plain constants: Tailwind/DaisyUI class choices
base_blocks/    Reusable design primitives and the block CSS pipeline
blocks/         Public block composition built on base_blocks
models/         Snippets: DaisyUITheme, DaisyUIMenu, DaisyUIIconSource, ErrorPage
icons/          Icon provider registry, chooser field/block/widget
emails/         MJML email templates (see docs/emails.md)
dynamic/        Context models, dynamic image/link values, resolution
notifications/  Email bridges, allauth emails, audiences and campaigns
forms/          DaisieFormPage and the DaisyUI form builder
errors/         Admin-designable error pages and Django handlers
allauth_ui/     Opt-in DaisyUI templates for allauth pages and forms
templates/      Block, tag, admin and preview templates
```

### `dynamic/`

`registry.py` parses `WAGTAIL_DAISIE_CONTEXT_MODELS`; `resolvers.py` resolves
request/URL/fixed values and dynamic expressions (including the URL scheme
allow-list); `mixins.py` injects the values into page and block contexts;
`blocks.py`/`forms.py` provide the per-page binding chooser; `feeds.py`
implements typed filters and feed rendering; `models.py` defines the `Feed`
snippet; `blocks_data.py` holds the Feed, Action button and Calendar blocks;
`actions.py` + `urls.py` + `views.py` run developer-defined actions and serve
feed slices.

### `notifications/`

`placeholders.py` renders `{{ ... }}` expressions (Django engine, autoescape,
tags left literal); `context.py` builds the built-in context; `rendering.py`
turns an `EmailTemplate` into subject/HTML/text; `bridges.py` dispatches events;
`registry.py`/`conf.py` read bridge settings; `allauth.py` +
`allauth_catalogue.py` bridge allauth; `campaigns.py` sends audiences;
`models.py` holds `AllauthEmailOverride`, `Audience`, `AudienceMember`,
`EmailCampaign` and `CampaignRecipientLog`.


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

## Errors

`errors/models.py` defines the status-specific `ErrorPage` snippet and
`errors/view_sets.py` registers **Errors → Error pages** in the Wagtail admin.
`errors/handlers.py` selects the active page, resolves its explicit or default
theme, and renders `templates/wagtail_daisIE/errors/error_page.html` with the
original HTTP status. Projects opt in from their root URL configuration, while
audience-gated pages can render the 403 snippet directly. See
[error-pages.md](error-pages.md).

## Icons

Provider-based registry; see [icons.md](icons.md).

## Invariants

See `AGENTS.md`. The most important are: no database queries at import time, and
nesting a `StreamBlock` inside a `StructBlock` by using the block instance
(never `StreamField`, which is a model field).

## Tests

`tests/` runs against `wagtail_daisIE.test.settings` (package only). Tests that
need the demo `home`/`blog` apps live in `demo/`.
