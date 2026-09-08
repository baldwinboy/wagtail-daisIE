from copy import deepcopy

from django.conf import settings


DEFAULT_ICONS = {
    "iconify": {
        "api": "https://api.iconify.design",
        "mode": "cached-svg",  # "cached-svg" or "component"
        "collections": [
            "mdi",
            "fa6-solid",
            "fa6-regular",
            "fa6-brands",
            "lucide",
            "heroicons",
            "bootstrap",
            "material-symbols",
        ],
        "timeout": 3,
    },
    "cache_timeout": 604800,
}


def get_icon_config():
    """Return the merged icon settings (package defaults + user overrides)."""
    config = deepcopy(DEFAULT_ICONS)
    user = getattr(settings, "WAGTAIL_DAISIE_ICONS", None)
    if not user:
        return config

    for key, value in user.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


def get_iconify_config():
    return get_icon_config()["iconify"]


def get_icon_cache_timeout():
    return get_icon_config()["cache_timeout"]
