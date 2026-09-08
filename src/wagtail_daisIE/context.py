import contextvars


_current_theme: contextvars.ContextVar = contextvars.ContextVar(
    "wagtail_daisIE_current_theme", default=None
)


def set_current_theme(theme):
    """Set the DaisyUITheme for the current request/block context."""
    return _current_theme.set(theme)


def reset_current_theme(token):
    _current_theme.reset(token)


def get_current_theme():
    """Return the DaisyUITheme active for widget rendering, or None."""
    return _current_theme.get()


def theme_from_instance(instance):
    """
    Extract a DaisyUITheme from a Page or DaisyUIMenu-like instance.

    Pages carry ``page_theme``; menus (custom Snippets/Clusterable models)
    carry ``menu_theme``. Either may be None.
    """
    if instance is None:
        return None
    for attr in ("page_theme", "menu_theme"):
        theme = getattr(instance, attr, None)
        if theme is not None:
            return theme
    return None
