# Menus

`DaisyUIMenu` is a snippet in the **Design** admin group. Menus reuse the same
block components as page bodies (`MENU_ITEM_BLOCKS` is a curated subset of the
public blocks), so links, buttons, cards and accordions behave identically in
both contexts.

Provided by the required `wagtail_daisIE.menus` app.

## Model

| Field | Purpose |
|-------|---------|
| `name` | Unique; used by `{% daisyui_menu "Name" %}`. |
| `layout` | `navbar`, `megamenu`, `footer`, `sidebar`, `horizontal`, `vertical`, `dock`. |
| `branding` | One-item stream of `MenuBranding` (logo and/or wordmark, optional link). |
| `show_search`, `search_url`, `search_parameter`, `search_placeholder` | Optional search box. |
| `menu_theme` | Theme applied to the menu; falls back to the default theme. |
| `show_theme_toggle`, `alt_menu_theme` | Optional light/dark toggle. |
| `menu_design` | One-item stream of `SpacedDesignBlock`: the **container** design. |
| `item_design` | One-item stream of `MenuItemDesignBlock`: defaults for every **item**. |
| `sticky` | Sticky navbar. |
| `body` | `MenuItemStreamBlock` — the menu items. |

`get_theme()` returns `menu_theme` or the default theme. `get_menu_design_css()`/
`get_menu_design_style()` describe the container; `get_item_css()`/
`get_item_style()` describe the item defaults. Container and item styles are
**fully independent**.

## Rendering

`{% daisyui_menu %}` looks the menu up by name and renders
`templates/wagtail_daisIE/blocks/menu_block.html`, which switches on `layout` and
includes the matching template. `menu_block.html` emits the menu theme CSS when
it differs from the page theme, then wraps the layout with
`menu_default_css`/`menu_default_style` (from `item_design`) for the items.
Container templates render `menu_design_css`/`menu_design_style` and are wrapped
in `.daisyui-menu` for isolated styling.

Layouts: `navbar` (dropdown on mobile + **megamenu** on desktop), standalone
`megamenu` (`<button popovertarget>` + `<div popover>` pairs, responsive
vertical on small screens), `footer`, `sidebar`, `horizontal`, `vertical` and
`dock` (bottom bar).

## Branding

`MenuBranding` is a `StructBlock` with a `logo`, a plain `wordmark`
(`InlineTextBlock`), and a single optional `destination`. `MenuLogo` subclasses
the image block (same fields/design) and renders inline; size it with the media
design `size` (e.g. a height class). The wrapper is `inline-flex items-center`
so the logo sits on the same line as the wordmark.

## Destination rules

`LinkDestinationBlock` is a custom `StreamBlock` (one of page, URL, document,
email, phone) with `max_num=1`. It is required (`min_num=1`) on
`LabelLinkBlock` and `InlineLinkBlock`; optional on `ButtonBlock`,
`MenuBranding`, and other users of `AbstractLinkBlock`.

Because it is nested inside a `StructBlock`, it is declared as the `StreamBlock`
instance (`destination = LinkDestinationBlock()`), not via `StreamField`.
`StreamField` is only used for model/top-level fields.
