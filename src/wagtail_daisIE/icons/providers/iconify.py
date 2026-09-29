import hashlib
import logging
import re

import requests

from django.core.cache import cache
from django.utils.html import escape

from ..conf import get_icon_cache_timeout, get_iconify_config
from .base import IconProvider, style_value


logger = logging.getLogger(__name__)

ICONIFY_ICON_SCRIPT = (
    "https://code.iconify.design/iconify-icon/3.0.0/iconify-icon.min.js"
)

_SVG_TAG = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
#: ``<script>`` with a body, then any leftover opener (unterminated or
#: self-closing) so a truncated response cannot smuggle one through.
_SCRIPT = re.compile(
    r"<script\b[^>]*>.*?</script\s*>|<script\b[^>]*/?>",
    re.IGNORECASE | re.DOTALL,
)
#: ``on*`` handlers, in any quoting style (``"``, ``'`` or bare).
_EVENT_ATTR = re.compile(
    r"\son\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)
#: Anything that can navigate or embed: ``href``/``src``/``xlink:href``.
_URL_ATTR = re.compile(
    r"\s(?:xlink:)?(?:href|src)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)
_ID_ATTR = re.compile(r'\s+id="[^"]*"')
#: SVG elements that can host script or external content. Paired forms are
#: removed with their body first, then any leftover open/void tag.
_FOREIGN_TAGS = "foreignObject|iframe|embed|object|use|animate|set"
_FOREIGN_PAIRED = re.compile(
    rf"<\s*(?:{_FOREIGN_TAGS})\b[^>]*>.*?<\s*/\s*(?:{_FOREIGN_TAGS})\s*>",
    re.IGNORECASE | re.DOTALL,
)
_FOREIGN_VOID = re.compile(
    rf"<\s*/?\s*(?:{_FOREIGN_TAGS})\b[^>]*>",
    re.IGNORECASE,
)


def _sanitize_svg(svg):
    """Strip anything executable from remote SVG before it is inlined.

    The markup is served straight from a third-party API, so it is treated as
    untrusted: scripts, event handlers, external references and the elements
    that can host them are removed rather than escaped, and the whole document
    is discarded if it is not an SVG at all.
    """
    if not svg or "<svg" not in svg:
        return ""
    svg = _FOREIGN_PAIRED.sub("", svg)
    svg = _FOREIGN_VOID.sub("", svg)
    svg = _SCRIPT.sub("", svg)
    svg = _EVENT_ATTR.sub("", svg)
    svg = _URL_ATTR.sub("", svg)
    return svg


def _apply_attrs(svg, size=None, color=None):
    style = style_value(size, color)
    attrs = 'aria-hidden="true" focusable="false"'
    if style:
        attrs += f' style="{escape(style)}"'

    def _replace(match):
        tag = _ID_ATTR.sub("", match.group(0))
        return f"{tag[:-1]} {attrs}>"

    return _SVG_TAG.sub(_replace, svg, count=1)


class IconifyProvider(IconProvider):
    """Icons served on demand by an Iconify API (public or self-hosted)."""

    kind = "iconify"

    def __init__(self, prefix, label, api_base=None, info=None):
        config = get_iconify_config()
        super().__init__(prefix=prefix, label=label, info=info or {})
        self.api_base = (api_base or config["api"]).rstrip("/")
        self.timeout = config["timeout"]
        self.mode = config["mode"]

    # -- fetching -----------------------------------------------------------
    def _get(self, path, params=None):
        return requests.get(
            f"{self.api_base}{path}",
            params=params,
            timeout=self.timeout,
            headers={"User-Agent": "wagtail-daisIE"},
        )

    def _cached_json(self, key, path, params=None):
        data = cache.get(key)
        if data is None:
            response = self._get(path, params=params)
            response.raise_for_status()
            data = response.json()
            cache.set(key, data, timeout=get_icon_cache_timeout())
        return data

    def _get_svg(self, name):
        key = f"daisie:icon:svg:{self.api_base}:{self.prefix}:{name}"
        svg = cache.get(key)
        if svg is None:
            try:
                response = self._get(f"/{self.prefix}/{name}.svg")
                response.raise_for_status()
                svg = _sanitize_svg(response.text)
            except Exception:
                logger.warning("Could not fetch Iconify icon %s:%s", self.prefix, name)
                return ""
            cache.set(key, svg, timeout=get_icon_cache_timeout())
        return svg

    # -- rendering ----------------------------------------------------------
    def render(self, name, size=None, color=None):
        if self.mode == "component":
            style = style_value(size, color)
            style_attr = f' style="{style}"' if style else ""
            return (
                f'<iconify-icon class="daisyui-icon" icon="{self.prefix}:{escape(name)}"'
                f"{style_attr}></iconify-icon>"
            )
        svg = self._get_svg(name)
        if not svg:
            return ""
        return _apply_attrs(svg, size=size, color=color)

    def email_svg(self, name, color=None):
        # Email clients cannot render the ``<iconify-icon>`` web component, so
        # always fall back to the sanitised inline SVG.
        return self._get_svg(name)

    def head_assets(self):
        if self.mode == "component":
            return [{"type": "script", "url": ICONIFY_ICON_SCRIPT}]
        return []

    # -- listing ------------------------------------------------------------
    def _to_result(self, icon):
        name = icon.split(":", 1)[-1]
        return {
            "value": f"{self.prefix}:{name}",
            "name": name,
            "label": self.choice_label(name),
        }

    def choice_label(self, name):
        return name.replace("-", " ").title()

    def search(self, query, limit=64, start=0):
        key = (
            "daisie:icon:search:"
            + hashlib.sha256(
                f"{self.api_base}:{self.prefix}:{query}:{limit}:{start}".encode()
            ).hexdigest()
        )
        try:
            data = self._cached_json(
                key,
                "/search",
                params={
                    "query": query,
                    "prefix": self.prefix,
                    "limit": limit,
                    "start": start,
                },
            )
        except Exception:
            logger.warning("Iconify search failed for %s", self.prefix)
            return []
        return [self._to_result(icon) for icon in data.get("icons", [])]

    def browse(self, limit=None):
        key = f"daisie:icon:collection:{self.api_base}:{self.prefix}"
        try:
            data = self._cached_json(
                key, "/collection", params={"prefix": self.prefix, "info": True}
            )
        except Exception:
            logger.warning("Iconify collection listing failed for %s", self.prefix)
            return []

        names = list(data.get("uncategorized", []))
        for category_names in (data.get("categories") or {}).values():
            names.extend(category_names)
        # Preserve order while removing duplicates.
        names = list(dict.fromkeys(names))
        if limit:
            names = names[:limit]
        return [self._to_result(f"{self.prefix}:{name}") for name in names]

    def info(self):
        info = self.options.get("info") or {}
        if info:
            return info
        key = f"daisie:icon:collections:{self.api_base}"
        try:
            collections = self._cached_json(key, "/collections")
        except Exception:
            return {}
        return collections.get(self.prefix, {})
