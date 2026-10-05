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
just tailwind-cli  # Download the DaisyUI-enabled Tailwind CLI for JIT builds
```

Always run `just lint`, `just test` and
`uv run ./demo/manage.py makemigrations --check --noinput` before considering
work complete. CI additionally runs `uv run ./demo/manage.py check` and
`uv run ./demo/manage.py test home`.

## Project layout

The package is one distribution split into per-feature Django apps, each with
its own `migrations/` and explicit `label`:

| App | Label | Owns |
|---|---|---|
| `wagtail_daisIE` (core) | `wagtail_daisIE` | `DaisyUITheme` + orderables |
| `wagtail_daisIE.assets` | `wagtail_daisIE_assets` | `DaisyUIIconSource`, `DaisyUIFavicon` |
| `wagtail_daisIE.menus` | `wagtail_daisIE_menus` | `DaisyUIMenu` |
| `wagtail_daisIE.feeds` | `wagtail_daisIE_feeds` | `Feed` |
| `wagtail_daisIE.errors` | `wagtail_daisIE_errors` | `ErrorPage` |
| `wagtail_daisIE.notifications` | `wagtail_daisIE_notifications` | `EmailTemplate`, audiences, campaigns (opt-in) |
| `wagtail_daisIE.allauth_ui` | `wagtail_daisIE_allauth_ui` | `AllauthPageOverride` (opt-in) |
| `wagtail_daisIE.allauth_emails` | `wagtail_daisIE_allauth_emails` | `AllauthEmailOverride` (opt-in) |

Everything else is code-only (no models/migrations):

```
src/wagtail_daisIE/
├── base_blocks/     # Design primitives: size, box, background, typography, link, design, audience, markup, compact
├── blocks/          # Public block composition (content, cards, inline, link, menu_items, ...)
├── choices/         # DaisyUI/Tailwind class-choice constants (incl. MAIN_LAYOUT_CHOICES)
├── detail_pages/    # ModelDetailPage/ModelDetailTemplate + post_save/pre_delete bridges
├── approval/        # Approval workflow registry + pre_save/post_save bridges
├── dynamic/         # Context models, bindings, actions, calendar (code only; Feed lives in feeds/)
├── allauth_ui/      # Opt-in DaisyUI templates for allauth pages and forms
├── assets/          # Icon/favicon snippet models + admin view sets
├── menus/           # DaisyUIMenu snippet + view set
├── feeds/           # Feed snippet, data blocks, view set
├── errors/          # ErrorPage snippet, admin view set, Django handlers
├── favicon/         # Public manifest.json / browser-config.xml / favicon.ico views
├── icons/           # Icon providers, registry, chooser field/block/widget
├── forms/           # DaisieFormPage (form pages that create context-model instances)
├── models/          # DaisyUITheme + theme orderables and fields
├── notifications/   # Email templates, campaigns, audiences, bridges, email_blocks/, allauth overrides
├── templates/wagtail_daisIE/  # Block, tag, admin, preview templates
├── blockref.py      # Stable registry keys for compact block migrations
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
- **Error handlers are opt-in**: projects expose the relevant functions from
  `wagtail_daisIE.errors.handlers` in their root URLconf. Audience-denied
  `StyledPageMixin` pages render the 403 snippet directly.
- **Detail-page bridges** connect `post_save`/`pre_delete` receivers in
  `AppConfig.ready()` inside `try/except` (like notification bridges) and resolve
  models lazily; never query at import time. Deletion runs in `pre_delete` via
  `Page.delete()` because `GenericRelation` cascades outside Wagtail's tree
  bookkeeping.
- **The stylesheet is committed and prebuilt** (`static/wagtail_daisIE/css/daisie.css`):
  Tailwind + daisyUI + the `tailwind/safelist.css` generated by
  `manage.py daisie_safelist` from `choices/*` and the feed layout literals. It
  is served through staticfiles and linked with `{% daisyui_styles %}`; there is
  no runtime compile. Regenerate with `just build-css` after changing class
  choices. Arbitrary colour utilities (`bg-[#…]`, `decoration-[#…]`, with
  `hover:`/`active:`) are generated at request time by
  `wagtail_daisIE.middleware.ArbitraryCSSMiddleware`. Design backgrounds are
  `BackgroundStreamBlock` values rendered as an inline `block_style` (not
  classes); `TextBackgroundBlock` is email-only.
- **Choice lists are `choicelist.ChoiceList`**, a callable `list` that
  deconstructs to a short registry key (`get_choice_list("<KEY>")`) so the
  options are not frozen verbatim into migration `block_lookup` trees. Assign
  every new `*_CHOICES` constant to a module-level name via `ChoiceList(...)`
  (the constant name must be unique across the project); Django model fields
  cannot store an iterable callable, so give them a plain zero-arg function
  (e.g. `def layout_choices(): return LAYOUT_CHOICES`) and pass that instead.
  `tests/core/test_choice_lists.py` guards the package constants.
- **Blocks serialise by stable registry key** (`base_blocks/compact.py`,
  `blockref.py`): concrete blocks subclass `DaisieStructBlock`/`DaisieStreamBlock`
  and register under `<top_package>.<ClassName>`, so a migration stores
  `("wagtail_daisIE.blockref.RegisteredBlock", ["<key>"], {})` instead of an
  expanded block tree. New block classes must use these bases; freeze
  `Meta.migration_key` before renaming or moving one, and note that `FieldBlock`
  subclasses (e.g. `IconChooserBlock`) are not keyed. Migrations no longer record
  internal block-field changes (StreamField is a `JSONField`, so there is no
  DDL); `tests/core/test_compact_blocks.py` guards round-trip and key resolution.
  See `docs/migrations.md`.
- **MJML backgrounds are per component**: only attributes a component supports
  are emitted (`background-color` / `container-background-color` /
  `inner-background-color`; images only on `mj-section`/`mj-wrapper`/`mj-hero`).
  Gradients are never emitted. Email design composites live in
  `notifications/email_blocks/design.py`.
- **Menu container and item styles are independent**: `DaisyUIMenu.menu_design`
  styles the container (`menu_design_css`/`menu_design_style`); `item_design`
  styles items (`menu_default_css`/`menu_default_style`). Menus are wrapped in
  `.daisyui-menu`.
- **Breadcrumbs are a block** (`blocks/breadcrumbs.py`), available in pages,
  form pages and allauth bodies. It resolves the page trail from context, or
  renders an explicit `items` list (label/link/icon) when provided.
- **Actions are a struct block** (`dynamic/action_blocks.py`): an
  `ActionButtonBlock` (subclass of the normal button) plus an optional
  confirmation alert. The action view adds the confirmation to Django messages;
  `{% daisie_messages %}` renders them. `make_parent_clickable` is only honored
  inside a card and renders the control as a bare `absolute! inset-0!` overlay.
- **Feed layout choices live in `dynamic/feeds.py`** (`LAYOUT_CHOICES`,
  `ROW_MODE_CHOICES`, `GAP_CHOICES`, `TOGGLE_CHOICES`, `TOGGLE_PAIRS`) and are
  imported by `models.py` and `blocks_data.py`. They cannot live on the `Feed`
  model because `blocks_data` needs them and `models` imports `blocks_data`.
  Every key in `TOGGLE_PAIRS` must be a layout in `LAYOUT_CHOICES`; the
  `TestLayoutConstants` test guards this.
- **Model `StreamField`s are plain `wagtail.fields.StreamField`**; the block tree
  is frozen into the owning app's migration. Nested streams inside structs stay
  as plain `StreamBlock` instances. There is no `LazyStreamField`/`fields.py`.
- **Approval workflows** (`approval/`) are settings-driven
  (`WAGTAIL_DAISIE_APPROVAL_WORKFLOWS`): a `pre_save` receiver snapshots the
  approval field, a `post_save` receiver fires the project handler only on
  `False → True`, and the result is recorded in `converted_field` for
  idempotency. Bridges connect in core `AppConfig.ready()` inside `try/except`
  and resolve models/handlers lazily.
- **Rudimentary inline markup** (`base_blocks/markup.py`) replaces plain
  single-line text: `**bold**`, `_italic_`, `__underline__`, `~~strike~~`,
  `[text](url)`. Parse with `render_inline_markup` (input already escaped by
  `{% daisie_markup %}`, which runs `render_placeholders` first); use the
  `daisie_strip_markup` filter for HTML attributes.
- **The `<main>` container is editor-designed**: `MainDesignBlock` on the theme
  (`DaisyUITheme.main_design`) and pages (`StyledPageMixin.main_design`); the page
  value wins over the theme, with no package fallback. Templates use
  `{% daisyui_main_attrs %}` (keep `id="main-content"`).
- **Allauth account pages are admin-designed** via `AllauthPageOverride`
  snippets. The package overrides every `account/*.html` template that defines a
  content block; each override keeps allauth's markup verbatim as a fallback and
  delegates to `{% daisie_allauth_page %}` when a row is active. Only `account`
  is supported. After upgrading django-allauth run
  `manage.py check_allauth_templates`.
- **The package must never ship a `base.html`**: the allauth layout extends
  `WAGTAIL_DAISIE_ALLAUTH_BASE_TEMPLATE` (default a package chrome base) and the
  package template dir is prepended to `TEMPLATES.DIRS`.
- **Remote SVG is inlined after sanitising**: `IconifyProvider` in `cached-svg`
  mode serves third-party markup into the page, so `_sanitize_svg` must strip
  scripts, event handlers, external references and the elements that host them,
  and `_apply_attrs` escapes `size`/`color` into the `style` attribute.
- **`DaisyUIFavicon` resolves per site**: a row with `Site` set wins for that
  site; a row with `Site` empty is the global fallback. `{% daisyui_favicon %}`
  belongs in the `<head>` of every base template.

## Demo content

`demo/blog/management/commands/load_initial_data.py` reads
`demo/fixtures/content.json` and media from `demo/fixtures/media/`, then seeds
themes, menus, error pages, email templates, notification audiences and feeds
programmatically. It is idempotent; use `--force` to recreate.
Block values passed to StreamFields must use the JSONish `{"type", "value"}`
form (with chooser values as primary keys) so nested blocks resolve. The loader
assigns values to live model fields (no migration state), so it is unaffected by
compact block serialization; `demo/home/tests.py::LoadInitialDataTests` covers
seeding and idempotency.

## Guidelines

- Follow [Semantic Versioning](https://semver.org/) for releases.
- Use [Keep a Changelog](https://keepachangelog.com/) format for CHANGELOG.md.
- CSS follows the Wagtail stylelint config; run `just lint` before committing.
- Refer to [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/](docs/architecture.md).
