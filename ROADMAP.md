# ROADMAP — Design inheritance, action components, and editor guide

## How to read this roadmap

Each story records:

- **Required task** — the implementation outcome.
- **Acceptance criteria** — testable conditions for “done”.
- **Expected file changes** — likely files; add/remove as implementation proves necessary.
- **Blocking stories** — must complete first.
- **Current status** — `Ready`, `Blocked`, or `Not started`.

Status legend:

- **Ready** — no blocker; can start.
- **Blocked** — depends on the listed stories.
- **Not started** — no implementation has begun.
- **In progress / In review / Done** — update when work starts.

## Definition of done for every story

- [ ] Acceptance criteria met.
- [ ] New/changed behaviour has regression tests.
- [ ] `just lint` passes.
- [ ] `just test` passes.
- [ ] `uv run ./demo/manage.py makemigrations --check --noinput` passes.
- [ ] Relevant help guide and repository docs updated.
- [ ] No debug code, dead code, `print`, or commented-out blocks.
- [ ] Claims about behaviour are evidenced by tests or handover output.

---

# Epic 1 — Design inheritance and menu isolation

**Outcome:** page defaults remain global, but a block’s own design no longer
cascades into descendants. Menus are isolated from page design, and menu item
defaults stop at the top-level item/trigger.

## DI-1 — Stop parent design cascading

**User story:** As an editor, I want a block’s design to style that block only,
so that nested cards, fields and components do not duplicate the parent’s
padding, background or border.

**Required task:**
- In `ThemedBlock.get_context`, keep the page category channel in `block_css`.
- Remove the write-back of the category channel (`context[key] = channel + own`).
- Explicitly blank `menu_default_css` and `menu_default_style` for descendants
  after computing the current block’s `block_css`/`block_style`.
- Update the `ThemedBlock` docstring and design-system docs.

**Acceptance criteria:**
- [ ] Page `container_css`/`text_css`/`button_css`/`media_css` still reach every
      block of that category.
- [ ] A nested block does not receive the parent block’s own design classes.
- [ ] A menu item’s `item_design` applies to the top-level item only.
- [ ] Existing tests are updated to the new inheritance contract.
- [ ] A regression test covers “parent design does not cascade, page channel does”.

**Expected file changes:**
- `src/wagtail_daisIE/base_blocks/design.py`
- `tests/core/test_page_design.py`
- `tests/blocks/test_blocks.py`
- `docs/design-system.md`
- `docs/architecture.md`
- `AGENTS.md`

**Blocking stories:** none.

**Current status:** Not started — **Ready**.

---

## DI-2 — Isolate menus from page design

**User story:** As a site builder, I want menus to use their own theme, container
design and item defaults, not the current page’s default design.

**Required task:**
- In `menu_block.html`, clear `container_css`, `text_css`, `button_css` and
  `media_css` for the menu render while preserving request/context values.
- Confirm the menu preview and live rendering agree.

**Acceptance criteria:**
- [ ] Page default design classes do not appear on menu items or menu branding.
- [ ] Menu theme, `menu_design` and `item_design` still work.
- [ ] Horizontal, vertical, footer, sidebar, navbar, megamenu and dock layouts
      are covered by tests.

**Expected file changes:**
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/menu_block.html`
- `tests/menus/test_menu_design.py`

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

## DI-3 — Isolate branding and render it in every menu layout

**User story:** As an editor, I want menu branding to be independent of menu
items and available in every menu layout.

**Required task:**
- In `MenuBranding.get_context`, clear `menu_default_css`/`menu_default_style`
  before calling `super()`.
- Add branding to `horizontal_menu.html`, `vertical_menu.html` and `dock.html`,
  matching the existing navbar/footer/sidebar/megamenu placement before items.
- Ensure branding markup is valid for each container (`li` for list layouts).

**Acceptance criteria:**
- [ ] Branding ignores page design and `item_design` padding/background/typography.
- [ ] Branding appears exactly once in every layout that supports it.
- [ ] Branding tests cover all `MENU_LAYOUT_CHOICES`.
- [ ] Wordmark and logo keep their own designs and accessible labels.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/menu_items.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/horizontal_menu.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/vertical_menu.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/dock.html`
- `tests/menus/test_menu_design.py`

**Blocking stories:** DI-1, DI-2.

**Current status:** Not started — **Blocked by DI-1, DI-2**.

---

## DI-4 — Render LinkList design and unify top-level menu links

**User story:** As an editor, I want top-level menu links and megamenu triggers
to share the same default link styling, while nested link lists use their own
container design.

**Required task:**
- Keep the megamenu trigger as `<button type="button">`.
- Apply `item_design` plus the heading’s own design to the trigger root.
- Add the shared `link link-hover` contract to the trigger.
- Add `daisie_design_css` / `daisie_design_style` template tags for own-design-only.
- Apply `LinkListBlock.design` (classes and background style) to the megamenu
  submenu panel.
- Render nested links with menu defaults cleared so they use their own design.
- Remove the explicit `menu_default_css` forwarding in `list.html`.
- Verify native button chrome; add only a scoped reset that does not override
  editor spacing/background/border.

**Acceptance criteria:**
- [ ] A plain top-level link and a `link_list` trigger receive the same item
      default class contract and `link link-hover`.
- [ ] A `link_list` trigger is still a button and keeps `popovertarget`.
- [ ] The submenu panel renders the LinkList design classes/style.
- [ ] Nested links do not receive `item_design`.
- [ ] `LinkListBlock.design` still renders on normal list layouts.
- [ ] Regression tests assert trigger classes, submenu design, and nested-link isolation.

**Expected file changes:**
- `src/wagtail_daisIE/templatetags/wagtail_daisIE_tags.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/megamenu.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/list.html`
- `tests/menus/test_menu_design.py`
- `docs/menus.md`

**Blocking stories:** DI-1, DI-2.

**Current status:** Not started — **Blocked by DI-1, DI-2**.

---

## DI-5 — Remove inherited CSS from the Action block wrapper

**User story:** As an editor, I want an action button inside a card or section to
use its own button design, not the surrounding container’s CSS.

**Required task:**
- Blank inherited `block_css`/`block_style` in `ActionBlock.get_context`, or
  remove their use from `action_button.html`.
- Keep the nested `ActionButtonBlock` design and menu item defaults intact.

**Acceptance criteria:**
- [ ] The outer action `<form>` no longer renders parent padding/background/border.
- [ ] The nested button still renders its own design.
- [ ] Test covers an Action block inside a Card/Section context.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_button.html`
- `tests/dynamic/test_action_blocks.py`

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

## DI-6 — Add Action form container design and field fallback

**User story:** As an editor, I want to style the action form wrapper separately
from its fields, and have fields use their own design or the page default.

**Required task:**
- Add `container_design = SpacedDesignBlock(required=False)` to `ActionFormBlock`.
- Apply `form_css`/`form_style` to the `<form>` only.
- Do not push the form design into `container_css`.
- Ensure fields get page `container_css` plus their own design.
- Add the form design field to the settings form layout.

**Acceptance criteria:**
- [ ] `container_design` renders on the form and nowhere else.
- [ ] Fields with no design fall back to the page container channel.
- [ ] Fields never receive an ancestor card/tab/fieldset design.
- [ ] Tests cover form design, own field design and page default fallback.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_form.html`
- `tests/dynamic/test_action_blocks.py`
- `docs/data-components.md`

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

## DI-7 — Audit remaining container inheritance

**User story:** As a maintainer, I want evidence that tabs, reusable blocks and
calendar events follow the new inheritance rule.

**Required task:**
- Add regression tests for:
  - tab-panel children do not inherit the tab-strip `design`;
  - `panel_design` still applies to the panel;
  - reusable content does not inherit the reusable wrapper design;
  - calendar event content does not inherit the calendar wrapper design.
- Update tests/docs that previously asserted the old cascade.

**Acceptance criteria:**
- [ ] The tests above exist and pass.
- [ ] Docs no longer claim block design cascades to descendants.
- [ ] Any intentional exception is documented with a test.

**Expected file changes:**
- `tests/core/test_page_design.py`
- `tests/blocks/test_blocks.py`
- `tests/feeds/test_data_components.py`
- `docs/design-system.md`
- `docs/architecture.md`

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

# Epic 2 — Action button behaviour

**Outcome:** action buttons render their configured dialog/alert only when
configured, support design of the dialog, and work in clickable cards and
icon-only contexts.

## AB-1 — Convert confirmations to optional one-item streams

**User story:** As an editor, I do not want an empty confirmation dialog forced
onto every action button.

**Required task:**
- Convert `ActionButtonBlock.confirm` to a one-item `StreamBlock`
  (`required=False`, `max_num=1`).
- Convert `ActionBlock.confirmation` and `ActionFormBlock.confirmation` to
  one-item `StreamBlock`s.
- Add `to_python` adapters accepting legacy confirmation dicts.
- Render only when the stream has an item.

**Acceptance criteria:**
- [ ] No configured dialog → no modal and a direct submit button.
- [ ] No configured alert → no hidden message values and no alert.
- [ ] Legacy dict values render correctly and normalize on save.
- [ ] New stream values render correctly.
- [ ] No data migration required; old data remains readable.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `tests/dynamic/test_action_blocks.py`

**Blocking stories:** none.

**Current status:** Not started — **Ready**.

---

## AB-2 — Render and design the pre-submit dialog in all modes

**User story:** As an editor, I want a configured confirmation dialog to render
consistently, including when the action button makes a whole card clickable.

**Required task:**
- Extract the dialog into `action_confirm_dialog.html`.
- Include it from normal and `stretch_to_parent` branches.
- In clickable-card mode, make the overlay open the dialog instead of submitting.
- Add `panel_design`, `confirm_appearance` and `cancel_appearance` to
  `ActionConfirmBlock`.
- Apply panel classes/background style and button appearance.
- Add dialog accessibility attributes.

**Acceptance criteria:**
- [ ] Configured dialog renders title/text/confirm label.
- [ ] Dialog renders in normal and clickable-card modes.
- [ ] Dialog design classes/style appear on `.modal-box`.
- [ ] Confirm/cancel buttons use their configured appearance.
- [ ] Cancel closes without submitting.
- [ ] Empty confirm stream renders no dialog.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_button_inner.html`
- new `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_confirm_dialog.html`
- `tests/dynamic/test_action_blocks.py`
- `docs/data-components.md`

**Blocking stories:** AB-1, DI-5.

**Current status:** Not started — **Blocked by AB-1, DI-5**.

---

## AB-3 — Render post-submit alert values and remove the silent fallback

**User story:** As an editor, I want the post-submit alert to show exactly the
text, icon and styles I configured, and no alert when I configured none.

**Required task:**
- Read the first item of the confirmation stream in `_confirmation_context`.
- Render hidden `daisie_message*` inputs only when confirmation is configured.
- Remove the unconditional “Saved” fallback from `action_form_status.html`.
- Add an alert-level fallback class when no colour/style/direction is set.
- Verify plain POST + messages and htmx inline paths use the same values.

**Acceptance criteria:**
- [ ] Configured text/icon/colour/style/direction reach messages and the inline fragment.
- [ ] No configured confirmation produces no alert.
- [ ] Alert classes are allowlisted and escaped.
- [ ] Action form inline/reload/navigate behaviours still work.
- [ ] Tests cover configured and unconfigured paths.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/dynamic/views.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_button.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_form.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_form_status.html`
- `tests/dynamic/test_action_blocks.py`
- `docs/htmx.md`
- `docs/data-components.md`

**Blocking stories:** AB-1.

**Current status:** Not started — **Blocked by AB-1**.

---

## AB-4 — Restore icon-only action links/buttons and labels

**User story:** As an editor, I want an action button or menu link with an icon
and no text to show the icon and remain accessible.

**Required task:**
- Add an optional accessible label to `LabelLinkBlock`/`ButtonBlock`.
- Render icon-only controls with `inline-flex items-center justify-center`.
- Add `aria-label` when visible text is empty.
- Keep decorative icons hidden from assistive technology.
- Add a regression test for an icon with empty text.

**Acceptance criteria:**
- [ ] Icon-only menu links/buttons render the SVG and an accessible label.
- [ ] Text + icon rendering is unchanged.
- [ ] Tests cover empty text, icon only and icon + text.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/link.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/link.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/button.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_button_inner.html`
- `tests/blocks/test_blocks.py`
- `tests/menus/test_menu_design.py`
- `docs/accessibility` guidance in the help guide

**Blocking stories:** AB-2.

**Current status:** Not started — **Blocked by AB-2**.

---

# Epic 3 — Action form behaviour and presets

**Outcome:** action forms can be configured by developers, editor fields are
optional overrides, and checkbox/toggle fields lay out predictably.

## AF-1 — Make fields optional and add the action field schema

**User story:** As a developer, I want to define an action’s fields in settings
so editors do not have to recreate them.

**Required task:**
- Set `ActionFormBlock.fields.required = False`.
- Add optional `fields` to `WAGTAIL_DAISIE_ACTIONS` entries.
- Add `get_action_fields(key)` in `dynamic/actions.py`.
- Define supported types and per-type keys.
- Add a system check for malformed field specs.

**Acceptance criteria:**
- [ ] An action form with no editor fields and no config fields is valid.
- [ ] Config fields are returned in declaration order.
- [ ] Unsupported types/duplicate names/missing options are reported by `checks`.
- [ ] Existing action configs without `fields` still work.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/actions.py`
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/checks.py`
- `tests/dynamic/test_action_blocks.py`
- `tests/core/test_checks.py` (or existing checks tests)
- `docs/data-components.md`

**Blocking stories:** none.

**Current status:** Not started — **Ready**.

---

## AF-2 — Render preset fields and match editor overrides

**User story:** As an editor, I want configured fields to appear automatically,
and to style or relabel them with matching editor fields.

**Required task:**
- In `ActionFormBlock.get_context`, resolve config fields and editor fields.
- Render config fields through the existing input block classes with stable IDs.
- Editor fields with matching `Field name` override the preset field.
- Preserve config order; missing editor fields fall back to presets.
- Render a vertical, `w-full` field stack.

**Acceptance criteria:**
- [ ] No editor fields + config fields → preset fields render.
- [ ] Matching editor field → editor design/label/help is used.
- [ ] Partial overrides leave the remaining preset fields rendered.
- [ ] No config fields + editor fields → current behaviour preserved.
- [ ] Neither → button-only form.
- [ ] Preset checkbox fields do not overlap.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/dynamic/actions.py`
- new preset-field/helper templates under
  `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_form.html`
- `tests/dynamic/test_action_blocks.py`
- `docs/data-components.md`

**Blocking stories:** AF-1.

**Current status:** Not started — **Blocked by AF-1**.

---

## AF-3 — Validate editor overrides against the action contract

**User story:** As a developer, I want invalid editor overrides rejected so the
submitted field contract cannot drift.

**Required task:**
- Add `ActionFormBlock.clean()` validation:
  - unique editor names;
  - editor names exist in config when config fields are present;
  - editor block type compatible with config type;
  - config `name`, `type` and `required` authoritative.
- Surface clear validation messages in the admin.

**Acceptance criteria:**
- [ ] Unknown, duplicate, unnamed and type-mismatched fields fail validation.
- [ ] Valid partial overrides save.
- [ ] Config-only and editor-only forms save.
- [ ] Tests cover every validation branch.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `tests/dynamic/test_action_blocks.py`
- `docs/data-components.md`

**Blocking stories:** AF-1, AF-2.

**Current status:** Not started — **Blocked by AF-1, AF-2**.

---

## AF-4 — Checkbox/toggle helper text and overlap

**User story:** As an editor, I want helper text below checkbox/toggle labels by
default, with control over placement and design.

**Required task:**
- Add `helper_position` and optional helper typography design to
  `CheckboxBlock` and `ToggleBlock`.
- Introduce a shared helper-text partial.
- Use `label-text-alt`/`text-sm` rather than the `label` wrapper class.
- Ensure wrappers are `w-full` and label rows use `items-start`.
- Apply the same layout to preset action fields.

**Acceptance criteria:**
- [ ] Default helper text appears below the checkbox/toggle label.
- [ ] `above` and `inline` positions work.
- [ ] Helper design classes render.
- [ ] Multiple checkbox fields stack without overlap in an action form.
- [ ] Tests assert markup/classes for each position.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/inputs.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/checkbox.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/toggle.html`
- new shared helper-text template
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/action_form.html`
- `tests/blocks/test_feedback_input_blocks.py`
- `tests/dynamic/test_action_blocks.py`
- `docs/forms.md`

**Blocking stories:** none (preset rendering consumes it in AF-2).

**Current status:** Not started — **Ready**.

---

## AF-5 — Regression-test after-submit behaviours and uploads

**User story:** As a maintainer, I want confidence that action forms still work
with and without htmx, including file uploads and preset fields.

**Required task:**
- Add regression tests for inline, reload and navigate behaviours.
- Test plain POST fallback and messages.
- Test file upload/autocomplete fields in action forms.
- Test multiple action forms on one page/in tabs.

**Acceptance criteria:**
- [ ] Each behaviour is covered for htmx and non-htmx requests.
- [ ] File uploads reach the handler.
- [ ] Multiple forms do not cross-post or share status areas.
- [ ] Tests use the configured confirmation values.

**Expected file changes:**
- `tests/dynamic/test_action_blocks.py`
- `tests/dynamic/test_action_views.py` (new if needed)
- `docs/htmx.md`
- `docs/data-components.md`

**Blocking stories:** AF-2, AB-3.

**Current status:** Not started — **Blocked by AF-2, AB-3**.

---

# Epic 4 — Form field layout management

**Outcome:** admins can control the internal layout of every form field,
especially a single checkbox and a list of checkboxes. The implementation
reuses the existing layout and design primitives instead of adding a parallel
layout system.

## Design approach (SOLID / DRY / KISS / YAGNI)

- **Single responsibility:** a new `FieldLayoutBlock` describes placement only;
  existing `DesignBlock`/`SpacedDesignBlock` continue to describe the field
  container, typography, spacing, size and overflow. Templates render the
  resulting class strings.
- **DRY:** reuse `LayoutBlock` (row/column/grid, columns, wrap, justify, align,
  gap, responsive), `LayoutItemDesignBlock` (item width, margin, order,
  align-self, grid spans), `BlockSizeBlock` (size, min/max, overflow) and the
  existing `build_design_css` pipeline. Do not introduce a second layout
  vocabulary.
- **Open/closed:** one `FieldLayoutMixin` exposes part CSS and visibility flags
  to every input template. New field types adopt the mixin without changing the
  renderer.
- **KISS:** editors choose a high-level `placement` (`auto`, `start`, `middle`,
  `end`, `grid`) and visibility; advanced item/grid controls live in a collapsed
  “Advanced layout” group.
- **YAGNI:** do not add a new `CheckboxGroupBlock` initially. A `Fieldset`
  containing `Checkbox` blocks already represents a multiple-checkbox list;
  `RadioBlock` already represents an internal option list. Add a dedicated
  group block only if real editing feedback shows the fieldset is insufficient.
- **Accessibility:** “visually hidden” uses `sr-only` and remains focusable;
  “hidden” omits the part. If the input is visually hidden, the label remains
  clickable; if the label is hidden, the input needs an accessible name.

## FL-1 — Add shared field layout primitives

**User story:** As a maintainer, I want one reusable field-layout vocabulary so
every form field can arrange its parts consistently.

**Required task:**
- Add `FIELD_PART_PLACEMENT_CHOICES` (`auto`, `start`, `middle`, `end`, `grid`).
- Add `FieldPartLayoutBlock`:
  - `visibility`: shown / visually hidden / hidden;
  - `placement`;
  - `max_lines` for label/help text clamping;
  - advanced `item = LayoutItemDesignBlock(required=False)`.
- Add `FieldLayoutBlock`:
  - `layout = LayoutBlock()`;
  - `input`, `label`, `help`, `error = FieldPartLayoutBlock()`;
  - `options = FieldGroupLayoutBlock(required=False)` for grouped choices.
- Add `FieldGroupLayoutBlock`: `layout = LayoutBlock()` plus
  `size = BlockSizeBlock()` for spacing, scroll and clamp of a multi-option group.
- Add `FieldOptionLayoutBlock`: `input`/`label` part layouts for internal option
  lists (radio options).
- Add `FieldLayoutMixin` and pure builders in
  `base_blocks/field_layout.py`, using `build_design_css` and
  `build_layout_item_css`.
- Define defaults: row → input start, label middle, help end; column → label
  start, input middle, help end; grid → auto-placement with editor spans.

**Acceptance criteria:**
- [ ] A field can be row, column or grid.
- [ ] Each part can be shown, visually hidden, hidden, or placed start/middle/end.
- [ ] Grid placement supports column/row start and span plus justify/align self.
- [ ] `max_lines` emits `line-clamp-*` for label/help.
- [ ] Group layout and option layout emit row/column/grid, gap, alignment, size,
      overflow and scroll classes.
- [ ] Unit tests cover builders and default placement per layout.
- [ ] No new CSS framework or arbitrary style field is introduced.

**Expected file changes:**
- new `src/wagtail_daisIE/base_blocks/field_layout.py`
- `src/wagtail_daisIE/base_blocks/__init__.py`
- `src/wagtail_daisIE/base_blocks/layout_design.py` (grid start choices, if added there)
- `src/wagtail_daisIE/base_blocks/css.py`
- `src/wagtail_daisIE/choices/layout_item.py`
- tests for field-layout builders and layout-item CSS

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

## FL-2 — Add full layout control to a single Checkbox and Toggle

**User story:** As an editor, I want to place the checkbox input, its label and
its help text independently, so I can build row, column and grid checkbox
layouts without overlap.

**Required task:**
- Add `field_layout = FieldLayoutBlock(required=False)` to `CheckboxBlock` and
  `ToggleBlock`.
- Apply the shared `FieldLayoutMixin` context.
- Update `checkbox.html`/`toggle.html` to render input, label and help wrappers
  using the layout classes and visibility flags.
- Use `sr-only` for visually hidden input; keep the label clickable.
- If the label is hidden, expose/require an accessible label on the input.
- Reuse the AF-4 helper-text partial; helper text no longer uses `label` as its
  wrapper class.
- Add `field_layout` to the settings form layout under a “Field layout” group.

**Acceptance criteria:**
- [ ] Input at start/middle/end of a row works.
- [ ] Label at start/middle/end of a row works.
- [ ] Help text at start/middle/end of a row works.
- [ ] Column defaults put the label top, input middle, help bottom.
- [ ] Each part can be visually hidden or omitted.
- [ ] Grid layout honours column/row start, span, justify/align.
- [ ] Spacing, alignment, size, max lines and overflow/scroll are configurable
      via the existing layout/design controls.
- [ ] Multiple checkbox fields stack or grid without overlap.
- [ ] Accessibility tests cover hidden input/label combinations.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/inputs.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/checkbox.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/toggle.html`
- shared helper-text partial from AF-4
- `tests/blocks/test_feedback_input_blocks.py`
- `tests/dynamic/test_action_blocks.py`

**Blocking stories:** FL-1, AF-4.

**Current status:** Not started — **Blocked by FL-1, AF-4**.

---

## FL-3 — Add group and option layout for multiple checkboxes and radios

**User story:** As an editor, I want a list of checkboxes or radio options to be
a row, column or grid, with each option's input and label laid out predictably.

**Required task:**
- Add `group_layout = FieldGroupLayoutBlock(required=False)` to `FieldsetBlock`.
  Apply it to the wrapper around its child fields.
- Add `group_layout = FieldGroupLayoutBlock(required=False)` to `RadioBlock`.
- Add `option_layout = FieldOptionLayoutBlock(required=False)` to `RadioBlock`
  for each option's input/label.
- For multiple checkboxes, use a `Fieldset` with `group_layout`; each
  `CheckboxBlock` keeps its own `field_layout`.
- Add a collapsed “Choice layout” settings group to the fieldset and radio forms.
- Document that a fieldset is the standard multiple-checkbox group; do not add a
  new block type yet.

**Acceptance criteria:**
- [ ] A fieldset of checkboxes can render as row, column or grid.
- [ ] Each checkbox in the group retains its own input/label/help layout.
- [ ] Radio options can render as row, column or grid.
- [ ] Radio option input/label placement is configurable.
- [ ] Group spacing, wrapping, justify, align, gap, size and overflow render.
- [ ] Tests cover row/column/grid groups and option layouts.
- [ ] No new `CheckboxGroupBlock` is introduced.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/inputs.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/fieldset.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/radio.html`
- `tests/blocks/test_feedback_input_blocks.py`
- `docs/forms.md`

**Blocking stories:** FL-1, FL-2.

**Current status:** Not started — **Blocked by FL-1, FL-2**.

---

## FL-4 — Apply field layout to every block input

**User story:** As an editor, I want the same input/label/help layout controls on
every form field, not just checkboxes.

**Required task:**
- Add `field_layout` to `InputBlock`, `TextareaBlock`, `SelectBlock`,
  `RangeBlock`, `RatingBlock`, `FileInputBlock` and
  `AutocompleteSelectMultipleBlock`.
- Apply `FieldLayoutMixin` and update each template to use the shared part
  wrappers/classes.
- Keep existing `design`, colour and size presets working.
- Add `field_layout` to each settings form layout.

**Acceptance criteria:**
- [ ] Every input template uses the shared field-part context.
- [ ] Row/column/grid part placement works for each field type.
- [ ] Existing inputs render unchanged when `field_layout` is empty.
- [ ] File/autocomplete tray and item designs still work.
- [ ] Tests cover at least input, textarea, select, range and file.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/inputs.py`
- all `templates/wagtail_daisIE/blocks/inputs/*.html`
- `tests/blocks/test_feedback_input_blocks.py`
- `tests/blocks/test_input_widget_design.py`

**Blocking stories:** FL-1.

**Current status:** Not started — **Blocked by FL-1**.

---

## FL-5 — Add field layout to standard form pages

**User story:** As an admin, I want standard form-page fields to offer the same
layout control as action-form fields.

**Required task:**
- Add a `field_layout` StreamField to `DaisieFormField` using
  `FieldLayoutBlock` (model change + migration).
- Expose the computed part/group/option classes through `DaisieFormBuilder`
  and the field’s rendered attributes.
- Update `forms/form_field.html` and choice-field rendering to use the shared
  layout wrappers.
- Extend `ChoiceOptionsDesignBlock`/form-page choice handling to support
  group and option layout consistently with FL-3.
- Provide a migration and handover note.

**Acceptance criteria:**
- [ ] Form-page checkbox/radio fields support single-field and group layout.
- [ ] All form-page field types support part visibility/placement.
- [ ] Existing fields with no layout render unchanged.
- [ ] Migration is generated and `makemigrations --check` passes.
- [ ] Tests cover a checkbox, a radio group and a text input.

**Expected file changes:**
- `src/wagtail_daisIE/forms/fields.py`
- `src/wagtail_daisIE/forms/builder.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/forms/form_field.html`
- `src/wagtail_daisIE/forms/migrations/<new migration>.py`
- `tests/forms/test_form_pages.py`
- `docs/forms.md`

**Blocking stories:** FL-1, FL-3, FL-4.

**Current status:** Not started — **Blocked by FL-1, FL-3, FL-4**.

---

## FL-6 — Apply field layout to action forms and preset fields

**User story:** As an editor, I want action-form fields and developer-preset
fields to use the same layout controls as standard fields.

**Required task:**
- Add `fields_layout = FieldGroupLayoutBlock(required=False)` to
  `ActionFormBlock` for arranging the whole field list.
- Ensure preset fields rendered from action config use `FieldLayoutBlock`
  defaults and accept layout configuration.
- Allow a preset checkbox group (`type: checkbox_group` or equivalent) only if
  the Fieldset approach cannot represent it; otherwise render multiple preset
  checkboxes with group layout.
- Reuse the FL-2/FL-3 templates; do not create a parallel preset renderer.
- Add tests for preset checkbox fields in row/column/grid.

**Acceptance criteria:**
- [ ] Action-form fields can be stacked, rowed or gridded.
- [ ] Preset fields honour layout config/defaults.
- [ ] Multiple preset checkboxes do not overlap.
- [ ] Editor overrides keep layout/design control.
- [ ] No duplicate checkbox markup exists.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/action_blocks.py`
- `src/wagtail_daisIE/dynamic/actions.py`
- preset/action form templates
- `tests/dynamic/test_action_blocks.py`
- `docs/data-components.md`

**Blocking stories:** AF-2, FL-2, FL-3.

**Current status:** Not started — **Blocked by AF-2, FL-2, FL-3**.

---

# Epic 5 — Toggles and switches

**Outcome:** Toggle and Swap controls are documented and regression-tested for
form and visibility use.

## TS-1 — Audit Toggle/Swap visibility controls

**User story:** As a maintainer, I want explicit tests for switch scopes,
duplicate keys and default states.

**Required task:**
- Add tests for Toggle and Swap controllers controlling target blocks.
- Test default on/off states.
- Test key scope: page, feed item, calendar event, menu.
- Test duplicate key rejection.
- Test combination with context conditions.
- Add or update accessibility coverage for `role="switch"`.

**Acceptance criteria:**
- [ ] Toggle and Swap both control matching targets.
- [ ] Keys are scoped and case-sensitive.
- [ ] Duplicate keys fail validation.
- [ ] Context condition + switch combination behaves as documented.
- [ ] Tests cover the `:has()` fallback contract where practical.

**Expected file changes:**
- `tests/blocks/test_visibility.py` (new if absent)
- `tests/menus/test_menu_design.py`
- `tests/feeds/test_data_components.py`
- `docs/visibility.md`

**Blocking stories:** DI-1.

**Current status:** Not started — **Blocked by DI-1**.

---

## TS-2 — Toggle/Swap helper and design consistency

**User story:** As an editor, I want Toggle and Swap controls to have clear,
consistent labels, helper text and design options.

**Required task:**
- Verify Toggle helper text uses the AF-4 shared partial.
- Verify Swap on/off text and design render consistently.
- Add missing help text or labels in the block form layouts where unclear.
- Add tests for Toggle design/helper and Swap design.

**Acceptance criteria:**
- [ ] Toggle form field and visibility-control use are documented in help text.
- [ ] Swap on/off text and logic key/state are covered by tests.
- [ ] Design classes/styles render on both controls.
- [ ] No duplicate helper-text markup remains.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/inputs.py`
- `src/wagtail_daisIE/blocks/layout_components.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/inputs/toggle.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/layout/swap.html`
- `tests/blocks/test_feedback_input_blocks.py`
- `docs/visibility.md`

**Blocking stories:** AF-4, TS-1.

**Current status:** Not started — **Blocked by AF-4, TS-1**.

---

# Epic 6 — Editor guide amendments

**Outcome:** every complex component has a dedicated guide page with a how-to
for every supported use case.

## HG-1 — Add the Action buttons guide page

**User story:** As an editor, I want a complete guide to action buttons,
including dialogs, alerts and clickable cards.

**Required task:**
- Create `help/pages/action-buttons.html`.
- Add the page to `GUIDE_SECTIONS`.
- Cover every use case listed in the refined plan.

**Acceptance criteria:**
- [ ] Page renders in the admin guide.
- [ ] Covers: dev setup, basic action, target expression, button design,
      icon-only, dialog, post-submit alert, both, no confirmation, clickable card,
      menus/feeds/calendars, audience/visibility, troubleshooting.
- [ ] Cross-links to Action forms and Accessibility.

**Expected file changes:**
- `src/wagtail_daisIE/help.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/action-buttons.html`
- `tests/core/test_help.py`

**Blocking stories:** DI-5, AB-1, AB-2, AB-3, AB-4.

**Current status:** Not started — **Blocked by DI-5, AB-1, AB-2, AB-3, AB-4**.

---

## HG-2 — Add the Action forms guide page

**User story:** As an editor, I want a complete guide to action forms, preset
fields, overrides and submission behaviours.

**Required task:**
- Create `help/pages/action-forms.html`.
- Cover editor fields, config presets, overrides, optional fields, form/field
  design, single and multiple checkbox layout, dialog/alert, behaviours, tabs,
  uploads and troubleshooting.
- Link to `form-field-layout` for detailed input/label/help placement.

**Acceptance criteria:**
- [ ] Page renders in the admin guide.
- [ ] Covers every use case listed in the refined plan.
- [ ] Includes a “Form page vs Action form” comparison and cross-links.
- [ ] Mentions htmx enhancement and no-JS fallback.

**Expected file changes:**
- `src/wagtail_daisIE/help.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/action-forms.html`
- `tests/core/test_help.py`

**Blocking stories:** DI-6, AB-1, AB-3, AF-1, AF-2, AF-3, AF-4, AF-5, FL-6.

**Current status:** Not started — **Blocked by the action-form and field-layout implementation stories**.

---

## HG-3 — Add the Toggles guide page

**User story:** As an editor, I want to know when to use a Toggle as a form
field and when to use it as a visibility controller.

**Required task:**
- Create `help/pages/toggles.html`.
- Cover form-field use, visibility control, default state, logic key/label,
  scope, design, helper text, accessibility and troubleshooting.
- Link to `form-field-layout` for Toggle input/label/help placement.
- Cross-link to Switches and Forms/Action forms.

**Acceptance criteria:**
- [ ] Page renders in the admin guide.
- [ ] Clearly distinguishes Toggle vs Checkbox vs Swap.
- [ ] Includes examples for form field and visibility control.
- [ ] Covers scope and duplicate-key rules.

**Expected file changes:**
- `src/wagtail_daisIE/help.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/toggles.html`
- `tests/core/test_help.py`

**Blocking stories:** AF-4, FL-2, TS-1, TS-2.

**Current status:** Not started — **Blocked by AF-4, FL-2, TS-1, TS-2**.

---

## HG-4 — Add the Switches guide page

**User story:** As an editor, I want to understand Swap blocks and the
visibility-switch system.

**Required task:**
- Create `help/pages/switches.html`.
- Cover Swap block use cases, visibility targets, multiple targets, scope,
  context-condition combination, browser fallback and accessibility.
- Cross-link to Toggles.

**Acceptance criteria:**
- [ ] Page renders in the admin guide.
- [ ] Explains Toggle and Swap as switch controllers.
- [ ] Covers target setup with Control key/Show when on/off.
- [ ] Covers no-`:has()` fallback and accessibility.

**Expected file changes:**
- `src/wagtail_daisIE/help.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/switches.html`
- `tests/core/test_help.py`

**Blocking stories:** TS-1, TS-2.

**Current status:** Not started — **Blocked by TS-1, TS-2**.

---

## HG-5 — Rewrite the overview and cross-link existing pages

**User story:** As an editor, I want the existing buttons/inputs/forms/menus
pages to point me to the detailed component guides.

**Required task:**
- Rewrite `buttons-and-actions.html` as an overview with links to Action button
  and Action form pages.
- Update `feedback-and-input-blocks.html` to link Toggle/Checkbox and
  Form field layout guidance.
- Update `forms.html` with “Form page vs Action form” and field-layout links.
- Update `menus.html` with action button and icon-only link guidance.
- Update `accessibility.html` with icon-only, hidden input/label and switch guidance.

**Acceptance criteria:**
- [ ] No duplicated full how-to content; overview links to the dedicated pages.
- [ ] Every cross-link resolves.
- [ ] Terminology matches the new pages.

**Expected file changes:**
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/buttons-and-actions.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/feedback-and-input-blocks.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/forms.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/menus.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/accessibility.html`

**Blocking stories:** HG-1, HG-2, HG-3, HG-4, HG-7.

**Current status:** Not started — **Blocked by HG-1..HG-4, HG-7**.

---

## HG-6 — Update block reference mappings and guide tests

**User story:** As an editor, I want the block reference to point complex blocks
to their dedicated how-to pages.

**Required task:**
- Add `BLOCK_HOWTO` overrides for:
  - `action` → `action-buttons`
  - `action_form` → `action-forms`
  - `toggle` → `toggles`
  - `swap` → `switches`
  - `checkbox` → `form-field-layout`
  - `radio` → `form-field-layout`
  - `fieldset` → `form-field-layout`
- Update `build_block_reference` to prefer block-level mappings.
- Add guide tests for valid mappings and page templates.

**Acceptance criteria:**
- [ ] Block reference links to the correct dedicated page.
- [ ] Every guide slug has a template file.
- [ ] Every group/block how-to target resolves to a guide slug.
- [ ] New pages are covered by `test_every_guide_page_renders`.

**Expected file changes:**
- `src/wagtail_daisIE/help_reference.py`
- `tests/core/test_help.py`

**Blocking stories:** HG-1, HG-2, HG-3, HG-4, HG-7.

**Current status:** Not started — **Blocked by HG-1..HG-4, HG-7**.

---

## HG-7 — Add the Form field layout guide page

**User story:** As an editor, I want one place that explains how to lay out a
single checkbox, a group of checkboxes, radio options and any other field.

**Required task:**
- Create `help/pages/form-field-layout.html`.
- Add it under How-to and link it from Action forms, Toggles and Feedback and
  inputs.
- Cover:
  - single-field parts: input, label, help, error;
  - shown / visually hidden / hidden;
  - row, column and grid placement;
  - default row and column arrangements;
  - multiple checkboxes in a Fieldset;
  - radio option layout;
  - spacing, alignment, size, max lines and overflow/scroll;
  - action-form fields, preset fields and standard form-page fields;
  - accessibility warnings for hidden input/label combinations;
  - troubleshooting overlap and grid placement.
- Add screenshots or diagrams only if the guide already uses them; otherwise
  use tables and step lists.

**Acceptance criteria:**
- [ ] Page renders in the admin guide.
- [ ] Covers every use case from the checkbox/multiple-checkbox brief.
- [ ] Clearly explains Fieldset as the multiple-checkbox group and when to use
      Radio instead.
- [ ] Cross-links to Action forms, Toggles and Forms.
- [ ] Includes a “row with input start, label end, help below” example and a
      “column with label top, input middle, help bottom” example.

**Expected file changes:**
- `src/wagtail_daisIE/help.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/form-field-layout.html`
- `tests/core/test_help.py`

**Blocking stories:** FL-2, FL-3, FL-4, FL-5, FL-6.

**Current status:** Not started — **Blocked by FL-2..FL-6**.

---

## HG-8 — Update repository documentation

**User story:** As a developer, I want the repository docs to match the new
component behaviour and guide pages.

**Required task:**
- Update:
  - `docs/data-components.md` — action buttons/forms, confirmations, presets.
  - `docs/htmx.md` — post-action alert/fallback behaviour.
  - `docs/forms.md` — form page vs action form, helper text, field layout.
  - `docs/visibility.md` — Toggle/Swap controls and scopes.
  - `docs/menus.md` — branding, LinkList design, unified triggers.
  - `docs/design-system.md` and `docs/architecture.md` — inheritance and field-layout model.
  - `AGENTS.md` — invariants if needed.
- Ensure help guide and repository docs do not contradict each other.

**Acceptance criteria:**
- [ ] Docs describe only implemented behaviour.
- [ ] No stale inheritance/cascade claims remain.
- [ ] Cross-links between help guide and docs are correct where applicable.

**Expected file changes:**
- The documentation files listed above.

**Blocking stories:** all implementation stories that change behaviour.

**Current status:** Not started — **Blocked by implementation**.

---

# Epic 7 — Tab-safe layout capability

**Outcome:** Admins can compose page-grade layout inside a tab panel — full rows, columns and grids, layout items, and feeds/actions with precise sizing — while the static block graph guarantees a full `TabsBlock` can never appear below another `TabsBlock`.

## TAB-1 — Add tab-safe layout components and expand tab content

**User story:** As an editor, I want full row/column/grid layout and layout-item precision inside a tab panel, so I can place content, feeds and actions exactly where I need them.

**Required task:**
- Add `TabLayoutStreamBlock`, `TabLayoutContainerContentStreamBlock` and `TabContentStreamBlock` palette wiring.
- Add `TabLayoutItemBlock`, `TabRowBlock`, `TabColumnBlock` and `TabGridBlock` as tab-safe variants of the existing layout blocks.
- Add `_tab_layout`, `_tab_layout_container_content` and `_tab_content` palette builders.
- Make `TabContentStreamBlock` use the `tab_content` palette.
- Keep every key currently available in tab content; the new palette must be a superset of the existing `layout` palette.
- Map the new palette keys to the tab-safe classes:
  - `layout_item` → `TabLayoutItemBlock`
  - `row` → `TabRowBlock`
  - `column` → `TabColumnBlock`
  - `grid` → `TabGridBlock`
- Keep `feed`, `action`, `action_form`, `autocomplete` and `tabs_inline` available.
- Do not add full `card`, `list`, `stack`, `aura`, `indicator`, `drawer` or `hero` variants in this story.
- Ensure the existing `row.html`, `column.html`, `grid.html` and `layout_item.html` templates work with the tab-safe block types.

**Acceptance criteria:**
- [ ] Every existing tab content key remains selectable.
- [ ] Full `row`, `column`, `grid` and `layout_item` are selectable inside a tab.
- [ ] A feed or action can be placed inside a `TabLayoutItemBlock` and inside a tab row/column/grid with precision.
- [ ] `layout_item` design controls work inside tab layouts, including grid spans in a tab grid.
- [ ] Tab row/column/grid use the dedicated tab-safe classes, not the generic full layout classes.
- [ ] `tabs_inline` remains available; full `tabs` is not added.
- [ ] No migration is generated by the palette or new block classes.
- [ ] Rendering tests cover a tab containing a full row with a layout item, plus a feed or action placement.
- [ ] `just lint` and `just test` pass.

**Expected file changes:**
- `src/wagtail_daisIE/blocks/layout.py`
- `src/wagtail_daisIE/blocks/stream.py`
- `src/wagtail_daisIE/blocks/palettes.py`
- new/updated `tests/blocks/test_tabs.py`
- `tests/core/test_compact_blocks.py`

**Blocking stories:** none.

**Current status:** Ready.

---

## TAB-2 — Guard and document the no-nested-full-tabs invariant

**User story:** As a maintainer, I want an automated guard so a future palette change cannot make a full `TabsBlock` a descendant of another `TabsBlock`.

**Required task:**
- Add a palette guard that rejects a direct full `tabs` entry in the tab palette graph.
- Add a recursive test that walks the tab palettes and every reachable child block, asserting that no exact `TabsBlock` instance is reachable.
- Explicitly allow `TabsInlineBlock` (`tabs_inline`) as the safe nested-tab option.
- Document the dedicated tab-safe layout family and the invariant.
- Update the editor help page for Tabs with the new composition options.

**Acceptance criteria:**
- [ ] The recursive guard fails if a full `TabsBlock` is injected into any tab palette or tab-safe layout component.
- [ ] `TabsInlineBlock` remains reachable and allowed.
- [ ] The test covers `TabContentStreamBlock`, `TabLayoutItemBlock`, `TabRowBlock`, `TabColumnBlock` and `TabGridBlock`.
- [ ] Docs explain that tab content uses tab-safe layout variants and that full `TabsBlock` must never be added to them.
- [ ] `docs/block-palettes.md`, `docs/architecture.md`, `docs/extending.md`, `AGENTS.md` and the Tabs help page match the implemented behaviour.
- [ ] `just lint` and `just test` pass.

**Expected file changes:**
- `tests/blocks/test_tabs.py`
- `src/wagtail_daisIE/blocks/palettes.py` (guard, if not added in TAB-1)
- `docs/block-palettes.md`
- `docs/architecture.md`
- `docs/extending.md`
- `AGENTS.md`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/layout-blocks.html`

**Blocking stories:** TAB-1.

**Current status:** Blocked by TAB-1.

---

# Epic 8 — Feed display titles

**Outcome:** Feeds have a friendly CMS display title separate from their unique internal name, so admins no longer have to use slug-like names for display.

## FT-1 — Add a separate feed display title

**User story:** As an admin, I want a friendly display title for a feed, so the CMS and snippet chooser show a human-readable name without forcing me to use a slug-like internal name.

**Required task:**
- Add `title` to `Feed` as a non-unique, optional display field.
- Keep `name` as the required unique internal identifier.
- Make `Feed.__str__` return `self.title or self.name`.
- Show `title` and `name` in the feed snippet list.
- Add both `title` and `name` to the feed snippet search fields.
- Put the `title` panel first and label `name` as the internal name.
- Seed demo feeds with a title.
- Add a migration for the new field.
- Update the feed documentation and help page.

**Acceptance criteria:**
- [ ] `title` is optional and not unique; `name` remains required and unique.
- [ ] `__str__` returns the title when set and falls back to the internal name when blank.
- [ ] Existing feeds with no title still display and can be selected.
- [ ] The snippet list and chooser show the display title.
- [ ] Searching by title or internal name works.
- [ ] The migration applies cleanly and `makemigrations --check --noinput` passes.
- [ ] Tests cover title display, fallback and duplicate titles.
- [ ] `docs/data-components.md`, the Feeds help page and the README data-components section describe both fields.
- [ ] `just lint` and `just test` pass.

**Expected file changes:**
- `src/wagtail_daisIE/feeds/models.py`
- `src/wagtail_daisIE/feeds/view_sets.py`
- `src/wagtail_daisIE/feeds/migrations/<new migration>.py`
- `demo/blog/management/commands/load_initial_data.py`
- `tests/feeds/test_data_components.py`
- `docs/data-components.md`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/feeds.html`
- `README.md`

**Blocking stories:** none.

**Current status:** Ready.

---

# Epic 9 — Link-destination audience redirects

**Outcome:** Audience-denied pages can redirect to the same destination types as buttons — page, URL/path, dynamic URL, document, email or phone — and the legacy page-only field is cleanly removed.

## AR-1 — Add link destination support for audience redirects

**User story:** As an admin, I want to choose any link destination for an audience-denied redirect, so the behaviour matches the destinations I can configure on buttons.

**Required task:**
- Add `audience_denied_destination` to `StyledPageMixin` as a `StreamField` using `LinkDestinationBlock` directly as the top-level block.
- Change the denial choice label from “Redirect to a page” to “Redirect to a link”.
- Add `get_audience_denied_url(request)` using `link_url()` with request/page context and `get_daisie_context()` when available.
- Keep a temporary fallback to `audience_denied_page` until AR-2 removes the legacy field.
- Update `audience_denied_response()` to redirect when the destination resolves and otherwise fall back to the 403 page; `404` behaviour is unchanged.
- Generate the `AddField` migrations for `demo/home` and `demo/blog` via handover.

**Acceptance criteria:**
- [ ] A page destination redirects to the page URL.
- [ ] An external URL or absolute path redirects correctly.
- [ ] A dynamic URL resolves using the page’s Daisie context.
- [ ] Document, email and phone destinations redirect correctly.
- [ ] An empty or unresolvable destination falls back to the 403 page.
- [ ] The 404 behaviour is unchanged.
- [ ] Existing page-only redirects still work through the temporary legacy fallback.
- [ ] Tests cover every destination type, dynamic context and fallback.
- [ ] The `AddField` migrations are generated and applied cleanly.
- [ ] `just lint` and `just test` pass.

**Expected file changes:**
- `src/wagtail_daisIE/pages.py`
- `src/wagtail_daisIE/base_blocks/audience.py`
- `tests/core/test_page_audience.py`
- `demo/home/migrations/<add field>.py`
- `demo/blog/migrations/<add field>.py`

**Blocking stories:** none.

**Current status:** Ready.

---

## AR-2 — Migrate page redirects and remove the legacy field

**User story:** As a maintainer, I want existing page redirects preserved while the page-only field is removed, so the final model has one link destination field and no deprecated fallback.

**Required task:**
- Add per-app data migrations in `demo/home` and `demo/blog` that copy every non-null `audience_denied_page_id` into `audience_denied_destination` as:
  ```python
  [{"type": "link_page", "value": page.audience_denied_page_id}]
  ```
- Implement a best-effort reverse migration that copies a `link_page` destination back to `audience_denied_page`.
- Document that non-page destinations cannot be represented in the old field and are therefore irreversible on reverse.
- Remove `audience_denied_page` from `StyledPageMixin`, its panels and `PageAudienceMixin`.
- Remove the temporary legacy fallback from `get_audience_denied_url`.
- Generate the `RemoveField` migrations after the data migrations.
- Update page audience tests to remove legacy-fallback coverage.
- Update the audience and error-page docs to describe the new field and clean removal.
- Add the consumer upgrade recipe: add field → data migration → remove field, with the copy-paste data migration snippet.

**Acceptance criteria:**
- [ ] Demo data migrations copy existing page redirects into the new stream shape.
- [ ] The reverse migration restores page destinations; non-page values are documented as irreversible.
- [ ] Migration order is `AddField` → data migration → `RemoveField` in each app.
- [ ] `audience_denied_page` no longer exists on the model, in the admin, or in runtime code.
- [ ] No legacy fallback remains.
- [ ] `makemigrations --check --noinput` passes.
- [ ] Tests use only the new field and cover the raw stream shape used by the data migration.
- [ ] Page audience, form page and detail page redirect paths are covered.
- [ ] The consumer upgrade recipe is documented and linked from the audience/error-page docs and README.
- [ ] `just lint` and `just test` pass.

**Expected file changes:**
- `src/wagtail_daisIE/pages.py`
- `src/wagtail_daisIE/base_blocks/audience.py`
- `demo/home/migrations/<data migration>.py`
- `demo/home/migrations/<remove field>.py`
- `demo/blog/migrations/<data migration>.py`
- `demo/blog/migrations/<remove field>.py`
- `tests/core/test_page_audience.py`
- `docs/error-pages.md`
- `docs/context-models.md`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/audiences.html`
- `README.md`

**Blocking stories:** AR-1, plus explicit approval for the hand-written data migrations required by `AGENTS.md` §7.

**Current status:** Blocked by AR-1 and migration-exception approval.


---

# Epic 10 — Context model admin performance

**Outcome:** context-model metadata and search have one scoped implementation;
saved bindings render with zero background requests; and model-field selection
no longer renders one control per configured model.

## UI-1 — Centralise context-model querysets and bounded search

**User story:** As a maintainer, I want one scoped queryset/search path for
context models, so the binding UI and feeds cannot drift in filtering, eager
loading or safe search fields.

**Required task:**
- Add a shared `dynamic/querysets.py` with:
  - `base_queryset(config, request=None, page=None)`, applying the configured
    `queryset`, `select_related` and `prefetch_related`.
  - `search_queryset(queryset, config, query, limit)`, using configured
    `search_fields`.
- Add optional `search_fields` to `WAGTAIL_DAISIE_CONTEXT_MODELS` and
  `ContextModel`; support a string or iterable.
- Define a safe fallback set (`title`, `name`, `slug`, `label`) that only uses
  fields present on the model; never search password-like fields.
- Replace the duplicated `base_queryset` implementations in
  `dynamic/feeds.py` and `dynamic/resolvers.py` with the shared helper.
- Replace the broad `TypeError` fallback for callable querysets with signature
  inspection.
- Replace blanket exception swallowing in filter/search resolution with
  specific exceptions and structured warnings.

**Acceptance criteria:**
- [ ] Feed queries and binding search both honour the configured queryset,
      `select_related` and `prefetch_related`.
- [ ] A callable queryset works with `(request, page)` and with no arguments.
- [ ] Search uses configured fields; fallback fields are only used when
      present; password-like fields are never searched.
- [ ] Invalid filter/search configuration is logged without hiding
      programming errors.
- [ ] No database access occurs at import time.
- [ ] Regression tests cover scoping, eager loading, fallback fields and
      callable signatures.

**Expected file changes:**
- new `src/wagtail_daisIE/dynamic/querysets.py`
- `src/wagtail_daisIE/dynamic/registry.py`
- `src/wagtail_daisIE/dynamic/resolvers.py`
- `src/wagtail_daisIE/dynamic/feeds.py`
- `src/wagtail_daisIE/dynamic/views.py`
- `tests/dynamic/test_dynamic_context_models.py`
- `tests/feeds/test_data_components.py`
- `docs/context-models.md`

**Blocking stories:** none.

**Current status:** Not started — **Ready**.

---

## UI-2 — Cache context-model metadata and split runtime/help state

**User story:** As an admin, I want context-model help and block metadata to be
built once and sent only where needed, so every admin page does not rebuild
field documentation it will not use.

**Required task:**
- Cache `field_docs`, `form_fields`, `help_fields` and `examples` on
  `ContextModel`; invalidate them through `reset_context_models()`.
- Split `get_context_models_state()` into:
  - runtime state used by `block_controllers.js`: keys, labels, model paths,
    modes and `fields`;
  - help state: `helpFields`, `examples` and source summaries, used only by the
    binding form and panels.
- Inject only runtime state through `register_context_models_js`.
- Update `FeedContextModelHelpPanel` and `FormModelFieldsHelpPanel` to use the
  cached help state and render full field/example detail only for the active
  model.
- Limit help examples to 4–6 per model.

**Acceptance criteria:**
- [ ] Building runtime state performs no database queries.
- [ ] The global admin script contains runtime fields only, not full help
      tables/examples.
- [ ] `reset_context_models()` invalidates every metadata cache.
- [ ] Feed and form help panels still show the active model’s fields/examples.
- [ ] Inactive model help does not render large hidden tables.
- [ ] Tests cover cache invalidation, query-free metadata and the split payload.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/registry.py`
- `src/wagtail_daisIE/dynamic/panels.py`
- `src/wagtail_daisIE/forms/panels.py`
- `src/wagtail_daisIE/wagtail_hooks.py`
- `tests/dynamic/test_dynamic_context_models.py`
- `tests/feeds/test_data_components.py`

**Blocking stories:** UI-1.

**Current status:** Not started — **Blocked by UI-1**.

---

## UI-3 — Render saved context bindings with zero background requests

**User story:** As an editor, I want a saved binding to show its selected
instance immediately when I open the editor, without the page firing a request
for every configured model.

**Required task:**
- Add a custom `ContextBindingValueBlock`/widget and telepath adapter whose
  form state is `{id, title, edit_url}`.
- Override `ContextBindingBlock.get_form_state()` to resolve the saved instance
  through the shared queryset helper and supply that state.
- Render the saved title/edit link server-side through the widget; use a small
  JS widget class for initial state, `setState`, `getValue` and `getState`.
- Remove `load@window->w-swap#submitLazy` from all binding forms.
- Keep the inline search forms for changing the value; update the display and
  hidden value when a result is clicked.
- Clear the stale value/display when the context-model `key` changes.
- Render a safe “missing” state when the saved object no longer exists or is
  outside the configured queryset.
- Cache resolved labels per request by `(model, pk)` if several bindings are
  present.

**Acceptance criteria:**
- [ ] Opening an edit page with saved bindings makes zero binding XHRs.
- [ ] The saved title/edit link renders on initial load.
- [ ] A newly added binding renders blank.
- [ ] Changing the model clears the previous model’s selection.
- [ ] A deleted or out-of-scope instance renders safely and fails validation on
      save.
- [ ] No `load@window` binding action remains in the form template.
- [ ] Tests cover saved, new, deleted and out-of-scope values plus key changes.
- [ ] Telepath/StreamField tests cover newly added blocks.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/blocks.py`
- new `src/wagtail_daisIE/dynamic/widgets.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/admin/context_binding_form.html`
- new widget JS under `src/wagtail_daisIE/static/wagtail_daisIE/js/`
- `tests/dynamic/test_dynamic_context_models.py`
- `tests/core/test_widgets.py`

**Blocking stories:** UI-1, UI-2.

**Current status:** Not started — **Blocked by UI-1, UI-2**.

---

## UI-4 — Harden and bound inline binding search

**User story:** As an editor, I want binding search to be fast, scoped and
permission-safe, without unnecessary display/current round-trips.

**Required task:**
- Reduce `binding_results` to the search path; remove `selected` and `current`
  display modes if the zero-XHR widget makes them unused.
- Protect the endpoint with `require_admin_access`.
- Use the shared queryset/search helper; apply configured `search_fields`,
  `select_related` and `prefetch_related`.
- Require at least 2 characters and cap results at 20 (hard maximum 50).
- Increase the client wait value to ~250 ms.
- Remove the `current` hidden input and display-sync glue no longer needed.
- Ensure invalid selectors and unknown/out-of-scope instances are rejected or
  return an empty response without a 500.

**Acceptance criteria:**
- [ ] Staff without admin access cannot query the endpoint.
- [ ] One-character searches make no database query.
- [ ] Results are capped and scoped to the configured queryset.
- [ ] Search is debounced at ~250 ms.
- [ ] Removed display modes have no orphaned template/JS code.
- [ ] Tests cover permission, scoping, minimum length, cap, invalid selectors
      and deleted instances.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/views.py`
- `src/wagtail_daisIE/dynamic/blocks.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/admin/context_binding_form.html`
- `src/wagtail_daisIE/templates/wagtail_daisIE/admin/binding_results.html`
- `tests/dynamic/test_dynamic_context_models.py`

**Blocking stories:** UI-1, UI-3.

**Current status:** Not started — **Blocked by UI-1, UI-3**.

---

## UI-5 — Optimise `ModelFieldSelect`

**User story:** As a form-page editor, I want the model-field selector to show
one useful control, not one hidden select per configured model.

**Required task:**
- Render one `<select>` server-side for the active model.
- Add a small JS controller that repopulates it from the cached runtime state
  when `instance_model` changes.
- Preserve the current value when it exists in the new model’s fields;
  otherwise reset to the empty option.
- Reuse `config.form_fields()` from the metadata cache.
- Remove per-model hidden/disabled selects and the per-select `w-rules` wiring.
- Document that without JS only the active model’s fields are selectable; the
  control still submits a real field name.

**Acceptance criteria:**
- [ ] One select is rendered per form field input, not one per model.
- [ ] The active model’s options match `form_fields()`.
- [ ] Changing the model repopulates options and preserves a valid value.
- [ ] The runtime payload is reused; no new endpoint is added.
- [ ] Tests cover active options, model changes, value preservation and the
      absence of per-model duplicate selects.

**Expected file changes:**
- `src/wagtail_daisIE/forms/fields.py`
- new `src/wagtail_daisIE/static/wagtail_daisIE/js/model_field_select.js`
- `tests/forms/test_form_pages.py`
- `docs/forms.md`

**Blocking stories:** UI-2.

**Current status:** Not started — **Blocked by UI-2**.

---

# Epic 11 — Feed rendering and filtering performance

**Outcome:** feeds use a standard Paginator/Page model, Load More appends only
new items, large choice sets are bounded, and filter parsing is maintained by
`django-filter` instead of bespoke code.

## FD-1 — Use Paginator pages and append-only Load More

**User story:** As a visitor, I want Load More to append the next page while the
feed keeps a normal page/previous/next model, so earlier items are not
re-rendered.

**Required task:**
- Use `Paginator`/`Page` as the feed loader.
- Implement `CountlessPaginator` by default:
  - fetch `page_size + 1` rows;
  - derive `has_next` from the extra row;
  - return a `Page` subclass without calling `count`/`num_pages`.
- Fall back to stock `Paginator` only if the subclass is rejected; in that case
  record the one-count-per-request behaviour in the story evidence.
- Replace `limit`/`offset` rendering with `?page=N`.
- Keep `limit`/`offset` as deprecated aliases for one release.
- Load More requests `page.next_page_number()`, appends only new items to the
  items container, and updates next/previous controls out-of-band.
- Hide the previous control in the Load More UI while keeping a real previous
  link in the DOM for no-JS.
- Reset to page 1 on filter/layout changes.
- Define the `total` policy: no total under `CountlessPaginator`; stock
  `Paginator` may retain `data-daisie-feed-total`. Document the chosen policy.

**Acceptance criteria:**
- [ ] Initial page and next page use the Paginator/Page API.
- [ ] Load More appends only new items; previous items are not re-rendered.
- [ ] Previous is hidden by the UI but available without JS.
- [ ] Filter/layout changes reset to page 1.
- [ ] `CountlessPaginator` makes no count query; stock fallback makes exactly
      one count query per request, recorded in tests.
- [ ] Invalid, empty and huge page values are handled safely.
- [ ] No duplicate items appear after repeated Load More requests.
- [ ] Legacy `limit`/`offset` aliases are tested or removed with a documented
      breaking change.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/feeds.py`
- `src/wagtail_daisIE/dynamic/views.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/feed_body.html`
- new page/fragment template under
  `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/`
- `tests/feeds/test_data_components.py`
- `docs/data-components.md`

**Blocking stories:** UI-1.

**Current status:** Not started — **Blocked by UI-1**.

---

## FD-2 — Bound filter choices and deduplicate filter work

**User story:** As a visitor, I want filter controls to stay responsive even
when a feed has large choice lists, without repeated resolution work.

**Required task:**
- Add optional `choice_limit` per filter: default 100; autocomplete default 20.
- Always include currently selected values even when outside the first limit.
- For long autocomplete lists, add remote search to the existing autocomplete
  controller rather than rendering every option twice.
- Resolve each filter’s choices once per request; pass the result to both
  `resolve_order()` and `build_filters()`.
- Compute the filter menu, submit CSS, layout CSS and filter panel CSS once in
  `render_feed()`.
- Remove duplicate `build_filter_menu()`/`build_design_css()` calls.

**Acceptance criteria:**
- [ ] Choice rendering is bounded by `choice_limit`.
- [ ] Selected values are always present and labelled.
- [ ] Long autocomplete filters search remotely instead of rendering all
      options.
- [ ] Sort choices are resolved once per request.
- [ ] Filter menu/CSS work is computed once.
- [ ] Tests cover caps, selected-value inclusion, large autocomplete lists and
      duplicate-resolution regressions.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/feeds.py`
- `src/wagtail_daisIE/dynamic/views.py`
- `src/wagtail_daisIE/templates/wagtail_daisIE/blocks/data/feed_filter.html`
- `src/wagtail_daisIE/static/wagtail_daisIE/js/daisyui_autocomplete.js`
- `tests/feeds/test_data_components.py`
- `docs/data-components.md`

**Blocking stories:** FD-1.

**Current status:** Not started — **Blocked by FD-1**.

---

## FD-3 — Adopt django-filter for standard feed filters

**User story:** As a maintainer, I want standard filter parsing and validation
maintained upstream, so this repository only owns the feed-specific UI and
configuration.

**Required task:**
- Add `django-filter>=26.2,<27` as a direct dependency and regenerate
  `uv.lock` through handover; do not hand-edit the lock file.
- Add `dynamic/filters.py` with a cached dynamic `FilterSet` per context-model
  filter set.
- Preserve current URL parameter names:
  - `filter_<key>` for choice, multi-choice, boolean and date;
  - `filter_<key>_from`/`_to` for date ranges;
  - `filter_<key>_min`/`_max` for numeric ranges;
  - `feed_search` for search;
  - custom `query` callables as `Filter.method` implementations.
- Keep `resolve_order()` for sort filters; do not add iommi’s
  Query/OrderingFilter.
- Build `build_filters()` from the same normalised filter definitions and bound
  form state; remove the manual `_apply_one` parser once parity is proven.
- Record the iommi comparison and the decision not to adopt it for feeds.
- Record the `django-listing` licence/fit rejection.

**Acceptance criteria:**
- [ ] All existing filter tests pass unchanged.
- [ ] Invalid values behave like the existing implementation.
- [ ] Custom `query` filters still work with `(queryset, params, key)`.
- [ ] Sort filters still work through `resolve_order()`.
- [ ] Query count does not increase relative to the manual parser.
- [ ] No new database migrations are generated.
- [ ] The dependency and lock update are applied through handover.
- [ ] Docs describe django-filter as the standard filter engine and iommi as
      assessed but not adopted.

**Expected file changes:**
- `pyproject.toml`
- `uv.lock` (handover only)
- new `src/wagtail_daisIE/dynamic/filters.py`
- `src/wagtail_daisIE/dynamic/feeds.py`
- `tests/feeds/test_data_components.py`
- `docs/data-components.md`
- `docs/architecture.md`

**Blocking stories:** UI-1, FD-2, plus dependency approval.

**Current status:** Not started — **Blocked by UI-1, FD-2 and dependency approval**.

---

## FD-4 — Prove feed query budgets and document package decisions

**User story:** As a maintainer, I want evidence that feed rendering is bounded
at each page load and that the build-vs-package decisions are recorded for
future work.

**Required task:**
- Add query-count tests for initial render, append requests and filter changes.
- Add an N+1 regression test with an item relation and the configured
  `select_related`/`prefetch_related`.
- Keep Feed editor help rendering to the active model and limit examples.
- Update `docs/data-components.md`, `docs/context-models.md`,
  `docs/architecture.md` and `README.md` for:
  - page-based feed URLs;
  - zero-XHR context bindings;
  - `search_fields` and `choice_limit`;
  - the Paginator/P2 decision;
  - `django-filter` adoption;
  - iommi and `django-listing` rejection reasons.
- Update the Feeds help page with the new Load More/previous behaviour.

**Acceptance criteria:**
- [ ] Append query count does not grow with already-loaded items.
- [ ] A tested feed item relation produces no N+1 queries.
- [ ] Feed editor help renders full detail only for the active model.
- [ ] Docs describe only implemented behaviour and all package decisions.
- [ ] Help guide links/pages render in the existing admin guide tests.
- [ ] No stale cumulative `limit`/`offset` claims remain.

**Expected file changes:**
- `src/wagtail_daisIE/dynamic/panels.py`
- `tests/feeds/test_data_components.py`
- `docs/data-components.md`
- `docs/context-models.md`
- `docs/architecture.md`
- `README.md`
- `src/wagtail_daisIE/templates/wagtail_daisIE/help/pages/feeds.html`

**Blocking stories:** FD-1, FD-3.

**Current status:** Not started — **Blocked by FD-1, FD-3**.

---

# Epic 12 — Verification

## V-1 — Full verification and handover

**User story:** As a maintainer, I want evidence that the whole change set is
safe.

**Required task:**
- Run the repository’s required verification through handover.
- Collect results and update story statuses.

**Acceptance criteria:**
- [ ] `just lint` passes.
- [ ] `just test` passes.
- [ ] `uv run ./demo/manage.py makemigrations --check --noinput` passes.
- [ ] `uv run ./demo/manage.py makemigrations --check --noinput` passes for the
      feed, home and blog apps.
- [ ] Any changed help guide page renders in the admin test.
- [ ] Final summary records what changed, risks and follow-ups.
- [ ] The tab-safe palette invariant test passes and no full `TabsBlock` is
      reachable below a `TabsBlock`.
- [ ] Feed title migration applies cleanly.
- [ ] Audience redirect data migrations preserve existing page destinations.
- [ ] The consumer upgrade recipe for the removed `audience_denied_page` field
      is present and accurate.
- [ ] Context bindings render saved selections with zero binding XHRs.
- [ ] `ModelFieldSelect` renders one select per field input, not one per model.
- [ ] Feed page/append tests show no duplicate items and the documented count
      policy.
- [ ] `django-filter` parity tests pass and the dependency/lock update is
      recorded.
- [ ] Package decision documentation covers Paginator/P2, django-filter, iommi
      and django-listing.

**Expected file changes:** none (verification only), unless fixes are required.

**Blocking stories:** DI-1..DI-7, AB-1..AB-4, AF-1..AF-5, FL-1..FL-6,
TS-1..TS-2, HG-1..HG-8, TAB-1, TAB-2, FT-1, AR-1, AR-2,
UI-1..UI-5, FD-1..FD-4.

**Current status:** Not started — **Blocked by all stories**.

---

## Summary dependency order

1. **DI-1** is the foundation for all inheritance and field-layout stories.
2. **AF-1 / AB-1 / FL-1** can start in parallel with DI-1.
3. **DI-2..DI-7** proceed once DI-1 is done.
4. **AB-2..AB-4** and **AF-2..AF-5** proceed after their bases.
5. **FL-2** follows FL-1 and AF-4; **FL-3** follows FL-2; **FL-4** follows FL-1;
   **FL-5** follows FL-1/FL-3/FL-4; **FL-6** follows AF-2/FL-2/FL-3.
6. **TS-1/TS-2** proceed after DI-1 and AF-4.
7. **HG-1..HG-4** are written only after the corresponding behaviour is final.
8. **HG-7** (field layout guide) follows FL-2..FL-6; **HG-5/HG-6** follow the
   guide pages; **HG-8** follows implementation.
9. **TAB-1**, **FT-1** and **AR-1** can start in parallel with the existing ready stories.
10. **TAB-2** follows **TAB-1**.
11. **AR-2** follows **AR-1** and the migration-exception approval.
12. **UI-1** is the shared query/search foundation; **UI-2** follows UI-1.
13. **UI-3** follows UI-1/UI-2; **UI-4** follows UI-1/UI-3;
    **UI-5** follows UI-2.
14. **FD-1** follows UI-1; **FD-2** follows FD-1; **FD-3** follows UI-1/FD-2;
    **FD-4** follows FD-1/FD-3.
15. **V-1** last.
