"""Fixed editor order for stream-block groups."""

from __future__ import annotations


#: Groups not listed here keep their natural first-seen order and are appended.
GROUP_ORDER = (
    "Layout",
    "Text",
    "Link",
    "Cards",
    "List",
    "Navigation",
    "Data",
    "Data input",
    "Actions",
    "Feedback",
    "Mockups",
    "Media",
    "Display",
)

_GROUP_RANK = {name: index for index, name in enumerate(GROUP_ORDER)}


def group_rank(group: object) -> int:
    # Group labels are gettext_lazy; use the untranslated source when available
    # so the fixed order still works under a non-English locale.
    args = getattr(group, "_args", None)
    key = str(args[0]) if args else str(group)
    return _GROUP_RANK.get(key, len(GROUP_ORDER))


__all__ = ["GROUP_ORDER", "group_rank"]
