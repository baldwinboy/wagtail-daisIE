from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock
from wagtail.images.models import Image

from ..dynamic.resolvers import resolve_object, url_for_object
from .base import ThemedMediaBlock


def _image_alt(value):
    if value is None:
        return ""
    return (
        getattr(value, "alt", "")
        or getattr(value, "title", "")
        or getattr(value, "name", "")
        or ""
    )


class ImageBlock(ThemedMediaBlock):
    image = WagtailImageBlock(
        required=False,
        help_text=_("Image to display (when the source is a static image)."),
    )
    image_source = blocks.ChoiceBlock(
        choices=[
            ("static", _("Static image")),
            ("dynamic", _("From context")),
        ],
        default="static",
        required=False,
        label=_("Image source"),
    )
    image_expression = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Image expression"),
        help_text=_("e.g. {{ user.profile.image }}"),
    )
    caption = blocks.CharBlock(
        max_length=255,
        blank=True,
        required=False,
        help_text=_("Optional caption shown beneath the image."),
    )
    attribution = blocks.CharBlock(
        max_length=255,
        blank=True,
        required=False,
        help_text=_("Optional attribution or credit for the image."),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["resolved_image"] = None
        context["resolved_image_url"] = ""
        context["resolved_image_alt"] = ""
        if (value.get("image_source") or "static") == "dynamic":
            obj = resolve_object(value.get("image_expression"), context)
            if isinstance(obj, Image):
                context["resolved_image"] = obj
            elif obj is not None:
                context["resolved_image_url"] = url_for_object(obj)
                context["resolved_image_alt"] = _image_alt(obj)
        return context

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/image.html"
        form_layout = blocks.BlockGroup(
            children=["image", "image_source", "image_expression"],
            settings=["design", "audience", "caption", "attribution"],
        )


class EmbedBlock(ThemedMediaBlock):
    """
    A block that renders a Wagtail embed (video, etc.) inside a DaisyUI
    themed container. The URL is stored as a struct field alongside the
    ThemedMediaBlock styling settings.
    """

    url = blocks.URLBlock(
        label=_("Embed URL"),
        help_text=_("Paste the URL of the media you want to embed."),
        required=False,
    )

    def get_context(self, value, parent_context=None):
        from wagtail.embeds.format import embed_to_frontend_html

        context = super().get_context(value, parent_context)
        url = (value or {}).get("url", "")
        embed_html = ""
        if url:
            try:
                embed_html = embed_to_frontend_html(url)
            except Exception:
                embed_html = ""
        context["embed_html"] = embed_html
        return context

    def to_python(self, value):
        if isinstance(value, str):
            value = {"url": value}
        elif hasattr(value, "url"):
            value = {"url": value.url}
        return super().to_python(value)

    class Meta:
        icon = "media"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/embed.html"
        form_layout = blocks.BlockGroup(
            children=["url"],
            settings=["design", "audience"],
        )
