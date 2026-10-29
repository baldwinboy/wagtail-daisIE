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
| `MainDesignBlock` | as `SpacedDesignBlock`, plus `layout` (column/row/grid) | `DaisyUITheme.main_design`, `StyledPageMixin.main_design` |
| `MenuItemDesignBlock` | `TypographyDesignBlock` + spacing | `DaisyUIMenu.item_design` |
| `PageDesignBlock` | container, text, button and media defaults | `StyledPageMixin.page_design` |

`ThemedBlock` subclasses pair a composite with a `form_layout`. Concrete blocks
add their own content fields and a `template`. They inherit `DaisieStructBlock`,
so migrations store them as a stable registry key rather than a frozen tree (see
[migrations.md](migrations.md)).

## Producing class strings

`build_design_css(value)` walks the design groups present on the value and joins
each group's builder output. Each builder lives in `base_blocks/css.py` and
returns a space-separated string, e.g. `build_typography_css` returns
`text-primary-content font-heading text-xl`.

Font families store the theme role (or custom name) and render as
`font-<role>`, matching the `--font-<role>` custom properties emitted by
`{% daisyui_theme_font_css %}`.

Those roles are also applied as theme defaults: `body` sets the body font
(plus `--font-size-base` and `--line-height`), `heading` applies to `h1`/`h2`,
`subheading` to `h3`–`h6`, and `code` to `code`/`kbd`/`samp`/`pre`. The rules
use element-level specificity scoped with `:where()`, so an explicit
`font-<role>` utility always wins. Custom font names cannot reuse a built-in
role name or a Tailwind font weight/family utility name.

Rich text renders inside `.daisie-richtext`, which restores the element styles
Tailwind preflight removes: paragraph and heading spacing, heading sizes,
list markers and indentation, link underlines, blockquotes, rules, code blocks
and media sizing. Rich text drops inherited page-level `font-*` classes so
non-heading content defaults to the theme `body` font; an explicit block font
still applies to normal text, while `h1`/`h2` and `h3`–`h6` keep their role
fonts. Inline editor font spans always win.

`ListBlock` stores `list-disc` (Unordered) or `list-decimal` (Ordered) and
renders `<ul>` or `<ol>` accordingly. Legacy stored `list-none` values render
as unordered lists and normalise on the next edit.

Auto spacing and size values are stored prefixed (`ml-auto`, `w-auto`,
`size-auto`, `min-h-auto`). Legacy bare `auto` values are normalised at render
time in both web and email output. `max-width`/`max-height` have no auto
utility in Tailwind, so their choice lists omit Auto.

Block-level `Size` includes an optional `Overflow` choice
(`overflow-y-auto`, `overflow-x-auto`, `overflow-auto`). Vertical scrolling only
has an effect when a height or maximum height constrains the container. Rows
that use horizontal scrolling automatically drop their wrap setting and mark
their children as non-shrinking so the row scrolls instead of wrapping.

`ChoiceOptionsDesignBlock` uses the same `Size -> Overflow` field. Values saved
with the old top-level `choice_options.scroll` key are upgraded into
`choice_options.size.scroll` when the block is loaded; the legacy key is removed
on the next save.

Page-level container design also exposes `Overflow`. Because page-level
container classes are inherited by every block, setting overflow there applies
to all blocks that use the container channel. Use it deliberately.

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

## Site chrome (favicon and PWA)

The favicon is a site-level design decision rather than a page-level one, so it
is not part of the `block_css` pipeline. `DaisyUIFavicon` is a snippet holding
the icon files, the theme colour and the manifest options; it is edited in the
Wagtail admin under **Design → Favicons**.

`{% daisyui_favicon %}` renders the `<link rel="icon">` / `apple-touch-icon`
tags plus the web-app manifest `<link>` and the theme-colour `<meta>`. Add it
to the `<head>` of your base template (the demo site does this in all eight
head templates, including the package's own).

The snippet is resolved per site: a `DaisyUIFavicon` row with a `Site` set
wins for that site, and a row with `Site` left empty acts as the global
fallback. That lets a multi-site Wagtail install give each site its own icon
without duplicating templates. The generated `manifest.json`,
`browserconfig.xml` and `favicon.ico` are served from public URLs by
`favicon/urls.py`, so they can be referenced by absolute URL from the manifest
and from `browserconfig.xml`.

## CSS production (committed Tailwind + DaisyUI)

The base stylesheet is prebuilt and committed
(`static/wagtail_daisIE/css/daisie.css`) and linked with `{% daisyui_styles %}`.
It contains Tailwind, daisyUI and every class enumerated in `choices/*` (via the
generated `tailwind/safelist.css`). The opt-in responsive stylesheet
(`daisie-responsive.css`) adds breakpoint variants. Arbitrary colour utilities
are generated at request time by `ArbitraryCSSMiddleware`. See
[assets.md](assets.md).

Because the safelist is generated from `choices/*`, runtime-built class strings
(for example the button hover/active variants and the feed layout containers in
`dynamic/feeds.py`) are covered automatically.

### Responsive design

Design blocks accept a sparse list of `{breakpoint, utility}` entries. The
admin edits them with four controls — Design area → Property → Side → Value —
reusing the design panel's slider plus native selects for text alignment and
layout properties. Side is shown only for padding, margin and gap (Wagtail's
`w-rules`); the matching control is switched with `w-zone`.
Entries render as prefixed classes (`md:p-8 lg:text-2xl`) and are stored only
when an editor adds one. The breakpoint variants live in the opt-in
`daisie-responsive.css`, enabled with `WAGTAIL_DAISIE_RESPONSIVE_CSS = True`.
See [assets.md](assets.md).

### Backgrounds

`background` on every design composite is a `BackgroundStreamBlock` (solid,
image, gradient layers). `ThemedBlock.get_context` renders it as an inline
`block_style` (`background: …`) rather than utility classes. The email-only
`TextBackgroundBlock` accepts a single colour.

### The `<main>` container

`MainDesignBlock` (`base_blocks/design.py`) designs the page's main container.
It adds a `layout` choice (`column` → `flex flex-col grow`, `row` →
`flex flex-row grow`, `grid` → `grid grow`) built by `build_layout_css`, on top
of the `SpacedDesignBlock` groups.

Set it on the theme (`DaisyUITheme.main_design`) as the site default and/or on a
page (`StyledPageMixin.main_design`) to override it. The page value wins over
the theme; when neither is set there is no package fallback. Build templates
with `{% daisyui_main_attrs daisyui_theme %}` on
`<main id="main-content">`, which emits the `class` and `style` (background)
attributes. The theme preview wraps its body in the same container.

### Inline markup

Single-line, editor-authored text uses `InlineMarkupBlock`
(`base_blocks/markup.py`). The rudimentary syntax is parsed at render time by
`{% daisie_markup value.text %}` (pass `allow_links=False` for button/link
labels and email):

- `**bold**` → `<strong>`
- `_italic_` → `<em>`
- `__underline__` → `<u>`
- `~~strikethrough~~` → `<s>`
- `[text](url)` → `<a class="link" href="url">text</a>` (schemes limited to
  `http`, `https`, `mailto`, `tel`; invalid URLs drop the anchor)

Placeholders (`{{ … }}`) are substituted first (literals escaped), then the
markup is applied, so output is safe without further sanitising. For HTML
attributes (`aria-label`, `alt`, `placeholder`) use the `daisie_strip_markup`
filter. The syntax is not nested and does not support multi-line text.

### Typography decoration and states

`TypographyBlock` adds `text_decoration` (`underline`/`overline`/`line-through`/
`no-underline`), `decoration_color`, `decoration_thickness`, and `hover`/`active`
states (`TypographyStateBlock`) whose colour/decoration are emitted as
`hover:`/`active:` variants. Links (`link link-hover`) and the breadcrumbs block
inherit these.

### Breadcrumbs

`BreadcrumbsBlock` (`blocks/breadcrumbs.py`) resolves the current page's trail
from context, or renders an explicit `items` list (label/link/icon). It is
available in pages, form pages and allauth bodies.

### Theme variables

`{% daisyui_theme_full_css theme %}` emits the theme's `--color-*`,
`--radius-*`, `--size-*`, `--font-*` custom properties as inline CSS, plus a
`.font-<role>` rule and the theme-scoped body/heading/subheading/code defaults
for each font family. A page renders with its theme by overriding those
variables; the shared structural CSS comes from the committed `daisie.css`.

Base templates also render `{% daisyui_all_themes_css %}`, which emits those
variables for **every** configured theme. Without it, a `data-theme` (or the
theme toggle) naming another theme has no variables and daisyUI's built-in
`@media (prefers-color-scheme: dark) { :root:not([data-theme]) }` fallback can
show the wrong background. Pages always resolve a theme
(`page_theme → default → first`) so `data-theme` is never omitted.

## Adding a design primitive

1. Add the field(s) to a new `StructBlock` in `base_blocks/`.
2. Add a `build_*_css` function in `base_blocks/css.py` and register it in
   `_DESIGN_BUILDERS` under the group's key.
3. Add the group to the relevant composite in `base_blocks/design.py`.
4. Add a `get_context` that uses `merge_block_css(parent_context, ...)` if the
   primitive is also usable standalone.
