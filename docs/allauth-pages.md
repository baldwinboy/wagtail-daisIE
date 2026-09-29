# Designing allauth account pages

`AllauthPageOverride` lets content editors redesign django-allauth **account**
pages (sign in, sign up, password reset, email management, …) with the same
DaisyUI blocks used everywhere else, without touching allauth's forms or
validation.

Provided by the opt-in `wagtail_daisIE.allauth_ui` app (extra `allauth`).

> Only the `account` view set is supported for now. `socialaccount`, `mfa` and
> `usersessions` templates are intentionally not overridden and may not be made
> available. Contributions for those view sets are welcome.

## What editors control

Editors control the **look only**:

- **Theme**, **background**, **page default design**, and optional header/footer
  menus.
- A full **body** of content blocks, with two allauth-specific blocks:
  - **Form** (`auth_form`) — renders the real allauth `<form>` (CSRF, hidden
    fields and any fields not placed explicitly) plus the submit button.
  - **Form field** (`auth_field`) — renders one of the page's fields at this
    point in the body. Inputs are associated with the form via the HTML `form`
    attribute, so content blocks (including ones that render their own forms)
    can sit between fields.
- Per-field **label**, **help text**, **placeholder**, **presentation** and
  typography design.
- **One-time code** presentation: set a field's presentation to *One-time code*
  to render the daisyUI `otp` component (optional size, colour and joined
  boxes). Fields with `autocomplete="one-time-code"` are detected automatically.
- Text/select/textarea/file inputs carry the daisyUI `validator` class, and the
  submit button shows a `loading` spinner while the form is submitting.

Allauth always owns which fields exist and how they validate. Placing every
field with `auth_field` also controls the order; unplaced fields are appended by
the **Form** block.

## How it works

1. Add the opt-in flag and, for full chrome parity, your base template:

   ```python
   WAGTAIL_DAISIE_ALLAUTH_UI = True
   WAGTAIL_DAISIE_ALLAUTH_BASE_TEMPLATE = "base.html"
   ```

2. Run `migrate`. A row is seeded for every discovered account view under
   **Design → Allauth pages**.
3. Open a row, design the page, and tick **Active**. Rows are resolved per
   site: a row with a **Site** set wins for that site; an empty **Site** is the
   global fallback.
4. Preview the design from the snippet editor — a sample form for the selected
   view is rendered so the fields appear.

The package overrides every `account/*.html` template that defines a content
block. Each override keeps allauth's markup verbatim as a fallback and renders
the override body only when the row is active, so allauth keeps handling POSTs,
redirects and validation.

## Keeping overrides in sync

The overrides embed a verbatim copy of allauth's template content. After
upgrading django-allauth, check for drift:

```bash
python manage.py check_allauth_templates        # exits non-zero on drift
python manage.py check_allauth_templates --write  # regenerate
```

`--write` regenerates the overrides from the installed allauth templates; review
the diff before committing.

## Field blocks are look-only

`auth_field` cannot add or remove fields and cannot change `required`,
validators or widget types — allauth is the single source of truth for the form.
This keeps account security decisions (password rules, verification) in code.
