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

Each field also has a **Container design** for the wrapper around the label,
input, help text and errors, and upload fields have a separate **Upload design**
(tray and item styling, item rendering and empty fallback). Choice fields
(checkboxes and radio buttons) have **Choice options**: layout, wrap, grid
columns, overflow scrolling, size and box styling around the option list.

The page's **Form design** controls the `<form>` container; when set it replaces
the default `mt-8 space-y-4` classes. The **Submit button** field exposes the
same button appearance (`ButtonAppearanceBlock`).

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
2. The target model is built from each input’s linked **Model field** (falling
   back to the field’s clean name): `create_instance_from_submission` on a create
   page, or `update_instance_from_submission` in **edit mode**. Many-to-many and
   taggit values are set after the instance is saved.
3. If **Require approval** is on, the approval field is set to `False`, so the
   instance is hidden from the public until an editor approves it. To convert an
   approved instance into another record, configure an
   [approval workflow](approval.md).

Failures creating the instance are logged and do not break the submission.

### Editing an existing instance

Set `form_mode = "edit"` on a `DaisieFormPage` subclass (a class attribute, never
a model field). The bound instance is resolved from the page’s **Context
bindings** for `instance_model` (for example a `pk` path or query parameter); the
fields prefill from it and a valid submission updates it in place:

```python
class MeetingEditPage(DaisieFormPage):
    form_mode = "edit"  # instance comes from the page's context binding
```

## File and image uploads

Form field types are configurable. Register extra types — for example file or
image uploads — in settings:

```python
WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
    "avatar": {
        "label": _("Profile picture"),
        "display": "image",  # default | image | attachments
        "is_upload": True,
        "validators": ["myapp.validators.image_only"],
        "handler": "myapp.uploads.store",
    },
    "attachments": {
        "label": _("Attachments"),
        "display": "attachments",
        "multiple": True,
        "collection_validators": ["myapp.validators.at_most_five"],
        "is_upload": True,
        "handler": "myapp.uploads.store",
    },
}
```

The package ships **no default field types**: copy the entries you need. The
demo registers a `file` upload and a `tags` multi-select that uses
`wagtail_daisIE.widgets.DaisieAutocompleteSelectMultiple`. The same
autocomplete control is available as the **Autocomplete** block for page
bodies — see
[data-components.md](data-components.md#autocomplete-and-attachments).

Every registered type appears in each form field’s **Field type** dropdown.
An upload type (`is_upload: True`) with no `field` is built from the package’s
own `DaisieFileField`; `display` selects the widget (`default`, `image` or
`attachments`), and `multiple` allows several files. `field` may still be a
Django form field class **or** a factory taking `(form_field, options)`, so a
project can supply its own; `widget`, `widget_attrs` and `css` are applied to
the input and `options` are merged into the field constructor. Every dotted
path is imported lazily.

### Validation

The package ships **no validators** and imports no imaging library — projects
own validation and may use Pillow or anything else:

* `validators` — a list of callables (or dotted paths) run **once per uploaded
  file**, each `fn(uploaded_file) -> None` raising `ValidationError`;
* `collection_validators` — a list run **once on the final value** (the list of
  new uploads plus any kept edit-mode references), each `fn(files) -> None`.

A validator that cannot be imported **fails closed** with
`ImproperlyConfigured` rather than being skipped. Any exception other than
`ValidationError` propagates. An example using Pillow:

```python
# myapp/validators.py
from django.core.exceptions import ValidationError


def at_least_128px(file):
    from PIL import Image

    try:
        width, height = Image.open(file).size
    finally:
        file.seek(0)
    if min(width, height) < 128:
        raise ValidationError("Image must be at least 128x128.")
```

### Edit mode

In edit mode, existing attachment references render as hidden
`{field}-existing` inputs; removing a card removes its reference, so the
submitted value is the kept references plus any new uploads. The handler runs
only on genuinely new uploads (`UploadedFile`), so references are not
re-sent to storage. A multiple-attachment value cannot bind to a single model
`FileField`; persist via the handler, bind to a related model, or override
`create_instance_from_submission`.

Upload types (`is_upload: True`) **must** have a handler — the package ships no
default storage. Set it per type (`handler`) or project-wide:

```python
WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER = "myapp.uploads.store"
```

The handler decides where the file goes and what reference is recorded:

```python
from django.core.files.storage import default_storage


def store(*, page, form, field, file, request=None):
    stored = default_storage.save(f"uploads/{file.name}", file)
    return default_storage.url(stored)
```

It is called once per uploaded file (list values call it per item) and must
return a JSON-safe value, which is stored in the submission’s `form_data`. The
file object is still present while the bound model instance is created, so
linking an input to a model `FileField`/`ImageField` also works. A missing
handler raises `ImproperlyConfigured` at submission time and is reported when
the page is saved; an exception raised by the handler is **not** swallowed, so
a storage failure surfaces instead of silently recording the submission.

Per-field options (maximum size, accepted types, target folder) belong on your
concrete form field model, which can add its own columns; the handler and
builder both receive that field instance. Override `get_upload_handler()` on
the page to choose a handler per field or page instead of by type. Field-type
keys are stored on `DaisieFormField.field_type`, so keep them within 16
characters (the package logs a warning otherwise).

The `css` classes come from the compiled stylesheet: `file-input`, `input` and
`w-full` are already included, but any project-specific utility you add to a
type’s `css` must be present in your own Tailwind build (the package safelist
only scans the package’s own class choices and templates).

The form template already posts as `multipart/form-data`, so no template
changes are needed.

### Choice sources

A registered type may declare `choices`:

* `True` — read the field’s own **Choices** box (comma/newline separated; range
  tokens such as `5-120/5` expand to `5, 10, …, 120`);
* a callable `(form_field, form_context) -> options`, or a dotted path to one —
  for model-backed options. `form_context` carries the bound instance in edit
  mode (`{"instance": …, "context": {…}}`).

```python
WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
    "languages": {
        "label": _("Languages"),
        "field": "django.forms.MultipleChoiceField",
        "widget": "wagtail_daisIE.widgets.DaisieAutocompleteSelectMultiple",
        "choices": "myapp.filters.language_choices",
    },
}
```

Either source renders through `DaisieAutocompleteSelectMultiple`, a searchable
multi-select with a native `<select multiple>` fallback. The same control is
available as a **block** inside **Fieldset**, **Action forms** and **Tabs** (it
is deliberately not part of the top-level page palette, so adding it does not
force a migration).

## Feedback and input blocks

The **Feedback** block group (alerts, toasts, progress, loading, steps, modal,
tooltip) and the **Data input** block group (input, textarea, select, checkbox,
toggle, radio, range, rating, file, fieldset) can be used in the success/error
bodies (and any page body) to design the look of those states without code.

## Form pages vs the Action form block

`DaisieFormPage` is the right tool when a page **is** a form: it has one form,
binds inputs to a model, validates them and creates/stores an instance. The
**Action form** block (`dynamic/action_blocks.py`) is the right tool for
**several small forms on one page** (for example a tabbed settings page): each
block is an independent `<form>` that posts its fields to a configured action,
without a model binding. Prefer `DaisieFormPage` when you need per-field
validation and error rendering or file uploads tied to a model field; prefer
**Action form** when you need many independent "mini-forms" that call project
code. See [data-components.md](data-components.md#action-forms) and
[htmx.md](htmx.md).
