# Block visibility

Every themed content block has a **Visibility** settings panel with two
independent controls:

1. **Controlled by a switch** — a Toggle or Swap block controls matching
   targets with CSS only.
2. **Only show when the data matches** — a server-side condition evaluated
   against the current render context.

Both can be used together. The context condition is evaluated first; if it
fails, the block is not rendered at all. If it passes, the switch wrapper is
rendered and CSS decides whether it is visible.

## Switch controllers

Toggle and Swap blocks have a **Logic key** field. The key is validated with
Django's slug validator and must be unique within the rendered scope:

- page, detail page, form page, error page, allauth page: page-wide;
- feed item design: within that feed item;
- calendar event design: within that event;
- menu: within that menu.

Controllers have a friendly **Logic label** and a default state:

- Toggle: **On by default**;
- Swap: **On by default**.

Blocks that should react to a switch select the same **Control key** and choose
whether they appear when the switch is **on** or **off**.

Switch keys are case-sensitive. Missing keys keep the target hidden in browsers
that support `:has()`; browsers without `:has()` keep content visible as a
progressive-enhancement fallback.

## Toggle and Swap controls

`Toggle` and `Swap` are the switch controllers. Both expose a **Logic key**
and a default state.

### Toggle

A `Toggle` is a styled checkbox with `role="switch"`. It can be used in two
ways:

- as an ordinary form field, by setting **Field name**;
- as a visibility controller, by setting **Logic key**.

It has **Helper text** and **Helper design**, reused from the shared helper
partial, and **Field layout** like other data-input blocks. Its default state
is controlled by **On by default**.

When no logic key is set, the toggle renders only as a form field and emits no
switch CSS.

### Swap

A `Swap` swaps two pieces of content (`On` / `Off`) with a checkbox. It has
**On**, **Off**, **Effect**, **Logic key**, **On by default** and the usual
design controls. Its checkbox carries `role="switch"`.

When no logic key is set, the swap renders only as a visual toggle and emits no
switch CSS.

### Helper text and design

Toggle helper text uses the shared helper partial, so its markup and
`aria-describedby` link are consistent with checkboxes. `helper_design`
applies the same typography, spacing, border and background controls as other
input blocks.

Swap has no helper text; its on/off text is the visible control label. Design
classes and background styles render on the `swap` label.

### Keys and scopes

Logic keys must be valid slugs and are case-sensitive. Duplicate controller
keys within the same rendered scope are rejected when the page, menu, feed or
calendar is saved. A target may reference a key that is not present; it stays
hidden in browsers that support `:has()`.

Controllers are scoped to the current render context:

- page, detail page, form page, error page, allauth page: page-wide;
- feed item: within that feed item;
- calendar event: within that event;
- menu: within that menu.

## Context conditions

The condition builder is not page-specific. It evaluates against the current
render context:

| Placement | Context available |
|---|---|
| Page body | Page context models and bindings |
| Detail page/template | The detail entity plus page context |
| Feed item | The current item under the feed's context model key |
| Calendar event | The current event under the calendar's context model key |
| Reusable block | The surrounding context |
| Menu | Menu context bindings |

Choose a **Context**, then a **Property**, a **Comparison**, and a **Value**.
For example:

```text
Context:     Meeting (meeting)
Property:    Status
Comparison:  is exactly
Value:       published
```

This is stored as `meeting.status equals published`. The **Advanced expression**
field is for developer use only and must not be combined with the dropdowns.

If the selected context value is absent at render time, the condition fails
closed: the block is hidden, even for `is not` or an inverted condition.
Invalid expressions and missing custom rules also fail closed and are logged.

### Custom rules

Select **matches a custom rule** to use a callable registered in
`WAGTAIL_DAISIE_FEED_CONDITIONS`:

```python
WAGTAIL_DAISIE_FEED_CONDITIONS = {
    "featured": {
        "label": "Featured",
        "rule": "myapp.conditions.is_featured",
    },
}
```

Rules receive the object resolved from the advanced expression, or `None` when
no expression is set, plus the request.

## Scopes and CSS

Switch targets render inside a presentational `<daisie-visibility>` wrapper:

```html
<daisie-visibility class="daisie-visibility-target"
                   data-daisie-visibility-key="provider-details"
                   data-daisie-visibility-state="on">
  ...
</daisie-visibility>
```

The wrapper uses `display: contents` when visible and `display: none` when
hidden, so flex, grid, and layout-item behaviour is preserved.

Controllers emit per-key CSS:

- page-level controllers use `body:has(...)`;
- feed items use `[data-daisie-feed-item]:has(...)`;
- calendar events use `[data-daisie-calendar-event]:has(...)`;
- menus use `[data-daisie-menu]:has(...)`.

The CSS is only active under `@supports selector(:has(*))`. Without `:has()`
support, targets stay visible. The structural rules live in
`static/wagtail_daisIE/css/tailwind/visibility.css`, which the runtime compiler
bundles into every page.

## Validation

- Controller keys must be valid slugs and unique within the current scope.
- Target keys must be valid slugs.
- A target may reference a key that is not present; it stays hidden at render
  time.
- Controllers inside a feed item or calendar event are scoped to that item or
  event and do not leak into siblings.

## Compatibility note

Alternate feed item designs (`Feed.item_variants` and the public
`FeedItemVariantBlock`) were removed. Existing feeds keep their single item
design; visibility conditions replace the old variant conditions.
