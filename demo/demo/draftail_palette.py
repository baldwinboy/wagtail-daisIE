"""PEP 562 bridge exposing daisIE font helpers to ``draftail_text_utils``.

``draftail_text_utils`` reads font families/URLs from module-level list
attributes, but ``wagtail_daisIE.utils`` exposes DB-backed functions. This
module resolves them lazily on first access so importing it never touches the
database.
"""


def __getattr__(name):
    if name == "DRAFTAIL_FONT_FAMILIES":
        from wagtail_daisIE.utils import get_draftail_font_families

        return get_draftail_font_families()
    if name == "DRAFTAIL_FONT_URLS":
        from wagtail_daisIE.utils import get_draftail_font_urls

        return get_draftail_font_urls()
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
