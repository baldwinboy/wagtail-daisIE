"""Shared plumbing for MJML email blocks.

Email blocks reuse the web block classes (fields, design composites and the
``build_design_*`` pipeline) and only add MJML-specific context:

* ``email_attributes`` — the design declarations the target ``mj-*`` component
  accepts as attributes,
* ``email_mj_class`` — the per-category ``mj-class`` seeded in ``mj-attributes``
  (only when the block's tag matches the category's canonical tag),
* ``email_css_class`` + a rule in the shared ``mjml_styles`` mapping — for the
  declarations MJML has no attribute for (shadow, margin, …).
"""

import hashlib

from ...base_blocks.mjml import build_design_style, split_style, style_to_css
from ..mjml import ATTR_MAPS, CATEGORY_TAGS


def mjml_css_class(declarations):
    """Return a stable class name for a set of leftover declarations."""
    digest = hashlib.sha256(style_to_css(declarations).encode()).hexdigest()[:8]
    return f"daisie-{digest}"


def get_mjml_styles(context):
    """Return the shared style registry from a (parent) context, creating it."""
    styles = context.get("mjml_styles")
    if styles is None:
        styles = {}
        context["mjml_styles"] = styles
    return styles


class EmailThemedMixin:
    """Add MJML context to a themed block without changing its web output.

    The mixin must come first in the MRO so its ``get_context`` wraps the
    block's own (web) ``get_context``.
    """

    email_mjml_tag = "mj-text"
    #: MJML components this block's content may contain (for validation tests).
    email_allowed_children = frozenset()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        theme = parent_context.get("email_theme") or context.get("email_theme")

        declarations = build_design_style((value or {}).get("design"), theme)
        attrs, leftover = split_style(
            declarations, ATTR_MAPS.get(self.email_mjml_tag, {})
        )

        category = getattr(self, "default_css_key", "container")
        context["email_tag"] = self.email_mjml_tag
        context["email_attributes"] = attrs
        context["email_css_class"] = ""
        context["email_mj_class"] = (
            f"daisie-{category}"
            if CATEGORY_TAGS.get(category) == self.email_mjml_tag
            else ""
        )

        styles = get_mjml_styles(parent_context)
        if leftover:
            css_class = mjml_css_class(leftover)
            context["email_css_class"] = css_class
            styles[css_class] = style_to_css(leftover)
        # Propagate the shared registry to children even when this block has
        # no leftovers of its own.
        context["mjml_styles"] = styles
        return context
