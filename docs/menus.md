# Menus

`DaisyUIMenu` is a snippet in the **Design** admin group. Menus reuse the same
block components as page bodies (`MENU_ITEM_BLOCKS` is a curated subset of the
public blocks), so links, buttons, cards and accordions behave identically in
both contexts.

## Model

| Field | Purpose |
|-------|---------|
| `name` | Unique; used by `{% daisyui_menu "Name" %}`. |
| `layout` | `navbar`, `footer`, `sidebar`, `horizontal`, `vertical`. |
| `branding` | One-item stream of `MenuBranding` (logo and/or wordmark, optional link). |
| `show_search`, `search_url`, `search_parameter`, `search_placeholder` | Optional search box. |
| `menu_theme` | Theme applied to the menu; falls back to the default theme. |
| `show_theme_toggle`, `theme_toggle_theme` | Optional light/dark toggle. |
| `item_design` | One-item stream of `MenuItemDesignBlock`: defaults for every item. |
| `sticky` | Sticky navbar. |
| `body` | `MenuItemStreamBlock` — the menu items. |

`get_theme()` returns `menu_theme` or the default theme. `get_item_css()` returns
the classes for `item_design`.

## Rendering

`{% daisyui_menu %}` looks the menu up by name and renders
`templates/wagtail_daisIE/blocks/menu_block.html`, which switches on `layout` and
includes the matching template. `menu_block.html` emits the menu theme CSS when
it differs from the page theme, then wraps the layout in
`{% with block_css=menu_item_css %}` so item defaults cascade.

## Branding

`MenuBranding` is a `StructBlock` with a `logo`, a plain `wordmark`
(`InlineTextBlock`), and a single optional `destination`. The template wraps both
in an `<a>` when a destination is set, making the logo and/or wordmark clickable.

## Destination rules

`LinkDestinationBlock` is a custom `StreamBlock` (one of page, URL, document,
email, phone) with `max_num=1`. It is required (`min_num=1`) on
`LabelLinkBlock` and `InlineLinkBlock`; optional on `ButtonBlock`,
`MenuBranding`, and other users of `AbstractLinkBlock`.

Because it is nested inside a `StructBlock`, it is declared as the `StreamBlock`
instance (`destination = LinkDestinationBlock()`), not via `StreamField`.
`StreamField` is only used for model/top-level fields.
