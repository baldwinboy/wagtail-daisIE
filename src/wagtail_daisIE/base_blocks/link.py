from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock


class LinkDestinationBlock(blocks.StreamBlock):
    """A single link destination chosen from page/URL/document/email/phone.

    This is a reusable custom ``StreamBlock``; wrap it in a ``StreamField``
    when it is stored as a model field. When nested inside a ``StructBlock``
    (as ``AbstractLinkBlock`` does) the ``StreamBlock`` instance is used
    directly, because ``StructBlock`` only registers child blocks.
    """

    link_page = blocks.PageChooserBlock(required=False, label=_("Page"))
    link_url = blocks.URLBlock(required=False, blank=True, label=_("External URL"))
    link_dynamic = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Dynamic URL"),
        help_text=_(
            "An expression resolving to a URL at render time, "
            "e.g. {{ meeting.url }}. Only http, https, mailto and tel are allowed."
        ),
    )
    link_document = DocumentChooserBlock(required=False, label=_("Document"))
    link_email = blocks.EmailBlock(required=False, blank=True, label=_("Email"))
    link_phone = blocks.CharBlock(required=False, blank=True, label=_("Phone"))

    class Meta:
        icon = "link"
        label = _("Destination")
        collapsed = True
        max_num = 1


def _destination_items(value):
    """Yield single-key mappings for the destination entries in ``value``.

    Handles a bound ``StreamValue`` (children expose ``block_type``/``value``),
    raw ``(type, value)`` tuples, ``{"type": ..., "value": ...}`` dicts, and the
    legacy ``StructBlock``-style ``{"link_page": ...}`` dict.
    """
    if not value:
        return
    if isinstance(value, dict):
        yield value
        return
    for child in value:
        if hasattr(child, "block_type"):
            yield {child.block_type: child.value}
        elif isinstance(child, (tuple, list)) and len(child) == 2:
            yield {child[0]: child[1]}
        elif isinstance(child, dict):
            if "type" in child and "value" in child:
                yield {child["type"]: child["value"]}
            else:
                yield child


def link_url(value, context=None):
    """Resolve a stored destination value to a URL."""
    for dest in _destination_items(value) or []:
        page = dest.get("link_page")
        if page:
            return getattr(page, "url", "") or ""
        if dest.get("link_dynamic"):
            from ..dynamic.resolvers import resolve_dynamic_url

            return resolve_dynamic_url(dest["link_dynamic"], context or {})
        if dest.get("link_url"):
            return dest["link_url"]
        document = dest.get("link_document")
        if document:
            return getattr(document, "url", "") or ""
        if dest.get("link_email"):
            return f"mailto:{dest['link_email']}"
        if dest.get("link_phone"):
            return f"tel:{dest['link_phone']}"
    return ""


def link_is_active(value, request):
    """Return whether a destination's page points at the current request path."""
    if not value or not request:
        return False
    for dest in _destination_items(value) or []:
        page = dest.get("link_page")
        if not page:
            continue
        try:
            return request.path.startswith(page.url_path)
        except Exception:
            return False
    return False


class AbstractLinkBlock(blocks.StructBlock):
    destination = LinkDestinationBlock()
    open_in_new_tab = blocks.BooleanBlock(
        default=False,
        required=False,
        label=_("Open in new tab"),
    )

    class Meta:
        abstract = True

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        request = (parent_context or {}).get("request")
        destination = (value or {}).get("destination")
        context["link_url"] = link_url(destination, context=context)
        context["link_new_tab"] = bool((value or {}).get("open_in_new_tab", False))
        context["link_is_active"] = link_is_active(destination, request)
        return context
