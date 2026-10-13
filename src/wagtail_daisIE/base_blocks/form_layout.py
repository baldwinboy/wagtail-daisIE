"""Helpers for building ``StructBlock.Meta.form_layout`` definitions.

``StructBlock.Meta.collapsed`` only affects ``StructBlock``/``ListBlock``/
``StreamBlock`` panels; a ``FieldBlock`` such as ``IconChooserBlock`` ignores it.
Nesting related fields in a ``BlockGroup`` with ``classname="collapsed"`` keeps
long forms compact until the editor opens them.

Nested groups are only valid inside ``children`` (Wagtail resolves a top-level
``settings`` list by child name), and must not be combined with a custom
``form_template`` (system check ``wagtailcore.E007``).
"""

from __future__ import annotations

from wagtail import blocks


def collapsed_group(heading, *children, icon="placeholder"):
    """Return a nested, initially-collapsed ``BlockGroup``.

    A fresh instance is returned on every call so groups are never shared
    between block classes.
    """
    return blocks.BlockGroup(
        children=list(children),
        heading=heading,
        classname="collapsed",
        icon=icon,
    )
