from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from .base import ThemedMediaBlock


class ImageBlock(ThemedMediaBlock):
    image = WagtailImageBlock(help_text=_("Image to display"))
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

    class Meta:
        icon = "image"
        group = _("Image")
        collapsed = True
        template = "wagtail_daisIE/blocks/image.html"
        form_layout = blocks.BlockGroup(
            children=["image"],
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
        group = _("Embed")
        collapsed = True
        template = "wagtail_daisIE/blocks/embed.html"
        form_layout = blocks.BlockGroup(
            children=["url"],
            settings=["design", "audience"],
        )
