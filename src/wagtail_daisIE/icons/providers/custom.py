import json
import logging

from functools import lru_cache
from pathlib import Path

from .base import IconProvider, style_value


logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def _load_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


class CustomIconProvider(IconProvider):
    """Provider for a project-supplied IconifyJSON manifest or icon map.

    The manifest may either be an IconifyJSON document (``{"icons": {...}}``)
    or a simple ``{name: "<svg .../>"}`` mapping.
    """

    kind = "custom"

    def __init__(self, prefix, label, manifest_path=""):
        super().__init__(prefix=prefix, label=label)
        self.manifest_path = manifest_path or ""

    def _data(self):
        if not self.manifest_path:
            return {}
        try:
            return _load_manifest(self.manifest_path)
        except Exception:
            logger.exception("Could not load icon manifest %s", self.manifest_path)
            return {}

    def _names(self):
        data = self._data()
        if "icons" in data:
            return sorted(data["icons"].keys())
        return sorted(data.keys())

    def _svg(self, name):
        data = self._data()
        if "icons" in data:
            icon = data["icons"].get(name)
            if not icon:
                return ""
            width = data.get("width", 24)
            height = data.get("height", 24)
            body = icon.get("body", "")
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
                f"{body}</svg>"
            )
        return data.get(name, "")

    def render(self, name, size=None, color=None):
        svg = self._svg(name)
        if not svg:
            return ""
        style = style_value(size, color)
        style_attr = f' style="{style}"' if style else ""
        return svg[:4] + f' aria-hidden="true" focusable="false"{style_attr}' + svg[4:]

    def search(self, query, limit=64, start=0):
        query = (query or "").lower()
        names = [n for n in self._names() if not query or query in n.lower()]
        return [
            {"value": f"{self.prefix}:{name}", "name": name, "label": name}
            for name in names[start : start + limit]
        ]

    def browse(self, limit=None):
        names = self._names()
        if limit:
            names = names[:limit]
        return [
            {"value": f"{self.prefix}:{name}", "name": name, "label": name}
            for name in names
        ]

    def info(self):
        return {"name": str(self.label), "total": len(self._names())}
