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

The stylesheet is prebuilt and committed (`static/wagtail_daisIE/css/daisie.css`)
and linked with `{% daisyui_styles %}`. It contains Tailwind, daisyUI and every
class enumerated in `choices/*` (via the generated `tailwind/safelist.css`).
Arbitrary colour utilities are generated at request time by
`ArbitraryCSSMiddleware`. See [assets.md](assets.md).

Because the safelist is generated from `choices/*`, runtime-built class strings
(for example the button hover/active variants and the feed layout containers in
`dynamic/feeds.py`) are covered automatically.

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
`.font-<role>` rule for each font family. A page renders with its theme by
overriding those variables; the shared structural CSS comes from the committed
`daisie.css`.

## Adding a design primitive

1. Add the field(s) to a new `StructBlock` in `base_blocks/`.
2. Add a `build_*_css` function in `base_blocks/css.py` and register it in
   `_DESIGN_BUILDERS` under the group's key.
3. Add the group to the relevant composite in `base_blocks/design.py`.
4. Add a `get_context` that uses `merge_block_css(parent_context, ...)` if the
   primitive is also usable standalone.
