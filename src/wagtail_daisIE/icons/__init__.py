"""Universal icon providers.

Icons are stored as ``"<prefix>:<name>"``. The prefix identifies a registered
:class:`~wagtail_daisIE.icons.providers.base.IconProvider`, which knows how to
list/search icons and render them. Legacy values without a ``:`` are treated as
raw CSS class strings (e.g. ``"fa-solid fa-home"``).
"""

from .registry import (
    get_provider,
    icon_assets,
    register_provider,
    render_icon,
    search_icons,
)
from .value import split_icon, validate_icon


__all__ = [
    "get_provider",
    "icon_assets",
    "register_provider",
    "render_icon",
    "search_icons",
    "split_icon",
    "validate_icon",
]
