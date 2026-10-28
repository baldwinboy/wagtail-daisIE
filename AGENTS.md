# AGENTS.md

Operating contract for AI coding agents working in this repository. Read this
file in full before planning or editing. It defines what you may run, what you
must hand over to the human or CI, and how to prove your work.

## 0. Non-negotiables

1. **Collaborate; do not work alone.** You are one member of a team. Propose,
   ask, implement, and hand back evidence.
2. **The human or CI owns the environment.** Long-running, mutating,
   credential-requiring, or heavyweight commands are handed over, never run and
   monitored by you.
3. **Read before you write.** Read the exact file, every caller, the relevant
   tests, and the migration history before editing. Never edit blind.
4. **One logical change per diff.** Atomic, reviewable, revertible. No drive-by
   refactors, reformatting, or import churn.
5. **No invented APIs, commands, paths, settings keys, or dependencies.** Verify
   in `justfile`, `pyproject.toml`, `uv.lock`, and the source. If you cannot
   verify it, stop and ask.
6. **No silent fallbacks.** No bare `except:`, no `except Exception: pass`, no
   `or {}` / `or []` masks, no `assert` for runtime validation.
7. **Every claim is tagged** `VERIFIED`, `REASONED`, or `UNVERIFIED`.
8. **Never edit `uv.lock` by hand, never touch secrets or vault files, never
   mutate production or shared data.**

## 1. Command ownership

### Safe for the agent to run

Fast, read-only, deterministic, local commands only:

```sh
rg ...                 # search
git status / diff / log / show
ls / find (read-only)
just --list
uv pip list
cat / sed / reading files
```

Single-file Ruff linting is also allowed:

```sh
uv run ruff check <path/to/file.py>
uv run ruff format --check <path/to/file.py>
```

Do not expand this into project-wide linting; `just lint` is a handover.

### Handover only — never run

Every `pytest` command and every Django `check` command is a handover, including
single-file runs:

```sh
uv run pytest tests/<any_file>.py
uv run ./demo/manage.py check
uv run ./demo/manage.py makemigrations --check --noinput
uv run ./demo/manage.py check_allauth_templates
```

Also hand over:

```sh
just install              # runs clean-db (deletes local SQLite DBs) + uv sync + npm ci
just demo                 # clean-db + migrate + seed + collectstatic + runserver
just runserver
just migrate              # makemigrations + migrate
just load_initial_data
just collectstatic
just build-css            # regenerates committed CSS
just lint                 # full linters
just format               # writes files
just test                 # full pytest suite
just coverage
just test-lowest-deps
just test-highest-deps
uv sync / uv lock / uv add / uv remove
npm ci / npm install
prek run --all-files
ansible-playbook (not present in this repo)
docker / docker compose (not present in this repo)
release, publish, deploy, tag, or push commands
```

`just install` and `just demo` are destructive: they delete local database
files. Treat them as shared-state mutations.

### Handover block

For every command the human must run, output exactly this and then pause. Do not
poll, retry, loop, or run it yourself.

```text
HANDOVER
Purpose:   <why this command needs to run>
Command:   <exact command, copy-pasteable>
Cwd:       <directory>
Env:       <required env vars / profiles, no secrets>
Expected:  <what success looks like>
Verify:    <how to confirm the result>
Blocked on: <what you will do once the human reports back>
```

Resume only after the human pastes the result.

## 2. Repository facts

- `wagtail-daisIE` is a **Django/Wagtail package**, not a deployable project.
  Source is `src/wagtail_daisIE/`; tests are `tests/`; a demo site lives in
  `demo/`.
- Import package name is `wagtail_daisIE` (capital `IE`). Do not rename it.
- Version `3.6.2`, managed by release-please. Do not hand-edit the version.
- Python `>=3.13` (dev on 3.14), Django `6.0.x`, Wagtail `8.0.x`, Node 24.
- Dependencies are managed by **uv**: `pyproject.toml` + `uv.lock`. Never add a
  dependency without explicit justification and human approval. `django-htmx`
  is a hard dependency.
- Task runner is **just**. Trust `justfile` over prose in docs. `justfile` is the
  source of truth for available recipes; `prek` runs pre-commit hooks.
- Python lint/format is **Ruff** (`ruff.toml`, line length 88, excludes `demo`
  and migrations). JS/CSS/JSON/Markdown-ish assets use **Prettier** and
  **Stylelint** via `npm run lint` / `npm run format`.
- There is **no mypy gate** in this repository. Do not claim one. Type hints are
  still expected on new code; if the human wants a mypy gate, that is a separate,
  approved change.
- There is no Docker, Compose, or Ansible infrastructure here. If a task
  references services, ports, volumes, inventories, or vault variables, stop and
  ask — do not assume.
- Tests run with `DJANGO_SETTINGS_MODULE=wagtail_daisIE.test.settings` and
  `--no-migrations` (see `[tool.pytest.ini_options]`).
- This project follows the
  [Wagtail package maintenance guidelines](https://wagtail.org/package-guidelines/)
  and was created from the
  [cookiecutter-wagtail-package](https://github.com/wagtail/cookiecutter-wagtail-package)
  template.

### Known documentation drift

- `just tailwind-cli` (historical) does not exist. Rebuild CSS with
  `just build-css`.
- `just compile-global-css` in `CONTRIBUTING.md` is historical; `just build-css`
  replaced it.
- `.github/workflows/test.yml` is authoritative for CI; it does not run
  `demo/manage.py test home`.

## 3. Definition of done

The human or CI must run, and paste back, all of the following before work is
declared complete:

```sh
just lint
just test
uv run ./demo/manage.py makemigrations --check --noinput
```

CI additionally runs:

```sh
just coverage
uv run ./demo/manage.py check
just test-lowest-deps
just test-highest-deps
```

Do not substitute "it looks correct" for these results. If they were not run,
the work is `UNVERIFIED`.

## 4. Project layout

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

```text
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
├── checks.py        # System checks (e.g. htmx middleware wiring)
├── context.py       # Theme contextvar used by FontFamilyChoiceBlock
├── pages.py         # StyledPageMixin
├── view_sets.py     # Wagtail admin "Design" snippet group
└── wagtail_hooks.py # Admin URLs, icons, JS/CSS, theme context hooks
tests/               # pytest suite (DJANGO_SETTINGS_MODULE=wagtail_daisIE.test.settings)
demo/                # Demo Wagtail site (settings, blog/home apps, fixtures)
```

## 5. Architecture: how CSS is produced

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

## 6. Invariants

### Data access and startup

- **Never query the database at import time or in `AppConfig.ready()`.**
  Widgets and form fields must not query in `__init__`; resolve lazily at
  request/render time (see `FontFamilyChoiceBlock` and
  `tests/test_widgets.py`). `makemigrations --check` runs on demo settings.

### Blocks and serialization

- **A `StructBlock` only registers child blocks** (`isinstance(value, Block)`),
  so a nested stream inside a struct uses the `StreamBlock` instance directly
  (e.g. `AbstractLinkBlock.destination = LinkDestinationBlock()`). Wrap a custom
  `StreamBlock` in `StreamField` only for model/top-level fields.
- **Destination blocks** store at least one destination where
  `LabelLinkBlock`/`InlineLinkBlock` require it (`min_num=1`); other users of
  `AbstractLinkBlock` leave it optional.
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
- **Model `StreamField`s are plain `wagtail.fields.StreamField`**; the block tree
  is frozen into the owning app's migration. Nested streams inside structs stay
  as plain `StreamBlock` instances. There is no `LazyStreamField`/`fields.py`.
- **Rudimentary inline markup** (`base_blocks/markup.py`) replaces plain
  single-line text: `**bold**`, `_italic_`, `__underline__`, `~~strike~~`,
  `[text](url)`. Parse with `render_inline_markup` (input already escaped by
  `{% daisie_markup %}`, which runs `render_placeholders` first); use the
  `daisie_strip_markup` filter for HTML attributes.

### Theming, menus, and layout

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
- **Menu container and item styles are independent**: `DaisyUIMenu.menu_design`
  styles the container (`menu_design_css`/`menu_design_style`); `item_design`
  styles items (`menu_default_css`/`menu_default_style`). Menus are wrapped in
  `.daisyui-menu`.
- **Menu item design cascade**: `menu.item_design` is a `MenuItemDesignBlock`
  stored in a one-item `StreamField`; `DaisyUIMenu.get_item_css()` returns its
  classes and the menu templates set `{% with block_css=menu_item_css %}`.
- **The `<main>` container is editor-designed**: `MainDesignBlock` on the theme
  (`DaisyUITheme.main_design`) and pages (`StyledPageMixin.main_design`); the page
  value wins over the theme, with no package fallback. Templates use
  `{% daisyui_main_attrs %}` (keep `id="main-content"`).
- **Breadcrumbs are a block** (`blocks/breadcrumbs.py`), available in pages,
  form pages and allauth bodies. It resolves the page trail from context, or
  renders an explicit `items` list (label/link/icon) when provided.
- **Feed layout choices live in `dynamic/feeds.py`** (`LAYOUT_CHOICES`,
  `ROW_MODE_CHOICES`, `GAP_CHOICES`, `TOGGLE_CHOICES`, `TOGGLE_PAIRS`) and are
  imported by `models.py` and `blocks_data.py`. They cannot live on the `Feed`
  model because `blocks_data` needs them and `models` imports `blocks_data`.
  Every key in `TOGGLE_PAIRS` must be a layout in `LAYOUT_CHOICES`; the
  `TestLayoutConstants` test guards this.

### Interaction, actions, and tabs

- **Actions are a struct block** (`dynamic/action_blocks.py`): an
  `ActionButtonBlock` (subclass of the normal button) plus an optional
  confirmation alert. The action view adds the confirmation to Django messages;
  `{% daisie_messages %}` renders them. `make_parent_clickable` is only honored
  inside a card and renders the control as a bare `absolute! inset-0!` overlay.
- **The Action form block** (`ActionFormBlock`, same module) collects
  data-input blocks and posts them to an action in one `<form>`. Its
  **After submit** `behaviour` (`inline` / `reload` / `navigate`) is submitted
  as `daisie_behaviour`; the action view returns an inline alert fragment
  (`action_form_status.html`), `HttpResponseClientRefresh`, or
  `HttpResponseClientRedirect`. It is nested only (tab content), so it never
  appears as a top-level block and produces no migration.
- **Tabs are CSS-only with per-block radio groups**: `TabItemBlock` has an
  optional `icon`, `key` (used by `?tab=`) and `audience`, and its `content`
  includes `LIST_CONTENT_BLOCKS`, the data-input blocks and the
  Action/Action-form blocks. `TabsBlock.get_context` resolves the per-tab list
  (audience, checked state, first-allowed fallback) and `tabs.html` renders
  DaisyUI `label.tab` controls containing a hidden radio, so an icon and label
  show while the panel switching stays pure CSS. Radio-group names use the
  inherited `block.id` (like inputs/drawer/modal), so accordions and tabs scope
  their controls per enclosing block rather than page-wide.
- **htmx is progressive enhancement** (`django-htmx` is a hard dependency):
  `WAGTAIL_DAISIE_HTMX` (default `True`) / `WAGTAIL_DAISIE_HTMX_VERSION`
  (default `2`) control `{% daisie_htmx %}`; `checks.py` warns (W001/W002) when
  the app/middleware are missing. Views branch on
  `getattr(request, "htmx", False)` so they work without the middleware. Feeds
  swap `feed_body.html` (`feed_items` returns the fragment, filtering/layout via
  `?layout=`/`limit`); the button-only Action block is not enhanced. Never rely
  on htmx: every form/link keeps a real `action`/`method`/`href`.

### Bridges and workflows

- **Error handlers are opt-in**: projects expose the relevant functions from
  `wagtail_daisIE.errors.handlers` in their root URLconf. Audience-denied
  `StyledPageMixin` pages render the 403 snippet directly.
- **Detail-page bridges** connect `post_save`/`pre_delete` receivers in
  `AppConfig.ready()` inside `try/except` (like notification bridges) and resolve
  models lazily; never query at import time. Deletion runs in `pre_delete` via
  `Page.delete()` because `GenericRelation` cascades outside Wagtail's tree
  bookkeeping.
- **Approval workflows** (`approval/`) are settings-driven
  (`WAGTAIL_DAISIE_APPROVAL_WORKFLOWS`): a `pre_save` receiver snapshots the
  approval field, a `post_save` receiver fires the project handler only on
  `False → True`, and the result is recorded in `converted_field` for
  idempotency. Bridges connect in core `AppConfig.ready()` inside `try/except`
  and resolve models/handlers lazily.

### Email

- **MJML backgrounds are per component**: only attributes a component supports
  are emitted (`background-color` / `container-background-color` /
  `inner-background-color`; images only on `mj-section`/`mj-wrapper`/`mj-hero`).
  Gradients are never emitted. Email design composites live in
  `notifications/email_blocks/design.py`.

### Allauth and assets

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

## 7. Django and Wagtail house rules

### Models

- Explicit `Meta` (`verbose_name`, `ordering`, indexes where queries demand
  them), `__str__` for anything shown in admin/choosers, and deliberate
  `on_delete` — never default to `CASCADE` without reasoning.
- Avoid mutable class attributes and module-level DB access.
- Prefer `TextChoices`/`IntegerChoices` or `ChoiceList` over raw string/int
  literals. Make illegal states unrepresentable with `null`/`blank`/defaults.
- Validate at the boundary (`clean()`, forms, blocks). Never trust request data.

### Migrations

- Treat migrations as part of the change. Generate them via handover; never
  hand-write migration files.
- Flag data migrations, irreversible operations, and changes to existing columns
  or `StreamField` schema explicitly, with a rollback note.
- Respect per-app labels and compact block serialization; see
  `docs/migrations.md`.
- Migrations must be deterministic and reversible, or explicitly flagged.

### ORM and queries

- Watch for N+1s; use `select_related`/`prefetch_related` on known access paths.
- Use `.exists()` instead of `.count()` when only presence matters.
- Cap unbounded querysets. Use `iterator()` for large scans and
  `bulk_create`/`bulk_update` for batch writes.
- Keep querysets explicitly ordered where output order matters.

### Wagtail

- Follow existing Page, block, panel, snippet, view-set, and hook patterns. Do
  not introduce a parallel convention.
- `StreamField` tree changes are schema-sensitive; update the owning app's
  migration and tests, and call the change out in the summary.
- Templates and `{% include %}` chains stay within existing app conventions; do
  not add a package-level `base.html`.

### Views and URLs

- Prefer class-based views where the repository already does; keep functions
  small and typed.
- Enforce permissions/audience checks at the view boundary. Handle anonymous
  users, missing page context, and CSRF explicitly.
- Never leak internal details in user-facing responses.

### Settings

- Environment-driven, `WAGTAIL_DAISIE_*` prefixed, no hardcoded secrets, no
  debug defaults in production settings. Fail fast on missing required values.
- Do not add a setting without documenting its default and wiring it into
  `checks.py` where misconfiguration is likely.

### Admin

- Register models where operationally useful, using the existing
  `view_sets.py` / "Design" snippet group. Guard destructive actions.

### Async

- Django ORM is sync. Do not call it from async contexts without
  `sync_to_async`. Prefer sync unless the repository already commits to async.

## 8. Correctness by construction

- **Type-first design.** Design models, forms, block fields, and signatures
  before writing bodies. Type hints on all new functions and methods.
- **Parse, don't validate.** Convert untrusted input to typed/cleaned values at
  the boundary, then trust them internally.
- **Read-before-write.** Check the exact installed version in `uv.lock` before
  using an API. Read migration history before changing a model.
- **Edge-case enumeration (mandatory before "done").** For each new or changed
  function, view, model method, block, or template, consider: empty querysets,
  `None`, boundary values, unicode/encoding, large inputs, malformed input,
  permission/audience gaps, CSRF, transaction boundaries, error paths, timeouts,
  concurrent writes, and retry/idempotency where state is mutated.
- **Errors carry context** and are logged structurally with Django `logging`.
  Catch specific exceptions only.

## 9. Performance and reproducibility

- Do not optimize speculatively. Mark hot paths `PERF-SENSITIVE` and propose a
  measurement (test, benchmark, `django-debug-toolbar`) instead of guessing.
  Never claim a speed improvement without a measurement the human ran.
- Use the configured cache backend if caching is genuinely needed; namespace
  keys explicitly and reason about invalidation.
- Set timeouts on outbound HTTP calls (e.g. icon providers); reuse clients.
- The committed CSS is a build artifact: do not regenerate it speculatively, and
  never run `collectstatic` or `build-css` without a handover.
- Seed and loaders must be deterministic and idempotent. No time/RNG/ordering
  nondeterminism in logic unless required and tested.
- Respect pinned versions; no dependency changes without approval.

## 10. Workflow

1. **Scope check.** Confirm the task is Phase A only. If it asks for more, stop
   and ask.
2. **Reconnaissance.** Read the relevant code, tests, migrations, `justfile`,
   `pyproject.toml`, `uv.lock`, and CI workflow.
3. **Plan.** State files to change, migrations needed, risks, test strategy, and
   required handovers. Ask clarifying questions before editing if anything is
   ambiguous, if multiple designs have material tradeoffs, or if the change
   affects public behaviour, data, security, permissions, or cost.
4. **Implement** in small, reviewable diffs. One logical change per edit.
5. **Hand over verification** as Handover Blocks. Do not run long or mutating
   commands yourself.
6. **Summarize**: what changed, why, evidence from pasted results, residual
   risks, follow-ups. Tag claims honestly.

Escalate after two failed attempts at the same fix. Never loop, never paper over
uncertainty.

## 11. Self-review and quality gates

Before declaring done, re-read the full diff as a hostile reviewer:

- Does each line satisfy the acceptance criteria?
- Is anything unused, unreachable, or dead?
- Would a reviewer ask "why this and not the simpler thing?"
- Are migrations consistent with the model changes?
- Is every assumption either verified or marked `UNVERIFIED`?

Quality gates:

- Acceptance criteria met.
- Requested tests, Ruff, `manage.py check`, and `makemigrations --check` passed
  per human-confirmed handover results.
- No debug code, secrets, dead code, `print`, or commented-out blocks.
- Errors are explicit; logging is structured.
- Queries on known access paths are free of N+1s.
- Diff is minimal and explainable line by line.
- Breaking changes, migration impact, and dependency changes are documented.

## 12. Demo content

`demo/blog/management/commands/load_initial_data.py` reads
`demo/fixtures/content.json` and media from `demo/fixtures/media/`, then seeds
themes, menus, error pages, email templates, notification audiences and feeds
programmatically. It is idempotent; use `--force` to recreate.
Block values passed to StreamFields must use the JSONish `{"type", "value"}`
form (with chooser values as primary keys) so nested blocks resolve. The loader
assigns values to live model fields (no migration state), so it is unaffected by
compact block serialization; `demo/home/tests.py::LoadInitialDataTests` covers
seeding and idempotency.

## 13. References

- `README.md` — user-facing usage.
- `docs/architecture.md` — architecture.
- `docs/migrations.md` — compact block migrations.
- `CONTRIBUTING.md` — contribution and release process.
- `ROADMAP.md` — scope guidance.
- `SECURITY.md` — vulnerability reporting.
- [Semantic Versioning](https://semver.org/) and
  [Keep a Changelog](https://keepachangelog.com/) for releases.
- [Conventional Commits](https://www.conventionalcommits.org/) — required for
  release-please classification.
- CSS follows the Wagtail Stylelint config.
