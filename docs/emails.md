# Emails (MJML)

`EmailTemplate` lets authors build an email from the same design primitives
used for pages, and renders it to [MJML](https://documentation.mjml.io) which is
compiled to responsive HTML.

## Layout

```
src/wagtail_daisIE/emails/
├── mjml.py       # component registry: hierarchy, ending tags, attributes
├── rendering.py  # theme/category defaults + two-pass MJML rendering
├── models.py     # EmailTemplate
├── view_sets.py  # Wagtail admin snippet group
└── blocks/       # email block subclasses (base, leaves, layout, content)
```

## How MJML is produced

1. `EmailTemplate.get_mjml()` calls `rendering.render_mjml`.
2. Pass one renders `emails/blocks/body_body.html` (`{% include_block content %}`).
   Every themed block resolves its `design` value through
   `base_blocks.mjml.build_design_style`, which returns literal CSS
   declarations (colours resolved from the active theme, because email clients
   do not support CSS custom properties). The declarations are split against the
   target component's attribute map (`emails.mjml.ATTR_MAPS`):
   - accepted attributes become inline MJML attributes,
   - everything else (shadow, margin, …) becomes a `.daisie-<hash>` rule in the
     shared style registry.
3. Pass two renders `emails/blocks/body.html`, which emits `<mj-head>` and
   `<mj-body>` using the collected styles. The admin preview wraps the result in
   `{% mjml %}…{% endmjml %}` to compile it.

The two passes exist because `<mj-style>` can only live in `<mj-head>`, which is
rendered before the body that defines the styles.

## Defaults via `mj-attributes`

`<mj-head><mj-attributes>` carries:

- theme defaults: `mj-all` font family, `mj-text` colour/size/line-height,
  `mj-button` colours and radius (`EmailTemplate.get_theme()`, falling back to
  the default theme);
- the template's **per-category defaults** from `EmailTemplate.design`
  (a `PageDesignBlock`) as named `mj-class` entries:
  `daisie-container` (`mj-section`), `daisie-text` (`mj-text`),
  `daisie-button` (`mj-button`), `daisie-media` (`mj-image`).

Each block adds `mj-class="daisie-<category>"` only when its component matches
the category's canonical component, so section-only attributes never bleed into
e.g. an `mj-accordion`. Per-block design is emitted inline and wins over the
class, per MJML's precedence (inline > `mj-class` > component defaults >
`mj-all` > MJML defaults).

## Hierarchy and ending tags

`emails/blocks/content.py` only exposes body-level components
(`EmailSectionBlock` → `mj-section`, `EmailRawBlock` → `mj-raw`); the section
template wraps its column-level content in an `mj-column`. The full model lives
in `emails/mjml.py`:

- `MJML_CHILDREN` / `MJML_PARENTS` — what may contain what;
- `ENDING_TAGS` — components that hold text/HTML only (`mj-text`, `mj-button`,
  `mj-table`, `mj-raw`, …);
- `MJML_ATTRS` / `ATTR_MAPS` — the attributes each component accepts and the
  CSS-property to attribute mapping. Components whose colour attribute is
  `container-background-color` (e.g. `mj-accordion`, `mj-text`) are handled
  automatically.

## Adding a component

1. Add or pick the component in `emails/mjml.py` (it already covers every
   documented component).
2. Subclass the matching web block in `emails/blocks/leaves.py`, set
   `email_mjml_tag` and `Meta.template` (a fresh `Meta`; Wagtail strips the
   inherited one) and add a template under
   `templates/wagtail_daisIE/emails/blocks/`.
3. Register it in `EMAIL_COLUMN_BLOCKS` (layout.py) or `EMAIL_BODY_BLOCKS`
   (content.py) as appropriate.

## Limits

MJML has no equivalent for `box-shadow`, margins, `gap`, hover/active button
states or Tailwind's responsive/layout utilities. Those are emitted as scoped
`mj-style` CSS where possible and otherwise dropped. See the plan/PR notes for
the deferred component subset (table, accordion, social, navbar, carousel).
