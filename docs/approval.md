# Approval workflows

`DaisieFormPage` can create a model instance in an **unapproved** state
(`require_approval` + `approval_field`, see [forms.md](forms.md)). An approval
workflow turns that instance into something else the first time an editor flips
the approval field to true — for example converting a `BreadSuggestion` into a
`Bread`.

The mechanism lives in `wagtail_daisIE.approval` (code only; no extra app to
install) and is driven by settings, like the detail-page and notification
bridges.

## Configuration

```python
# settings.py
WAGTAIL_DAISIE_APPROVAL_WORKFLOWS = {
    "bread_suggestion": {
        "label": "Bread suggestion",  # admin label (optional)
        "model": "blog.BreadSuggestion",  # source model
        "approval_field": "is_approved",  # bool field; triggers on False -> True
        "handler": "blog.workflows.approve_bread_suggestion",
        "converted_field": "bread",  # optional FK recording the result
    },
}
```

- **`model`** — `"app_label.ModelName"` or a dotted import path.
- **`approval_field`** — the boolean field on the source model (default
  `is_approved`).
- **`handler`** — a dotted path to a callable `handler(instance) -> object |
  None`. Returning `None` (or configuring no `converted_field`) leaves the
  source untouched; raising is logged and swallowed.
- **`converted_field`** — an optional FK/OneToOne on the source. When set, the
  handler's return value is stored there, and the workflow is skipped on later
  saves (idempotency).

## Example handler

```python
# blog/workflows.py
from datetime import date


def approve_bread_suggestion(suggestion):
    from blog.models import Bread

    bread, _created = Bread.objects.get_or_create(
        name=suggestion.title,
        defaults={
            "description": suggestion.description,
            "added_on": date.today(),
            "is_available": True,
        },
    )
    return bread
```

Creating a `Bread` also lets the configured
[detail-page bridge](detail-pages.md) generate its `BreadDetailPage` page.

## How it runs

- Bridges connect in the core `AppConfig.ready()` inside a `try/except`, and
  models/handlers are resolved lazily (never at import time).
- A `pre_save` receiver snapshots the previous value of `approval_field`.
- A `post_save` receiver runs the handler only on a `False → True` transition,
  and (when `converted_field` is set) skips instances that already have a
  converted value. The result is written back with a queryset `update` to avoid
  re-triggering signals.
