from django.utils.html import escape

from .base import IconProvider, style_value


class FontIconProvider(IconProvider):
    """Provider for webfont icon sets rendered with CSS classes."""

    kind = "font"

    def __init__(self, prefix, label, css_url="", css_class_prefix="", icons=None):
        super().__init__(prefix=prefix, label=label)
        self.css_url = css_url or ""
        self.css_class_prefix = css_class_prefix or ""
        self._icons = list(icons or [])

    def render(self, name, size=None, color=None):
        classes = f"{self.css_class_prefix}{name}".strip()
        style = style_value(size, color)
        style_attr = f' style="{style}"' if style else ""
        return f'<i class="{escape(classes)}" aria-hidden="true"{style_attr}></i>'

    def head_assets(self):
        if self.css_url:
            return [{"type": "css", "url": self.css_url}]
        return []

    def search(self, query, limit=64, start=0):
        query = (query or "").lower()
        names = [n for n in self._icons if not query or query in n.lower()]
        return [
            {"value": f"{self.prefix}:{name}", "name": name, "label": name}
            for name in names[start : start + limit]
        ]

    def browse(self, limit=None):
        names = self._icons[:limit] if limit else self._icons
        return [
            {"value": f"{self.prefix}:{name}", "name": name, "label": name}
            for name in names
        ]

    def info(self):
        return {"name": str(self.label), "total": len(self._icons)}
