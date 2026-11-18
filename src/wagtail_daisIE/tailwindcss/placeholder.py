"""Template placeholder markup and per-page JSON config injection."""

from __future__ import annotations

import re

from django.templatetags.static import static
from django.utils.html import format_html, json_script
from django.utils.safestring import SafeString


JIT_PLACEHOLDER_ID = "daisyui-jit-styles"
JIT_CONFIG_ID = "daisyui-jit-config"

BASE_CSS_STATIC_PATH = "wagtail_daisIE/css/daisie-base.css"
JIT_JS_STATIC_PATH = "wagtail_daisIE/js/tailwind_jit.js"

_CONFIG_RE = re.compile(
    r'<script\b[^>]*\bid="daisyui-jit-config"[^>]*>.*?</script>',
    re.IGNORECASE | re.DOTALL,
)


def placeholder_html() -> SafeString:
    """Return the base stylesheet link, JIT placeholder, config and JS."""
    script = format_html(
        '<script type="module" src="{}"></script>',
        static(JIT_JS_STATIC_PATH),
    )
    return format_html(
        '<link rel="stylesheet" href="{}">\n<style id="{}"></style>\n{}{}',
        static(BASE_CSS_STATIC_PATH),
        JIT_PLACEHOLDER_ID,
        json_script({}, JIT_CONFIG_ID),
        script,
    )


def inject_config(
    html_text: str,
    config: dict,
    *,
    fragment: bool,
    key: str,
) -> str | None:
    """Replace the page config or prepend a fragment config.

    The compiled stylesheet is never inserted here.
    """
    if not fragment:
        replacement = json_script(config, JIT_CONFIG_ID)
        updated, count = _CONFIG_RE.subn(lambda _match: replacement, html_text, count=1)
        return updated if count else None

    fragment_id = f"{JIT_CONFIG_ID}-{key}"
    return f"{json_script(config, fragment_id)}\n{html_text}"
