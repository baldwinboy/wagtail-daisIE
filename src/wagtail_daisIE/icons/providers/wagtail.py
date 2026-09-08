import re

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .base import IconProvider, style_value


_SVG_TAG = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_ID_ATTR = re.compile(r'\s+id="[^"]*"')
_ARIA_HIDDEN_ATTR = re.compile(r'\s+aria-hidden="[^"]*"')
_STYLE_ATTR = re.compile(r'\s+style="[^"]*"')


def get_wagtail_icons():
    """Return a mapping of Wagtail icon name -> SVG template path."""
    from wagtail import hooks

    icons = []
    for hook in hooks.get_hooks("register_icons"):
        icons = hook(icons)

    mapping = {}
    for path in icons or []:
        name = path.rsplit("/", 1)[-1].removesuffix(".svg")
        mapping[name] = path
    return mapping


class WagtailIconProvider(IconProvider):
    """Built-in provider for icons registered via Wagtail's ``register_icons``."""

    kind = "wagtail"

    def __init__(self):
        super().__init__(prefix="wagtail", label=_("Wagtail icons"))

    def _icons(self):
        return get_wagtail_icons()

    def render(self, name, size=None, color=None):
        template = self._icons().get(name)
        if not template:
            return ""
        svg = render_to_string(template)
        return _prepare_svg(svg, size=size, color=color)

    def choice_label(self, name):
        return name.replace("-", " ").title()

    def search(self, query, limit=64, start=0):
        query = (query or "").lower()
        names = sorted(
            name for name in self._icons() if not query or query in name.lower()
        )
        page = names[start : start + limit]
        return [
            {"value": f"wagtail:{name}", "name": name, "label": self.choice_label(name)}
            for name in page
        ]

    def browse(self, limit=None):
        names = sorted(self._icons())
        if limit:
            names = names[:limit]
        return [
            {"value": f"wagtail:{name}", "name": name, "label": self.choice_label(name)}
            for name in names
        ]

    def info(self):
        return {"name": str(self.label), "total": len(self._icons())}


def _prepare_svg(svg, size=None, color=None):
    style = style_value(size, color)
    attrs = 'aria-hidden="true" focusable="false"'
    if style:
        attrs += f' style="{style}"'

    def _replace(match):
        tag = _ID_ATTR.sub("", match.group(0))
        tag = _ARIA_HIDDEN_ATTR.sub("", tag)
        tag = _STYLE_ATTR.sub("", tag)
        return f"{tag[:-1]} {attrs}>"

    return _SVG_TAG.sub(_replace, svg, count=1)
