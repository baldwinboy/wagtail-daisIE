# Roadmap

This roadmap represents the current vision for this project, and is subject to
change. We welcome feedback and we're open to suggestions!

---

# Refactor: persistence fix, modularisation, rudimentary markup, `<main>` design

## Context

All tests currently pass, but three user-facing issues remain, and a major
refactor is underway:

1. **Home body content disappears on edit.** Root cause confirmed:
   `LazyStreamField.deconstruct()` strips `block_lookup`, so Wagtail 8's
   `StreamField.deconstruct()` (`wagtail/fields.py:194`) cannot round-trip the
   block tree. `Page.save_revision()` therefore serialises the page revision's
   `body` as `[]` (verified in `demo/db.sqlite3`: live revision 13 has a
   3124-char body, latest revision 34 has `body: "[]"`). The editor loads the
   latest revision, so the body appears empty and a save wipes it.
2. **Hero height.** The seeded hero has no height and collapses.
3. **Gradient shape choices** do not render because
   `BackgroundLayerBlock.gradient_shape` has no `choices`.

`LazyStreamField` must be removed (plain `StreamField` persists correctly). To
manage the resulting migration size, the package is split into per-feature
Django apps, each owning its own migrations — mirroring how Wagtail ships
`wagtailcore`, `wagtail.admin`, `wagtail.images`, etc.

Alongside the split, two features land:

- **Rudimentary inline markup** (bold, italic, underline, strikethrough, link)
  replacing plain inline text everywhere visible text is authored.
- **Admin-controlled `<main>` design** on the theme and page, replacing the
  hardcoded main-container classnames.

The email/MJML feature is folded into the `notifications` app (there is no
separate `emails` app). `notifications`, `allauth_ui` and `allauth_emails` are
opt-in.

---

## Target architecture

One distribution, multiple Django apps. Each app has an `apps.py` with an
explicit `label`, a `migrations/` package, and
`default_auto_field = "django.db.models.BigAutoField"`.

| App | Label | Models owned | State |
|---|---|---|---|
| core (`wagtail_daisIE`) | `wagtail_daisIE` | `DaisyUITheme` + colors/radii/sizes/effects/background/fonts orderables; `DaisyUIColorField`, `DaisyUISizeField` | required |
| `wagtail_daisIE.assets` | `wagtail_daisIE_assets` | `DaisyUIIconSource`, `DaisyUIFavicon` | required |
| `wagtail_daisIE.menus` | `wagtail_daisIE_menus` | `DaisyUIMenu` | required |
| `wagtail_daisIE.feeds` | `wagtail_daisIE_feeds` | `Feed` | required |
| `wagtail_daisIE.errors` | `wagtail_daisIE_errors` | `ErrorPage` | required |
| `wagtail_daisIE.notifications` | `wagtail_daisIE_notifications` | `EmailTemplate`, `Audience`, `AudienceMember`, `EmailCampaign`, `CampaignRecipientLog` | opt-in (extra `notifications`) |
| `wagtail_daisIE.allauth_ui` | `wagtail_daisIE_allauth_ui` | `AllauthPageOverride` | opt-in (extra `allauth`) |
| `wagtail_daisIE.allauth_emails` | `wagtail_daisIE_allauth_emails` | `AllauthEmailOverride` | opt-in (extra `allauth_emails`) |

**Dependency flow:** core → assets / menus / feeds / errors / notifications →
allauth_emails; allauth_ui → core + menus.

**Code-only packages (no models, no migrations):** `base_blocks/`, `blocks/`,
`choices/`, `pages.py`, `forms/`, `detail_pages/`, `icons/` (providers),
`favicon/` (views), `templatetags/`, `management/`, `static/`, `templates/`,
`middleware.py`, `utils.py`, `widgets.py`, `panels.py`, `telepath.py`,
`validators.py`, `arbitrary.py`, `context.py`.

`DaisyUITheme` and its orderables stay in core, so all existing
`from wagtail_daisIE.models import DaisyUITheme` imports keep working. Only
moved models need import rewrites.

---

## Phase 0 — Bug fixes

- `base_blocks/background_layer.py:137` — add
  `choices=BlockGradientShape.choices,` to `gradient_shape`.
- `demo/blog/management/commands/load_initial_data.py` in `_home_body` (hero
  dict around line 1094) — add
  `"size": {"height": {"height": "h-56"}}` to the hero's `design`.

---

## Phase 1 — Remove `LazyStreamField`

### 1.1 Replace with plain `StreamField`

In each file: remove the `from ..fields import LazyStreamField` import, add
`from wagtail.fields import StreamField`, and replace every `LazyStreamField(`
token with `StreamField(`.

| File | import line | call sites |
|---|---|---|
| `pages.py` | 17 | 55, 64, 76, 83, 94 |
| `models/menu.py` | 20 | 63, 125, 136, 153, 161 |
| `forms/models.py` | 20 | 44, 85, 92, 108 |
| `forms/fields.py` | 13 | 50, 57 |
| `allauth_ui/models.py` | 21 | 59, 65, 91 |
| `notifications/models.py` | 18 | 269 |
| `errors/models.py` | 10 | 48 |
| `dynamic/models.py` → `feeds/models.py` (Phase 2) | 14 | 128, 136, 143 |

### 1.2 Delete

- `src/wagtail_daisIE/fields.py` (and its `__pycache__`).
- `src/wagtail_daisIE/migrations/000{1,2,3}_*.py` (keep `__init__.py`).
- `src/wagtail_daisIE/test/migrations/0001_initial.py` (keep `__init__.py`).
- `demo/home/migrations/000{3,4,5}_*.py`.
- `demo/blog/migrations/000{3,4,5}_*.py`.

Keep `demo/home/migrations/0001_initial.py`, `0002_create_homepage.py` and
`demo/blog/migrations/0001_initial.py`, `0002_alter_blogpage_body.py` (June,
plain `StreamField`).

---

## Phase 2 — App split

### 2.1 Core `wagtail_daisIE`

- `models/__init__.py`: drop imports/`__all__` entries for `DaisyUIMenu`,
  `DaisyUIIconSource`, `DaisyUIFavicon`, `Feed`, `EmailTemplate`, `ErrorPage`,
  `Audience`, `AudienceMember`, `EmailCampaign`, `CampaignRecipientLog`,
  `AllauthEmailOverride`, `AllauthPageOverride`. Keep theme/background/boxes/
  colors/fonts/fields and the `BackgroundLayer`/`GradientStop` aliases.
- Move `models/menu.py` → `menus/models.py`; `models/icons.py` +
  `models/favicon.py` → `assets/models.py`.
- `apps.py`: keep telepath registration, `dynamic.panels` import,
  `detail_pages.bridges` connect. Remove seeding of icon sources, allauth
  email overrides and allauth page overrides (distributed to the owning apps).
- Add `blocks/registry.py`:
  - `_content: list[tuple[str, Block]]`, `_menu: list[tuple[str, Block]]`.
  - `register_content_block(name, block)`, `register_menu_block(name, block)`.
  - `content_block_contributions()`, `menu_block_contributions()`.
- `blocks/content_blocks.py`, `blocks/menu_items.py`: keep the core base lists,
  then extend with registry contributions and trigger optional registration at
  import time based on settings, e.g.
  ```python
  from django.conf import settings

  if "wagtail_daisIE.notifications" in settings.INSTALLED_APPS:
      from ..notifications.blocks import (
          MenuNewsletterBlock,
          NewsletterSignupBlock,
      )

      register_content_block("newsletter", NewsletterSignupBlock())
      register_menu_block("newsletter", MenuNewsletterBlock())
  ```

### 2.2 `assets` app

- Create `assets/{__init__,apps,migrations/__init__,models,view_sets}.py`.
- `assets/models.py` = `models/icons.py` + `models/favicon.py` contents.
- `assets/view_sets.py` = `DaisyUIIconSourceViewSet` + `DaisyUIFaviconViewSet`.
- `assets/apps.py`: `post_migrate` seed `DaisyUIIconSource.ensure_defaults()`
  (`dispatch_uid="wagtail_daisIE_assets.seed_icon_sources"`).

### 2.3 `menus` app

- Create `menus/{__init__,apps,migrations/__init__,models,view_sets}.py`.
- `menus/models.py` = `models/menu.py` (relative imports to
  `..base_blocks`, `..blocks.menu_items`, `..dynamic.blocks`,
  `..dynamic.resolvers`; plain `StreamField`).
- `menus/view_sets.py` = `DaisyUIMenuViewSet`.

### 2.4 `feeds` app (from `dynamic`)

- `dynamic/models.py` (`Feed`, `FeedFilterBlock`) → `feeds/models.py`.
- `dynamic/blocks_data.py` (`DATA_BLOCKS`, `ITEM_BLOCKS`, `FeedBlock`,
  `CalendarBlock`) → `feeds/blocks_data.py`; imports →
  `..dynamic.action_blocks`, `..dynamic.feeds`, `..dynamic.registry`;
  `SnippetChooserBlock("wagtail_daisIE.Feed")` →
  `"wagtail_daisIE_feeds.Feed"`.
- `dynamic/view_sets.py` (`FeedViewSet`) → `feeds/view_sets.py`.
- `blocks/content.py`: `DATA_BLOCKS` import → `..feeds.blocks_data`.
- Keep `dynamic/` as a code-only package (context models, resolvers, actions,
  bindings, `views.py`, `urls.py`, `forms.py`, `panels.py`, `mixins.py`,
  `registry.py`, `context.py`). Keep the `wagtail_daisIE_dynamic` URL namespace;
  `dynamic/views.py` `feed_items` imports `Feed` from `..feeds.models`.

### 2.5 `errors` app

- Add `errors/apps.py` + `errors/migrations/__init__.py`. No code moves; FK
  string `"wagtail_daisIE.DaisyUITheme"` unchanged.

### 2.6 `notifications` app (email + notifications)

Fold the former `emails/` package into `notifications/`:

- Move `emails/models.py` `EmailTemplate` into `notifications/models.py`
  (alongside `Audience`, `AudienceMember`, `EmailCampaign`,
  `CampaignRecipientLog`). Same-app FKs become `"EmailTemplate"`; `email_theme`
  stays `"wagtail_daisIE.DaisyUITheme"`.
- Move `emails/blocks/` → `notifications/email_blocks/`.
- Move `emails/mjml.py` → `notifications/mjml.py`.
- Move `emails/rendering.py` → `notifications/email_rendering.py`.
- Move `emails/view_sets.py` `EmailTemplateViewSet` + `EmailViewSetGroup` into
  `notifications/view_sets.py` (with `AudienceViewSet`,
  `EmailCampaignViewSet`).
- Keep existing helpers in place: `context.py`, `placeholders.py`, `panels.py`,
  `preview.py`, `rendering.py`, `bridges.py`, `campaigns.py`, `conf.py`,
  `registry.py`, `forms.py`, `views.py`, `urls.py`, `tasks.py`.
- `notifications/blocks.py`: `EmailVariableBlock`, `NewsletterSignupBlock`,
  and `MenuNewsletterBlock` (moved from core `blocks/menu_items.py`);
  `target_audience` chooser → `"wagtail_daisIE_notifications.Audience"`.
- Add `notifications/apps.py` (connect `notifications.bridges`) +
  `notifications/migrations/__init__.py`.
- Internal imports updated (`..emails.*` → local `.`).

### 2.7 `allauth_emails` app (opt-in)

- Create `allauth_emails/{__init__,apps,models,migrations/__init__,view_sets,
  allauth,catalogue}.py`.
- `models.py`: `AllauthEmailOverride` with FK
  `"wagtail_daisIE_notifications.EmailTemplate"`.
- `allauth.py` = `notifications/allauth.py`; `catalogue.py` =
  `notifications/allauth_catalogue.py`; `view_sets.py` =
  `AllauthEmailOverrideViewSet`.
- `apps.py`: `post_migrate` seed
  (`dispatch_uid="wagtail_daisIE_allauth_emails.seed_overrides"`).

### 2.8 `allauth_ui` app (opt-in)

- Add `allauth_ui/apps.py` + `allauth_ui/migrations/__init__.py`.
- Move `AllauthPageOverride.ensure_defaults` seeding and
  `register_template_dir()` from core `apps.py`.
- `allauth_ui/models.py`: menu FKs →
  `"wagtail_daisIE_menus.DaisyUIMenu"` (x2); theme FK unchanged.

### 2.9 Hooks and view sets

- Core `view_sets.py`: import theme from `.models`, menu view set from
  `.menus.view_sets`, icon/favicon from `.assets.view_sets`, `FeedViewSet` from
  `.feeds.view_sets`.
- `wagtail_hooks.py`: guard optional imports inside hook functions with
  `django.apps.apps.is_installed(...)`:
  - `wagtail_daisIE_allauth_ui` → `AllauthPageOverrideViewSet`.
  - `wagtail_daisIE_notifications` → `EmailViewSetGroup`,
    `EmailTemplateViewSet`, `AudienceViewSet`, `EmailCampaignViewSet`.
  - `wagtail_daisIE_allauth_emails` → `AllauthEmailOverrideViewSet`.
  - Theme/menu/assets/feeds/errors stay unconditional.

---

## Phase 3 — Rudimentary inline markup

### 3.1 Block and syntax

New `base_blocks/markup.py`:
```python
class InlineMarkupBlock(blocks.CharBlock):
    """Single-line text with rudimentary markup."""
```
Syntax (no nesting):
- `**bold**` → `<strong>`
- `_italic_` → `<em>`
- `__underline__` → `<u>`
- `~~strikethrough~~` → `<s>`
- `[text](url)` → `<a class="link" href="url">text</a>`

### 3.2 Renderer

`render_inline_markup(value, *, allow_links=True)`:
1. `render_placeholders(value, data, escape_literals=True)` — HTML-escape
   literals, substitute `{{ … }}`.
2. One combined regex pass, ordered `\*\*(?P<bold>.+?)\*\*`,
   `~~(?P<strike>.+?)~~`, `__(?P<u>.+?)__`, `_(?P<i>.+?)_`,
   `\[(?P<text>[^\]]+)\]\((?P<url>[^)]+)\)`.
3. Link arm validates `url` with `dynamic.resolvers.sanitize_url` (allow-list
   `""`, `http`, `https`, `mailto`, `tel`); invalid URLs keep the text and drop
   the anchor.
4. `mark_safe`.

Tags in `templatetags`: `{% daisie_markup value.text %}` (full) and
`{% daisie_markup value.text allow_links=False %}` (bold/italic/underline/
strike). `{% daisie_text %}` remains for genuinely plain fields.

### 3.3 Scope

Convert `CharBlock`/`TextBlock` → `InlineMarkupBlock` for user-visible
single-line text:

| Block | Convert | Keep plain |
|---|---|---|
| `blocks/inline.py` | `text` | — |
| `blocks/link.py` | `text` (Inline/Label/Button) | — |
| `blocks/display.py` | badge/kbd/divider `text`, stat `title`/`value`/`description`, chat `text`/`name`/`time`, timeline line, text-rotate items | — |
| `blocks/blockquote.py` | `text`, `attribute_name` | — |
| `blocks/marquee.py` | `text` | — |
| `blocks/layout_components.py` | indicator `item`, dropdown `trigger`, swap `on_text`/`off_text`, join `text` | `name`, `options`, `url` |
| `blocks/menu_items.py` | newsletter `heading`/`description`/`button_label` | `search_*`, `alt`, `action` |
| `blocks/inputs.py` | `label`, `helper_text`, `error_text`, fieldset `legend`/`description` | `name`, `placeholder`, `value`, `options`, `accept` |
| `notifications/blocks.py` | newsletter `heading`/`description`/`button_label` | key/value |
| `dynamic/action_blocks.py` | confirmation `text`, action button `text` | `target_expression` |

- Button/link labels and email use `allow_links=False` (bold/italic/underline/
  strikethrough only).
- `name`, `placeholder`, `value`, `accept`, `url`, `alt` stay plain (HTML
  attributes). `DaisieFormField.label` (Wagtail's form builder) is out of scope.
- `MenuBranding.fallback_alt` must strip tags from the wordmark.

### 3.4 Tests

Parser tests: each feature, `allow_links=False` drops links, URL allow-list,
disallowed HTML escaped, placeholders still substituted.

---

## Phase 4 — Admin-controlled `<main>` design

### 4.1 Composite and layout

`MainDesignBlock(SpacedDesignBlock)` in `base_blocks/design.py`, adding:
```python
layout = blocks.ChoiceBlock(
    choices=MAIN_LAYOUT_CHOICES, default="column", label=_("Layout")
)
```
`MAIN_LAYOUT_CHOICES` in `base_blocks/design.py` (or `choices/`):
- `column` → `flex flex-col grow`
- `row` → `flex flex-row grow`
- `grid` → `grid grow`

Add `build_layout_css` to `_DESIGN_BUILDERS` (key `layout`) and add these
literal classes to `management/commands/daisie_safelist.py`.

### 4.2 Fields

- `DaisyUITheme.main_design = StreamField([("main", MainDesignBlock())],
  blank=True, max_num=1)` — theme default.
- `StyledPageMixin.main_design = StreamField([("main", MainDesignBlock())],
  blank=True, max_num=1)` — page override.

### 4.3 Resolution and rendering

- Page value wins, else theme value; **no package fallback** (empty when unset).
- `daisyui_main_css = build_design_css(value)`.
- `daisyui_main_style = "background: " + BackgroundStreamBlock().get_css(...)`
  when a background layer is set.
- Exposed from `StyledPageMixin.get_context` and
  `DaisyUITheme.get_preview_context`; add `{% daisyui_main_attrs %}` for project
  base templates.

### 4.4 Templates

Replace hardcoded `<main class="…">` with the resolved attrs (keeping
`id="main-content"`):
- `demo/demo/templates/base.html:43`
- `src/.../errors/error_page.html:13`
- `src/.../forms/form_page.html:14`
- `src/.../forms/form_page_landing.html:13`
- `src/.../allauth_ui/.../allauth/base.html:20`
- wrap the theme preview body.

### 4.5 Seed the demo default theme

In `load_initial_data._ensure_theme`, seed the default theme's `main_design`
with the previous class set equivalent:
- `layout: "column"`
- `size.width: {"width": "w-full", "max_width": "max-w-6xl"}`
- `margin: {"left": "ml-auto", "right": "mr-auto"}`
- `padding: {"top": "pt-8", "right": "pr-4", "bottom": "pb-8", "left": "pl-4"}`

renders `grow w-full max-w-6xl ml-auto mr-auto pt-8 pr-4 pb-8 pl-4`
(equivalent to `mx-auto w-full max-w-6xl grow px-4 py-8`). Theme+page only, no
per-site override.

---

## Phase 5 — Settings, packaging, imports

### 5.1 `INSTALLED_APPS`

Add, in order, to `src/wagtail_daisIE/test/settings.py` and
`demo/demo/settings/base.py` (before project apps and before `allauth`):

```python
("wagtail_daisIE",)
("wagtail_daisIE.assets",)
("wagtail_daisIE.menus",)
("wagtail_daisIE.feeds",)
("wagtail_daisIE.errors",)
("wagtail_daisIE.notifications",)  # optional
("wagtail_daisIE.allauth_ui",)  # optional
("wagtail_daisIE.allauth_emails",)  # optional
```

### 5.2 Extras (`pyproject.toml`)

```toml
[project.optional-dependencies]
allauth = ["django-allauth>=65"]
allauth_emails = ["wagtail-daisIE[notifications,allauth]"]
notifications = []
blocks = ["draftail-text-utils>=0.3.1"]
```

"Install everything":

```sh
uv add "wagtail-daisIE[notifications,allauth,allauth_emails,blocks]"
# or: pip install "wagtail-daisIE[notifications,allauth,allauth_emails,blocks]"
```

### 5.3 Import rewrites

| Old import | New import |
|---|---|
| `wagtail_daisIE.models.DaisyUIMenu` | `wagtail_daisIE.menus.models.DaisyUIMenu` |
| `wagtail_daisIE.models.DaisyUIIconSource` / `DaisyUIFavicon` | `wagtail_daisIE.assets.models.*` |
| `wagtail_daisIE.models.Feed` / `wagtail_daisIE.dynamic.models` | `wagtail_daisIE.feeds.models.Feed` |
| `wagtail_daisIE.models.EmailTemplate` / `wagtail_daisIE.emails.models` | `wagtail_daisIE.notifications.models` |
| `wagtail_daisIE.models.ErrorPage` | `wagtail_daisIE.errors.models.ErrorPage` |
| `wagtail_daisIE.models.Audience` / `AudienceMember` / `EmailCampaign` / `CampaignRecipientLog` | `wagtail_daisIE.notifications.models.*` |
| `wagtail_daisIE.models.AllauthEmailOverride` | `wagtail_daisIE.allauth_emails.models.AllauthEmailOverride` |
| `wagtail_daisIE.models.AllauthPageOverride` | `wagtail_daisIE.allauth_ui.models.AllauthPageOverride` |
| `wagtail_daisIE.emails.mjml` | `wagtail_daisIE.notifications.mjml` |
| `wagtail_daisIE.emails.rendering` | `wagtail_daisIE.notifications.email_rendering` |
| `wagtail_daisIE.notifications.allauth` / `.allauth_catalogue` | `wagtail_daisIE.allauth_emails.allauth` / `.catalogue` |
| `wagtail_daisIE.models` theme imports | unchanged |

Sites to touch: `view_sets.py`, `wagtail_hooks.py`,
`templatetags/wagtail_daisIE_tags.py`, `icons/registry.py`, `favicon/views.py`,
`dynamic/views.py`, `errors/handlers.py`, `tests/test_menu_context.py`,
`tests/test_menu_design.py`, `tests/test_template_tags_blocks.py`,
`tests/test_models_blocks.py`, `tests/test_favicon.py`,
`tests/test_email_blocks.py`, `tests/test_email_mjml.py`,
`tests/test_notification_allauth.py`,
`tests/test_notification_allauth_catalogue.py`,
`demo/blog/management/commands/load_initial_data.py`, `demo/home/tests.py`.

### 5.4 Migration regeneration

1. `uv run ./demo/manage.py makemigrations wagtail_daisIE wagtail_daisIE_assets wagtail_daisIE_menus wagtail_daisIE_feeds wagtail_daisIE_errors wagtail_daisIE_notifications wagtail_daisIE_allauth_ui wagtail_daisIE_allauth_emails`
2. `uv run ./demo/manage.py makemigrations wagtail_daisIE_test`
3. `uv run ./demo/manage.py makemigrations home blog`
4. Confirm `demo/home/migrations/0002_create_homepage.py` still resolves.

---

## Phase 6 — Docs and changelog

- `AGENTS.md`: replace the `LazyStreamField` invariant with "model
  `StreamField`s are plain `wagtail.fields.StreamField`; the block tree is
  frozen into the owning app's migration". Add the app/migration ownership
  table, the optional apps + extras notes, the markup rules, and the `<main>`
  design. Update the project layout.
- `docs/architecture.md`: remove the `fields.py` line; update `models/`; add an
  "Apps and migrations" section; document `dynamic` (code) vs `feeds` (models)
  and `notifications` (email + notifications).
- `docs/design-system.md`: add the rudimentary markup syntax and the `<main>`
  container (`MainDesignBlock`, resolution, tag).
- `docs/emails.md`, `docs/notifications.md`: email now lives in
  `notifications`; `[notifications]` extra/app.
- `docs/allauth.md`, `docs/allauth-pages.md`: `[allauth]` +
  `wagtail_daisIE.allauth_ui`.
- `docs/{menus,favicon,error-pages,data-components}.md`: required app entries.
- `README.md`: required vs optional apps and the all-extras install command.
- `CHANGELOG.md` under `[Unreleased]`:
  - Removed `LazyStreamField`; model `StreamField`s are plain.
  - Split into apps: `assets`, `menus`, `feeds`, `errors`, `notifications`
    (email + notifications), `allauth_ui`, `allauth_emails`.
  - Rudimentary inline markup (bold/italic/underline/strikethrough/link).
  - Admin-controlled `<main>` design on theme and page.
  - Fixed gradient-shape choices and demo hero height.
  - Breaking: apps must be added to `INSTALLED_APPS`; moved models get new app
    labels/table names.

---

## Verification

```sh
just lint
just test
uv run ./demo/manage.py check
uv run ./demo/manage.py makemigrations --check --noinput
uv run ./demo/manage.py test home
```

Manual smoke test: fresh demo DB → `just demo` → open the homepage in the
admin, edit, save, reopen → the body persists; gradient shape select populated;
hero renders at `h-56`; markup renders bold/italic/underline/strike/link with
`class="link"`; `<main>` uses the seeded/edited design.

---

## Product roadmap (unchanged vision)

## 1.x

- Additional daisyUI block components (carousel, tabs, stats, timeline).
- Per-page and per-menu background layer previews in the admin.
- Richer icon provider options (cache warming, self-hosted manifests).
- More demo content mirroring the Wagtail Bakery demo.

## Later

- Theme import/export.
- A block styleguide page generated from the registered blocks.
