# Stimulus migration follow-up (admin widgets)

Wagtail recommends [Stimulus](https://stimulus.hotwired.dev/)
(`window.StimulusModule.Controller` registered via `window.wagtail.app.register`)
for client-side behaviour that must initialise on dynamically inserted nodes
(StreamField, `InlinePanel`, modals), and the
[Form widget client-side API](https://docs.wagtail.org/en/stable/reference/streamfield/widget_api.html)
(telepath) only for widgets whose value/state handling differs from the
built-ins.

The icon chooser, the image/audience/background-layer blocks and the alignment
widget have already been migrated (see `telepath.py`, `icon_chooser.js`,
`block_controllers.js`). The items below still hand-roll the telepath widget
render/state protocol and should be migrated next.

## 1. Colour swatch widget (`DaisyUISwatchWidget` / `DaisyUIRawSwatchWidget`)

- **Current:** `DaisyUISwatchWidgetAdapter` (`src/wagtail_daisIE/telepath.py`)
  plus `SwatchSelectDefinition` / `RadioTileWidget`
  (`static/wagtail_daisIE/js/block_settings.js`), and the non-telepath
  `initAllSwatches` fallback.
- **Why deferred:** the "Custom" tile is rendered value-less in the telepath
  template, so the stored custom value (`bg-[#rrggbb]`, or raw `#rrggbb` for
  `DaisyUIRawSwatchWidget`) has to be mapped back onto a radio after `setState`.
  The generic `RadioSelect` bound widget cannot do this — its empty-value
  `includes()` check would incorrectly select the custom radio. The Coloris
  single-picker lifecycle (one physical picker moved between containers) is also
  stateful.
- **Approach:**
  - Keep a minimal bound widget overriding `setState`/`getState` for the custom
    mapping (telepath is the documented "deeper integration" path), registered
    via a `WidgetAdapter` subclass.
  - Move the Coloris interaction into a Stimulus controller attached to the
    widget root via `build_attrs`/`data-controller`, loaded through the widget's
    `Media`.
  - Delete the `initAllSwatches` fallback from `block_settings.js`.
- **Tests:** extend `TestWidgetAdapters` in `tests/core/test_widgets.py` for the
  swatch constructor. No JS test harness exists; verify manually.
- **Risk:** high.

## 2. Preset slider (`DaisyUISliderWidget`)

- **Current:** `DaisyUISliderWidgetAdapter` (`telepath.py`) plus `SliderWidget` /
  `SliderSelectDefinition` (`block_settings.js`), and the `initAllSliders`
  fallback.
- **Why deferred:** the widget subclasses `django.forms.Select`. Switching to
  Wagtail's built-in `wagtail.widgets.Select` adapter changes `getState()`
  (returns an array) and `setState()` (substring `includes`) semantics, so block
  state round-trips need to be verified before the custom adapter can go.
- **Approach:**
  - Add a Stimulus controller for the range ↔ select sync and value label,
    attached via the widget `Media`.
  - Either keep a thin adapter for exact state mapping, or verify the built-in
    adapter is safe and remove the custom one.
- **Risk:** medium.

## 3. Numeric slider (`DaisyUINumberSliderWidget`)

- **Current:** `DaisyUINumberSliderWidgetAdapter` (`telepath.py`) plus
  `NumberSliderWidget` / `NumberSliderDefinition` (`block_settings.js`), and the
  `initAllNumberSliders` fallback.
- **Why deferred:** needs the range ↔ number ↔ label sync rewritten as a
  Stimulus controller; the generic `Widget` value handling is otherwise fine.
- **Approach:** Stimulus controller + widget `Media`; delete the adapter and the
  fallback.
- **Risk:** medium.

## 4. Plain-JS admin scripts → Stimulus

Global scripts that use `MutationObserver`/manual `initAll` and could become
Stimulus controllers attached via panel/widget `attrs`/`build_attrs`, allowing
their `insert_global_admin_js` hooks and observer fallbacks to be removed:

- `static/wagtail_daisIE/js/context_binding_block.js` — context binding block:
  field visibility, help panel and instance chooser. Largest of the three.
- ~~`static/wagtail_daisIE/js/forms_admin.js`~~ — done: the model-field selects
  and the "form field" block select now render server-side, and the remaining
  `instance_model` refresh is a Stimulus controller (loaded through the widget
  `Media`) with no observer or global state.
- `static/wagtail_daisIE/js/feed_help.js` — Feed model help panel.

- **Risk:** medium (context binding is the largest).

## 5. `block_settings.js` cleanup

Once the swatch/slider widgets above are migrated, delete `BaseDefinition`, the
bound widget classes and the `initAll*` fallbacks from `block_settings.js`,
leaving only (or removing) any telepath registrations still required.

## Not applicable

- `static/wagtail_daisIE/js/dynamic_data.js` (calendar) is loaded from a public
  block template, where Stimulus is not available.
- `static/wagtail_daisIE/js/theme_persistence.js` runs on the public site, not
  the admin.
