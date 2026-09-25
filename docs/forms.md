# Form pages

`DaisieFormPage` is a Wagtail form page that:

* renders with DaisyUI field styling and per-field design;
* links each input to a field on a configured **context model** and creates an
  instance from the submission (optionally in an unapproved state);
* shows success and error bodies after a submission, with an optional success
  redirect.

## Creating a form page

Define the form field model (deriving from `DaisieFormField`) and the page
together:

```python
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail_daisIE.forms.fields import DaisieFormField
from wagtail_daisIE.forms.models import DaisieFormPage


class SuggestionFormField(DaisieFormField):
    page = ParentalKey(
        "SuggestionFormPage",
        related_name="form_fields",
        on_delete=models.CASCADE,
    )


class SuggestionFormPage(DaisieFormPage):
    parent_page_types = ["home.HomePage"]
    subpage_types = []
```

The target model must be declared as a context model:

```python
WAGTAIL_DAISIE_CONTEXT_MODELS = {
    "suggestion": {"label": "Suggestion", "model": "myapp.Suggestion"},
}
```

On the page in the admin:

* **Model to create**, **Require approval**, **Approval field** — as before.
* **Fields available to link** — a help panel lists every editable field on the
  bound model so admins know what inputs can be linked to. It updates when the
  chosen model changes.
* **Messages** — success body, error body and an optional success redirect.
* **Form fields** — each field’s **Model field** dropdown links the input to a
  model field (populated from the bound model).

> Do **not** set page settings such as `require_approval = True` as class
> attributes — that shadows the inherited model fields. Set them on the page
> instance (admin, data migration or seed).

## Per-field styling

Each form field has an **Input design** and a **Label design** (both typography
plus input styling — background, size, border, padding, margin and box). The
builder applies the input design to the widget and the label design to its
legend/label, so inputs and labels can be styled individually on top of the
DaisyUI defaults.

The page's **Submit button** field exposes the same button appearance
(`ButtonAppearanceBlock`).

## Ordering fields in the body

The page body is a form-specific stream (`FormContentBlock`). It carries every
block a normal page body has **plus** a **Form field** block, so inputs can be
interleaved with content:

```
Header
[Form field: Title]
Rich text
[Form field: Description]
```

How it works:

* the **Form field** block stores the clean name of one of the page's form
  fields (the dropdown is populated with the page's own fields);
* the page renders the real bound field there, so the input keeps its label,
  help text, styling and errors;
* because the body sits outside the `<form>` element, each input is associated
  with it through `form="daisie-form"`. This keeps body blocks that render
  their own `<form>` (newsletter, search, feed, action button) valid;
* any field you do **not** place is rendered inside the `<form>`, just above the
  submit button, so existing pages keep working;
* placing the same field twice is rejected when the page is saved.

`success_body` and `error_body` do not include the **Form field** block — there
is no form to render on those views.

## Success and error bodies

`success_body` and `error_body` are content streams (the same blocks as a page
body). They are **only** shown after a submission:

* an invalid POST renders the form with `error_body` (plus the field errors);
* a valid POST renders `success_body`, unless **Success redirect** is set, in
  which case the visitor is redirected to that page.

On a valid submission the landing context gains `payload.submission`, a mapping
of `{clean_name: cleaned value}` taken from the stored `FormSubmission`. Use it
to confirm what the visitor sent:

```html
{% daisie_richtext "Thanks for suggesting {{ payload.submission.title }}!" %}
```

Preview mode passes an empty mapping, so the expression renders as empty.

Templates: `wagtail_daisIE/forms/form_page.html`,
`wagtail_daisIE/forms/form_field.html`,
`wagtail_daisIE/forms/form_field_block.html`,
`wagtail_daisIE/forms/form_page_landing.html`.
Override them or `get_template()` / `get_landing_page_template()` as needed.

## How submission works

1. The form is validated and a `FormSubmission` is stored (Wagtail behaviour).
2. `create_instance_from_submission` builds the target model from each input’s
   linked **Model field** (falling back to the field’s clean name) and saves it.
3. If **Require approval** is on, the approval field is set to `False`, so the
   instance is hidden from the public until an editor approves it.

Failures creating the instance are logged and do not break the submission.

## Feedback and input blocks

The **Feedback** block group (alerts, toasts, progress, loading, steps, modal,
tooltip) and the **Data input** block group (input, textarea, select, checkbox,
toggle, radio, range, rating, file, fieldset) can be used in the success/error
bodies (and any page body) to design the look of those states without code.
