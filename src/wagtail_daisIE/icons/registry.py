import logging

from django.utils.html import escape
from django.utils.safestring import mark_safe

from .value import split_icon


logger = logging.getLogger(__name__)

_providers = {}
_builtins_loaded = False
_hooks_loaded = False
_db_loaded = False
_signals_connected = False


def register_provider(provider, replace=True):
    """Register an :class:`IconProvider`, keyed by its prefix."""
    if not replace and provider.prefix in _providers:
        return
    _providers[provider.prefix] = provider


def reset_providers():
    """Clear all registered and lazily-loaded providers (used by tests)."""
    global _builtins_loaded, _hooks_loaded, _db_loaded
    _providers.clear()
    _builtins_loaded = False
    _hooks_loaded = False
    _db_loaded = False


def _load_builtin_providers():
    global _builtins_loaded
    if _builtins_loaded:
        return
    _builtins_loaded = True
    from .providers.wagtail import WagtailIconProvider

    register_provider(WagtailIconProvider())


def _load_hook_providers():
    global _hooks_loaded
    if _hooks_loaded:
        return
    _hooks_loaded = True
    from wagtail import hooks

    providers = []
    for hook in hooks.get_hooks("register_icon_providers"):
        providers = hook(providers)
    for provider in providers or []:
        register_provider(provider)


def _connect_signals(model):
    global _signals_connected
    if _signals_connected:
        return
    _signals_connected = True
    from django.db.models.signals import post_delete, post_save

    def _invalidate(sender, **kwargs):
        global _db_loaded
        _db_loaded = False

    post_save.connect(
        _invalidate, sender=model, dispatch_uid="daisie_icon_source_saved"
    )
    post_delete.connect(
        _invalidate, sender=model, dispatch_uid="daisie_icon_source_deleted"
    )


def _register_default_iconify_providers():
    from .conf import get_iconify_config
    from .providers.iconify import IconifyProvider

    config = get_iconify_config()
    for collection in config["collections"]:
        register_provider(
            IconifyProvider(
                prefix=collection,
                label=collection,
                api_base=config["api"],
            )
        )


def _load_db_providers():
    global _db_loaded
    if _db_loaded:
        return
    _db_loaded = True
    try:
        from ..models import DaisyUIIconSource
    except Exception:  # pragma: no cover - models unavailable pre-migration
        _register_default_iconify_providers()
        return

    _connect_signals(DaisyUIIconSource)
    try:
        sources = list(
            DaisyUIIconSource.objects.filter(enabled=True).order_by("order", "label")
        )
    except Exception:  # pragma: no cover - table not migrated yet
        logger.debug("Icon sources unavailable; using defaults", exc_info=True)
        _register_default_iconify_providers()
        return

    if not sources:
        _register_default_iconify_providers()
        return

    for source in sources:
        try:
            register_provider(source.to_provider())
        except Exception:
            logger.exception("Could not load icon source %r", source)


def enabled_providers():
    _load_builtin_providers()
    _load_hook_providers()
    _load_db_providers()
    return [provider for provider in _providers.values() if provider.enabled]


def get_provider(prefix):
    if not prefix:
        return None
    _load_builtin_providers()
    _load_hook_providers()
    _load_db_providers()
    return _providers.get(prefix)


def render_icon(value, size=None, color=None, label=None):
    """Render a stored icon value to safe HTML."""
    prefix, name = split_icon(value)
    if not name:
        return ""

    try:
        if prefix is None:
            # Legacy raw CSS class value (e.g. "fa-solid fa-home").
            inner = f'<i class="{escape(name)}" aria-hidden="true"></i>'
        else:
            provider = get_provider(prefix)
            if provider is None:
                return ""
            inner = provider.render(name, size=size, color=color)
    except Exception:
        logger.exception("Failed to render icon %r", value)
        return ""

    if label:
        inner = f'{inner}<span class="sr-only">{escape(label)}</span>'
    return mark_safe(inner)  # noqa: S308


def search_icons(query, prefixes=None, limit=64, start=0):
    """Search all enabled providers, returning a flat list of icon dicts."""
    results = []
    prefix_set = set(prefixes) if prefixes else None
    for provider in enabled_providers():
        if prefix_set is not None and provider.prefix not in prefix_set:
            continue
        if not provider.search_enabled:
            continue
        try:
            results.extend(provider.search(query, limit=limit, start=start))
        except Exception:
            logger.exception("Icon search failed for %s", provider)
    return results


def icon_assets():
    """Return the de-duplicated head assets required by enabled providers."""
    assets = []
    seen = set()
    for provider in enabled_providers():
        for asset in provider.head_assets():
            key = (asset.get("type"), asset.get("url"))
            if key in seen:
                continue
            seen.add(key)
            assets.append(asset)
    return assets
