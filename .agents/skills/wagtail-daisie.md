---
name: wagtail-daisie
description: Work on the wagtail-daisIE Django/Wagtail package. Use when editing blocks, design primitives, error pages, menus, themes, icons, the demo site, or its tests and docs in this repository.
license: MIT
---

# wagtail-daisIE

Repo-local guide for the Wagtail DaisyUI Interface Editor package.

## When to use

Any task in `/Users/giraffe/daisie` touching `src/wagtail_daisIE/`, `tests/`, or
`demo/` — especially block/design changes, error-page handlers and templates,
menu/theme models, icons, the demo loader, or documentation.

## Read first

1. `AGENTS.md` — invariants and commands.
2. `docs/architecture.md` — layers and the `block_css` pipeline.
3. `docs/design-system.md` — design primitives and how to add one.
4. `docs/menus.md` — menu model, branding, item-design cascade.
5. `docs/error-pages.md` — error snippets, handlers, themes and fallbacks.

## Core rules

- **No DB queries at import time or in `AppConfig.ready()`.** Resolve lazily in
  `get_form_state`/`render_form`/`get_context` (see `FontFamilyChoiceBlock`).
- **Nesting a stream inside a `StructBlock`:** use the `StreamBlock` instance
  directly, e.g. `destination = LinkDestinationBlock()`. `StreamField` is a model
  field and is silently ignored as a struct child.
- **Always preserve `block_css` inheritance:** a block's `get_context` must
  merge inherited `block_css` (`merge_block_css(parent_context, own)`), otherwise
  menu `item_design` defaults stop cascading.
- **Render `{{ block_css }}`** in every themed block template inside a
  `{% if audience_allowed %}` guard.
- Font families store the theme **role/name** and render as `font-<role>`.
- **Error handlers are opt-in:** expose the relevant functions from
  `wagtail_daisIE.errors.handlers` in the project's root URLconf.

## Adding a block

1. Subclass the right `Themed*Block` in `base_blocks/design.py`.
2. Declare content fields; set `Meta.template`, `Meta.group`, and a
   `BlockGroup` `form_layout` (children + `settings=["design", "audience"]`).
3. Add the template under
   `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/` and render
   `{{ block_css }}`.
4. Register it in the relevant stream (`blocks/content.py`,
   `blocks/menu_items.py`, ...).
5. Add focused tests and run `just lint && just test`.

## Commands

```sh
just test        # pytest
just lint        # Ruff, pre-commit, Prettier, Stylelint
just demo        # migrate + load data + runserver
uv run ./demo/manage.py makemigrations --check --noinput
uv run ./demo/manage.py test home
npm run compile-global-css
```

## Demo data

`demo/blog/management/commands/load_initial_data.py` reads
`demo/fixtures/content.json` + media, then seeds themes, menus, error pages,
email templates, notification audiences and feeds. Keep it idempotent.
StreamField values use `{"type": "value"}` dicts with chooser IDs, not model
instances.
