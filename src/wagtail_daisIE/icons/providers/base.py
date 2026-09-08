"""Icon provider base class and helpers."""


def style_value(size=None, color=None):
    """Build the raw inline style value for an icon's size and colour."""
    styles = []
    if size:
        styles.append(f"font-size: {size}")
    if color:
        styles.append(f"color: {color}")
    return "; ".join(styles)


def style_attrs(size=None, color=None):
    """Build an inline ``style`` string for an icon's size and colour."""
    value = style_value(size, color)
    return f' style="{value}"' if value else ""


class IconProvider:
    """Base class for an icon source.

    Subclasses implement ``render`` and, when searchable/browsable,
    ``search``/``browse``. Providers must never query the database at import
    time or in ``__init__``.
    """

    kind = "custom"
    search_enabled = True
    enabled = True

    def __init__(self, prefix, label, **options):
        self.prefix = prefix
        self.label = label
        self.options = options

    def head_assets(self):
        """Return a list of ``{"type": "script"|"css", "url": ...}`` assets."""
        return []

    def render(self, name, size=None, color=None):
        """Return safe HTML for a single icon (without accessibility wrapper)."""
        raise NotImplementedError

    def choice_label(self, name):
        return name

    def search(self, query, limit=64, start=0):
        """Return a list of ``{"value", "name", "label"}`` dicts."""
        return []

    def browse(self, limit=None):
        """Return icons available without a search query."""
        return []

    def info(self):
        """Return provider metadata (name, licence, total, ...)."""
        return {}

    def __repr__(self):
        return f"<{type(self).__name__} prefix={self.prefix!r}>"
