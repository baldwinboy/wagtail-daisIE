# Block palettes

Container blocks accept different child sets. The sets live in
`src/wagtail_daisIE/blocks/palettes.py` and are resolved lazily by
`src/wagtail_daisIE/blocks/stream.py`.

## Finite layout tiers

The palettes are acyclic by construction. There is no editor depth setting and
no cyclic block-definition graph.

| Tier | Palette | Contents | Used by |
|---|---|---|---|
| 0 | `inline` | Inline elements only | Inline counterparts |
| 1 | `inline_layout` | Tier 0 + inline layout counterparts | Specialized containers and calendar event design |
| 2 | `layout` | Tier 0 + Tier 1 + specialized containers + data | Full common layouts |
| root | `ALL_CONTENT_BLOCKS` | Tier 0 + Tier 1 + Tier 2 + specialized containers + data | Page bodies, form pages, allauth bodies |

A full layout never contains another full layout. It contains inline
counterparts instead. Inline counterparts contain inline elements only.

## Full layouts and inline counterparts

| Full layout | Inline counterpart | Counterpart content |
|---|---|---|
| `row` | `row_inline` | `inline` |
| `column` | `column_inline` | `inline` |
| `grid` | `grid_inline` | `inline` |
| `card` | `inline_card` | `inline` |
| `list` | `list_inline` | `inline` |
| `stack` | `stack_inline` | `inline` |
| `aura` | `aura_inline` | `inline` |
| `indicator` | `indicator_inline` | `inline` |
| `drawer` | `drawer_inline` | `inline` for side and content |
| `hero` | `hero_inline` | `inline` |
| `tabs` | `tabs_inline` | `inline` for tab content |

Full layouts use `layout`. They also accept specialized containers and
`feed`, `calendar` and `reusable`.

## Specialized containers

- `accordion` — item content uses `inline_layout`
- `alert`, `toast`, `modal` — body uses `inline_layout`
- `carousel` — slide content uses `inline_layout`
- `mockup_browser`, `mockup_window`, `mockup_phone` — content uses
  `inline_layout`

Specialized containers are available in full layouts and the top-level palette,
but not in inline elements or inline counterparts. Their content cannot contain
data blocks or full layouts.

## Data blocks

`feed`, `calendar` and `reusable` are available in:

- the top-level page palette;
- full layout palettes.

They are not available in:

- inline palettes;
- inline counterparts;
- specialized containers;
- calendar event designs;
- menu-item streams.

`CalendarBlock.event` uses `inline_layout`.

## Inline elements

The `inline` palette contains the inline elements from the block inventory:
text, media, display, links, navigation, feedback, inputs, forms, table,
marquee, dropdown and similar leaf blocks.

`accordion` is not an inline element because its item content is Tier 0 + Tier 1;
it is a specialized container.

## Intentionally restricted blocks

These keep their own child format and are not layout containers:

- link list (links only)
- fieldset (form fields only)
- pagination (page items only)
- FAB (actions only)
- join (inputs/buttons only)
- filter (options only)
- breadcrumbs (crumb items only)
- table (table cells only)
- status, progress, loading, countdown, skeleton (leaf display blocks)

## Editor categories

Stream-block groups are sorted by a fixed order in `base_blocks/groups.py`:

```text
Layout, Text, Link, Cards, List, Navigation, Data, Data input,
Actions, Feedback, Mockups, Media, Display
```

Category assignments:

- `Table`, `Accordion` and `Reusable` are in **Layout**.
- `Newsletter` is in **Data**.
- `Icon` is in **Display**.

## Runtime data recursion

Static nesting is finite because it follows the tiers above. Data-driven
references can still form runtime cycles:

- a feed whose item design contains that same feed;
- a reusable block that references itself through a container.

`dynamic/recursion.py` tracks the chain of data blocks currently rendering. A
second occurrence of the same token in one chain is blocked, logged, and renders
empty; sibling blocks are unaffected. `FeedBlock`, `CalendarBlock` and
`ReusableBlockBlock` also reject a direct self-reference in `clean()` with an
editor validation message.

## Compatibility notes

- Existing block type keys are preserved.
- `inline_card` is the inline counterpart of `card`; its content is now
  inline-only.
- `accordion` is a specialized container; its item content is Tier 0 + Tier 1.
- `reusable` is no longer offered in menu-item streams.
- Alert, toast and modal keep their legacy rich-text `content` field and add an
  optional `body` stream.
- Content created with the previous recursive palettes may lose nested full
  layouts on load.
- See [migrations.md](migrations.md) for why nested palette changes do not
  create migrations, and [data-components.md](data-components.md) for feed and
  calendar item designs.
