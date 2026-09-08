# Agents

Important context for AI coding agents working on this project.

## Project overview

Wagtail DaisyUI Interface Editor is a Django/Wagtail package. The source code is
in `src/wagtail_daisIE/`, with tests in `tests/` and a demo Wagtail site in
`demo/`.

This project was created from the
[cookiecutter-wagtail-package](https://github.com/wagtail/cookiecutter-wagtail-package)
template and follows the
[Wagtail package maintenance guidelines](https://wagtail.org/package-guidelines/).

## Key commands

```sh
just help        # View all commands
just install     # Install Python and Node.js dependencies
just demo        # Run the demo Wagtail site (migrate + load data + runserver)
just test        # Run tests with pytest
just lint        # Run all linters (Ruff, pre-commit, Prettier, Stylelint)
just format      # Run all formatters (Ruff, Prettier)
just coverage    # Run tests with coverage report
npm run compile-global-css   # Rebuild the bundled Tailwind/DaisyUI stylesheet
```

Always run `just lint`, `just test` and
`uv run ./demo/manage.py makemigrations --check --noinput` before considering
work complete. CI additionally runs `uv run ./demo/manage.py check` and
`uv run ./demo/manage.py test home`.

## Project layout

```
src/wagtail_daisIE/
├── base_blocks/     # Design primitives: size, box, background, typography, link, design, audience
├── blocks/          # Public block composition (content, cards, inline, link, menu_items, ...)
├── choices/         # DaisyUI/Tailwind class-choice constants
├── icons/           # Icon providers, registry, chooser field/block/widget
├── models/          # DaisyUITheme (+ orderables), DaisyUIMenu, DaisyUIIconSource
├── templates/wagtail_daisIE/  # Block, tag, admin, preview templates
├── context.py       # Theme contextvar used by FontFamilyChoiceBlock
├── pages.py         # StyledPageMixin
├── view_sets.py     # Wagtail admin "Design" snippet group
└── wagtail_hooks.py # Admin URLs, icons, JS/CSS, theme context hooks
tests/               # pytest suite (DJANGO_SETTINGS_MODULE=wagtail_daisIE.test.settings)
demo/                # Demo Wagtail site (settings, blog/home apps, fixtures)
```

## Architecture: how CSS is produced

- `base_blocks/css.py` builds space-separated DaisyUI/Tailwind utility class
  strings from design block values (`build_design_css`, `build_typography_css`,
  ...).
- Every themed block's `get_context` sets `context["block_css"]` by merging any
  inherited `block_css` from `parent_context` with its own classes
  (`merge_block_css`). This is deliberate: a menu injects its `item_design`
  defaults through the parent context, and each item appends its own design.
- `ThemedBlock.get_context` also evaluates `audience_allowed`.
- Templates render `block_css` into the element's `class`.

When adding a block, subclass the appropriate `Themed*Block` from
`base_blocks/design.py`, declare fields, set a `template`, a `form_layout`
(children + settings), and render `{{ block_css }}`.

## Invariants

- **Never query the database at import time or in `AppConfig.ready()`.**
  Widgets and form fields must not query in `__init__`; resolve lazily at
  request/render time (see `FontFamilyChoiceBlock` and
  `tests/test_widgets.py`). `makemigrations --check` runs on demo settings.
- **A `StructBlock` only registers child blocks** (`isinstance(value, Block)`),
  so a nested stream inside a struct uses the `StreamBlock` instance directly
  (e.g. `AbstractLinkBlock.destination = LinkDestinationBlock()`). Wrap a custom
  `StreamBlock` in `StreamField` only for model/top-level fields.
- **Destination blocks** store at least one destination where
  `LabelLinkBlock`/`InlineLinkBlock` require it (`min_num=1`); other users of
  `AbstractLinkBlock` leave it optional.
- **Menu item design cascade**: `menu.item_design` is a `MenuItemDesignBlock`
  stored in a one-item `StreamField`; `DaisyUIMenu.get_item_css()` returns its
  classes and the menu templates set `{% with block_css=menu_item_css %}`.

## Demo content

`demo/blog/management/commands/load_initial_data.py` reads
`demo/fixtures/content.json` and media from `demo/fixtures/media/`, then seeds
themes and menus programmatically. It is idempotent; use `--force` to recreate.
Block values passed to StreamFields must use the JSONish `{"type", "value"}`
form (with chooser values as primary keys) so nested blocks resolve.

## Guidelines

- Follow [Semantic Versioning](https://semver.org/) for releases.
- Use [Keep a Changelog](https://keepachangelog.com/) format for CHANGELOG.md.
- CSS follows the Wagtail stylelint config; run `just lint` before committing.
- Refer to [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/](docs/architecture.md).
