# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0](https://github.com/baldwinboy/wagtail-daisIE/compare/v1.1.0...v1.2.0) (2026-09-25)


### Features

* enable form ordering ([80c872c](https://github.com/baldwinboy/wagtail-daisIE/commit/80c872c47b6825493a894d68a8564dc711c32d2d))

## [Unreleased]

### Added

- **Rudimentary inline markup**: user-visible single-line text now renders
  `**bold**`, `_italic_`, `__underline__`, `~~strikethrough~~` and
  `[text](url)` (scheme allow-list) via `InlineMarkupBlock` and the
  `{% daisie_markup %}` tag; use the `daisie_strip_markup` filter for HTML
  attributes. See `docs/design-system.md`.
- **Admin-controlled `<main>` design**: `MainDesignBlock` on the theme
  (`DaisyUITheme.main_design`) and page (`StyledPageMixin.main_design`) sets the
  main container's layout (`column`/`row`/`grid`), spacing and background; the
  page value wins, and templates use `{% daisyui_main_attrs %}`.
- **Approval workflows**: settings-driven `WAGTAIL_DAISIE_APPROVAL_WORKFLOWS`
  converts a record once an editor flips its approval field, with an optional
  FK recording the result. See `docs/approval.md`.
- **Allauth page overrides**: `AllauthPageOverride` snippets let editors design
  allauth **account** pages (theme, background, page defaults, body with
  `auth_form`/`auth_field` blocks). Look-only; allauth owns fields and
  validation. See `docs/allauth-pages.md`.
- **`check_allauth_templates`** management command to detect/regenerate drift in
  the bundled allauth account template overrides.
- **Feed model properties help panel**: a `<details>` panel on the Feed editor
  listing the available properties and filters for the selected model.
- **Committed Tailwind + daisyUI stylesheet**: `daisie.css` is prebuilt from
  `tailwind/input.css` plus a generated safelist and served through staticfiles;
  `{% daisyui_styles %}` emits the render-blocking link and
  `ArbitraryCSSMiddleware` covers arbitrary colour utilities. Regenerate with
  `just build-css`. See `docs/assets.md`.
- **Background layers**: design backgrounds use `BackgroundStreamBlock`
  (solid/image/gradient) and render as an inline `block_style`; `TextBackgroundBlock`
  is retained for email components that only accept a colour.
- **Typography underline + states**: `underlines` (`text_decoration`), colour,
  thickness, and configurable `hover`/`active` states on every typography block.
- **Breadcrumbs block**: a placeable `BreadcrumbsBlock` (auto page trail or a
  manual list of crumbs with links/icons) for pages, form pages and allauth.
- **Menu design split + responsive menus**: `menu_design` styles the menu
  container independently of `item_design`; navbar renders a daisyUI
  **megamenu** on desktop, plus new `megamenu` and `dock` layouts.
- **MJML backgrounds per component**: backgrounds map only to the attributes a
  component supports (`background-color`/`container-background-color`/`inner-…`,
  images only on section/wrapper/hero); gradients are dropped.
- **allauth OTP + validator**: one-time-code fields render the daisyUI `otp`
  component and form fields carry `validator` states.
- **Component catalog**: new blocks for avatar, badge, kbd, divider, stat,
  countdown, skeleton, text-rotate, chat, timeline, diff, hover-gallery,
  hover-3d, stack, aura, indicator, mask, dropdown, swap, tabs, carousel,
  pagination, FAB, drawer, hero, filter, join and the four mockups.
- **Action** blocks are now a struct of a normal button subclass and an optional
  confirmation **alert**; the confirmation is added to Django messages and
  rendered by `{% daisie_messages %}`. Actions are available in pages, menus,
  feeds, calendars and cards.
- **Clickable cards**: a button or action inside a card can set *Make the parent
  card clickable* to stretch itself over the card.
- **MJML components**: accordion, carousel, column, group, hero, navbar, social
  and table, plus email-safe icons (`{% daisyui_email_icon %}`).
- **Theme persistence** (`{% daisyui_theme_script %}`) and cookie-aware
  django-allauth theming.
- **Email preview sample values**: previews now show a sample recipient,
  synthesised `payload.*` values and stubbed context models.
- **Form field** body block on `DaisieFormPage`, letting editors interleave
  form inputs with content blocks in any order. Inputs rendered outside the
  `<form>` are associated with it via `form="daisie-form"`.
- `payload.submission` in the form page landing context, exposing the stored
  `FormSubmission` data to `success_body` placeholders.
- **Configurable form field types**: register extra types for `DaisieFormPage`
  via `WAGTAIL_DAISIE_FORM_FIELD_TYPES` — a Django form field class (or a
  `(field, options) -> Field` factory), a widget and DaisyUI classes. Types
  marked `is_upload` accept a file; a required `handler` callable (per type or
  `WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER`) decides where it is stored and returns
  the JSON-safe reference recorded in the submission. See `docs/forms.md`.
- **DaisyUI Editor Guide**: a multi-page guide in the admin help menu
  (Getting started, Concepts, How-to, Reference), covering themes, page blocks
  and design, menus, feeds, forms, notifications, icons, error pages and
  allauth. The block reference is generated from the registered blocks so it
  cannot drift.

### Changed

- **Split into per-feature apps** — `assets`, `menus`, `feeds`, `errors`,
  `notifications` (email + notifications), `allauth_ui` and `allauth_emails` —
  each with its own migrations/label. `notifications`, `allauth_ui` and
  `allauth_emails` are opt-in. Email moved from `emails/` into
  `notifications/`; `Feed` moved from `dynamic/` into `feeds/`. See the README
  for the app list and extras.
- Icons inherit the size and colour of their parent button.
- The image block hides `image`/`image_expression` based on the chosen source;
  image expressions use the canonical `{{ bread.image }}` form.
- The theme preview (`DaisyUITheme`) now loads the configured values.
- Form page bodies now accept form fields; any field not placed in the body is
  still rendered above the submit button, so existing pages are unaffected.
- Static choice lists are wrapped in `choicelist.ChoiceList`, so migrations
  store a short registry reference instead of every option; redundant `label`
  copy and long `help_text` were trimmed, and package and demo migrations were
  regenerated (~15% smaller, ~70% smaller than before choice compaction).
  Editing a choice list no longer produces a schema-only `AlterField`
  migration.
- The Bread chooser is hidden on the **Bread suggestions** snippet; the linked
  Bread is still set automatically by the approval workflow.

### Fixed

- Page/snippet designs with no background layer can be saved again
  (`BackgroundStreamBlock` is no longer required inside design composites).
- The image block's **Static image** / **From context** fields toggle as
  intended (added the missing Telepath adapter for `ImageBlock`).
- Page save/preview no longer fails with
  `MultiValueDictKeyError: 'body-count'`: `image_block.js` is now loaded through
  the `ImageBlock` adapter's media (after Wagtail's telepath runtime) instead of
  globally, so a script-order error can no longer leave the body StreamField
  widget uninitialised.
- Background-layer and audience block adapters no longer throw while rendering
  (`Cannot read properties of null (reading 'style')`); a thrown render aborted
  the StreamField child and dropped blocks when saving.
- Save-blocking field validation is fixed: `BooleanBlock`s are now optional
  (background layer *Repeat*, table zebra/pin rows and columns, link/button
  *Icon after*, menu *Logo after*), and fields that relied on the no-op
  `blank=True` (background position and gradient options, link/button/marquee/
  copyright/inline text) are now genuinely optional via `required=False`.
- Action buttons no longer raise
  `MultiValueDictKeyError: '…-destination-count'` when saving
  (`ActionButtonBlock` removes the inherited, unrendered destination stream).
- Approving a bread suggestion now creates the `Bread` (and its generated
  detail page) via an approval workflow.
- Gradient-shape choices render and the demo hero no longer collapses.
- Removed Django 7.0 `RemovedInDjango70Warning`s by configuring `MAILERS`.

### Removed

- **`LazyStreamField`** (and `src/wagtail_daisIE/fields.py`); model
  `StreamField`s are plain `wagtail.fields.StreamField` frozen into the owning
  app's migration.
- The precompiled `global.css`, the `npm run compile-global-css` step and the
  Tailwind `@source inline(...)` safelists (CSS is now compiled JIT).

### Breaking

- Add the new apps to `INSTALLED_APPS` (core, `assets`, `menus`, `feeds`,
  `errors`, plus the opt-in `notifications`/`allauth_ui`/`allauth_emails`) and
  run the regenerated migrations: moved models get new app labels and table
  names.
- `<main>` no longer ships hardcoded container classes; set
  `DaisyUITheme.main_design` (and optionally `StyledPageMixin.main_design`) or
  the container renders unstyled.

### Validation

- Saving a form page that places the same field more than once now raises a
  validation error on the body field.

## [1.1.0](https://github.com/baldwinboy/wagtail-daisIE/compare/v1.0.0...v1.1.0) (2026-09-22)


### Features

* add context bindings ([3f180cf](https://github.com/baldwinboy/wagtail-daisIE/commit/3f180cf287d886035e62f07770aa20dcc3bfa598))
* add draftail_text_utils plugin ([2cb3134](https://github.com/baldwinboy/wagtail-daisIE/commit/2cb31344e023e04992fc4d58630d566a85188ae7))
* add email logic and filters ([ae267eb](https://github.com/baldwinboy/wagtail-daisIE/commit/ae267eb8135961df9b833debda8336db2b31a036))
* add email templates ([d612491](https://github.com/baldwinboy/wagtail-daisIE/commit/d612491d8c40ae2a166ce192130fcb622613d1ab))
* add filters ([065e551](https://github.com/baldwinboy/wagtail-daisIE/commit/065e55168beaece7b608fad806fa1792a7b2a94f))
* add settings layout ([1e59ea4](https://github.com/baldwinboy/wagtail-daisIE/commit/1e59ea457e8aa7b47111258e005c6c83e878a01f))
* add table block ([cc183ca](https://github.com/baldwinboy/wagtail-daisIE/commit/cc183caba88416c2309fc3b3cd38d881348f1e67))


### Bug Fixes

* add release please config ([1d9ae19](https://github.com/baldwinboy/wagtail-daisIE/commit/1d9ae1980c7bbaab967f81f81ac1f761a353edb3))
* add release please manifest ([5a1a162](https://github.com/baldwinboy/wagtail-daisIE/commit/5a1a162fcaa3c5da9202943f19c9a2b70d722084))
* add workflow call ([55ec604](https://github.com/baldwinboy/wagtail-daisIE/commit/55ec604d1ba5a6888fd8ab74f5c1cdc5e9523734))
* exclude migrations from linting ([4552da1](https://github.com/baldwinboy/wagtail-daisIE/commit/4552da1f9c101538faed07e052abb7636db1e62d))
* remove incompatible python version tests ([8d57403](https://github.com/baldwinboy/wagtail-daisIE/commit/8d574039a31ec7e3540c6c52b91b71a49235113f))
* remove incompatible wagtail version tests ([6c70d3b](https://github.com/baldwinboy/wagtail-daisIE/commit/6c70d3bab19f9dc71c71858f2d41df4d26d8c472))
* remove template check ([012d7a0](https://github.com/baldwinboy/wagtail-daisIE/commit/012d7a0d2bae565b74ab513461d90741be7d9a0b))

## [1.0.0] - 2026-09-16

### Added

- `base_blocks/` package of reusable design primitives (size, box, background,
  typography, link, audience, background layers) and a `block_css` pipeline that
  every themed block shares.
- `MenuItemDesignBlock` and `DaisyUIMenu.item_design`, letting editors set
  menu-wide font, colour, background, spacing and size defaults that cascade
  into every item while per-item settings still apply.
- `DaisyUIMenu.menu_theme` (falls back to the default theme) and a single
  `branding` field built from the `MenuBranding` block (logo and/or wordmark,
  optionally wrapped in a link).
- `font_family` selection on every `TypographyBlock`, populated from the current
  theme's font-family roles and rendered as `font-<role>`.
- Universal icon provider registry (Wagtail, Iconify, webfont, custom), an admin
  `DaisyUIIconSource` snippet, a `register_icon_providers` hook, and
  `{% daisyui_icon %}` / `{% daisyui_icon_assets %}` tags.
- Author docs (`docs/`) and a repo-local `wagtail-daisie` agent skill.
- Fixture-driven demo loader reading `demo/fixtures/content.json` and media,
  then seeding themes and menus programmatically.

### Changed

- Menus now reuse the same blocks as page bodies (`MENU_ITEM_BLOCKS` is a curated
  subset of the public blocks), with semantic DaisyUI navbar/footer/sidebar
  markup.
- `LinkDestinationBlock` is a custom `StreamBlock` nested directly inside
  `AbstractLinkBlock` (required on `LabelLinkBlock`/`InlineLinkBlock`).
- The demo project renders page `body` StreamFields and the bundled
  `{% daisyui_global_css %}` stylesheet instead of the Bootstrap UI.

### Removed

- Per-menu `bg_color`/`text_color`/`menu_size` and the branding model fields, in
  favour of `item_design` and the `branding` block.
- The legacy menu block classes (`MenuLinkBlock`, `MenuButtonBlock`, ...) and
  their templates, plus the unused `MenuBlock`.

### Fixed

- The package now imports and migrates cleanly on Django 6 (`CheckConstraint`
  `condition=`), with corrected block exports and a single squashed migration.
- Link destinations resolve through `link_url`/`link_is_active` for both
  `StreamValue` and legacy values.
- Background-layer blocks build CSS from the bound value rather than the block
  instance.

## [0.2.0](https://github.com/baldwinboy/wagtail-daisIE/compare/v0.1.3...v0.2.0) (2026-07-21)


### Features

* add draftail_text_utils plugin ([2cb3134](https://github.com/baldwinboy/wagtail-daisIE/commit/2cb31344e023e04992fc4d58630d566a85188ae7))

## [0.1.3](https://github.com/baldwinboy/wagtail-daisIE/compare/v0.1.2...v0.1.3) (2026-06-11)


### Bug Fixes

* add release please config ([1d9ae19](https://github.com/baldwinboy/wagtail-daisIE/commit/1d9ae1980c7bbaab967f81f81ac1f761a353edb3))
* add release please manifest ([5a1a162](https://github.com/baldwinboy/wagtail-daisIE/commit/5a1a162fcaa3c5da9202943f19c9a2b70d722084))
* add workflow call ([55ec604](https://github.com/baldwinboy/wagtail-daisIE/commit/55ec604d1ba5a6888fd8ab74f5c1cdc5e9523734))
* exclude migrations from linting ([4552da1](https://github.com/baldwinboy/wagtail-daisIE/commit/4552da1f9c101538faed07e052abb7636db1e62d))
* remove incompatible python version tests ([8d57403](https://github.com/baldwinboy/wagtail-daisIE/commit/8d574039a31ec7e3540c6c52b91b71a49235113f))
* remove incompatible wagtail version tests ([6c70d3b](https://github.com/baldwinboy/wagtail-daisIE/commit/6c70d3bab19f9dc71c71858f2d41df4d26d8c472))
* remove template check ([012d7a0](https://github.com/baldwinboy/wagtail-daisIE/commit/012d7a0d2bae565b74ab513461d90741be7d9a0b))

## [0.1.2](https://github.com/baldwinboy/wagtail-daisIE/compare/v0.1.1...v0.1.2) (2026-06-10)


### Bug Fixes

* remove incompatible wagtail version tests ([6c70d3b](https://github.com/baldwinboy/wagtail-daisIE/commit/6c70d3bab19f9dc71c71858f2d41df4d26d8c472))

## [0.1.1](https://github.com/baldwinboy/wagtail-daisIE/compare/v0.1.0...v0.1.1) (2026-06-10)


### Bug Fixes

* remove incompatible python version tests ([8d57403](https://github.com/baldwinboy/wagtail-daisIE/commit/8d574039a31ec7e3540c6c52b91b71a49235113f))

## 0.1.0 (2026-06-09)


### Bug Fixes

* add release please config ([1d9ae19](https://github.com/baldwinboy/wagtail-daisIE/commit/1d9ae1980c7bbaab967f81f81ac1f761a353edb3))
* add release please manifest ([5a1a162](https://github.com/baldwinboy/wagtail-daisIE/commit/5a1a162fcaa3c5da9202943f19c9a2b70d722084))
* add workflow call ([55ec604](https://github.com/baldwinboy/wagtail-daisIE/commit/55ec604d1ba5a6888fd8ab74f5c1cdc5e9523734))
* exclude migrations from linting ([4552da1](https://github.com/baldwinboy/wagtail-daisIE/commit/4552da1f9c101538faed07e052abb7636db1e62d))
* remove template check ([012d7a0](https://github.com/baldwinboy/wagtail-daisIE/commit/012d7a0d2bae565b74ab513461d90741be7d9a0b))

<!-- TEMPLATE - keep below to copy for new releases -->
<!--


## [x.y.z] - YYYY-MM-DD

### Added

- ...

### Changed

- ...

### Removed

- ...

-->
