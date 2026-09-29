"""Build the block reference for the editor guide from the block registries.

Keeping this generated means the guide cannot drift from the blocks that are
actually available in the page editor.
"""

from django.utils.translation import gettext_lazy as _

from .blocks.content_blocks import PAGE_CONTENT_BLOCKS


#: One-line, editor-facing description for each block type.
BLOCK_DESCRIPTIONS = {
    "breadcrumbs": _("A trail of links back to parent pages."),
    "image": _("A picture, with an optional caption and credit."),
    "header": _("A heading."),
    "text": _("A short line of text."),
    "rich_text": _("A paragraph of formatted text."),
    "button": _("A button that links somewhere."),
    "inline_link": _("A text link."),
    "embed": _("Embedded media such as a video."),
    "inline_card": _("A small card that sits within other content."),
    "card": _("A box with an image, heading, text and actions."),
    "list": _("An ordered or unordered list of content blocks."),
    "link_list": _("A list of links, optionally with a heading."),
    "icon": _("A single icon."),
    "accordion": _("Collapsible sections that reveal their content."),
    "row": _("Lay blocks out side by side."),
    "column": _("A vertical stack of blocks."),
    "grid": _("A responsive grid of blocks."),
    "table": _("A data table."),
    "marquee": _("Scrolling text."),
    "copyright": _("A copyright line with the current year."),
    "blockquote": _("A quotation with an optional attribution."),
    "badge": _("A small status label."),
    "kbd": _("A keyboard key."),
    "divider": _("A horizontal or vertical separator."),
    "avatar": _("A round image, optionally with a status dot."),
    "stat": _("A single highlighted figure."),
    "countdown": _("A number displayed prominently."),
    "skeleton": _("A placeholder shape for loading states."),
    "text_rotate": _("Text that cycles through several lines."),
    "chat": _("A chat conversation."),
    "timeline": _("A vertical list of events."),
    "diff": _("A before/after comparison."),
    "hover_gallery": _("A gallery that reveals images on hover."),
    "hover_3d": _("A card with a 3D tilt on hover."),
    "stack": _("Stacked panels."),
    "aura": _("A soft glow behind the content."),
    "indicator": _("A small badge attached to a corner."),
    "mask": _("Content cropped into a shape."),
    "dropdown": _("A menu that opens from a button."),
    "swap": _("Two states that toggle."),
    "tabs": _("Content split into tabs."),
    "carousel": _("A horizontally scrolling set of slides."),
    "pagination": _("Navigation between pages."),
    "fab": _("A floating action button with options."),
    "drawer": _("A panel that slides in from the side."),
    "hero": _("A large banner with a heading, text and actions."),
    "filter": _("A set of filter controls for a feed."),
    "join": _("Items joined together as one control."),
    "mockup_browser": _("A browser frame around content."),
    "mockup_window": _("A window frame around content."),
    "mockup_phone": _("A phone frame around content."),
    "mockup_code": _("A code editor frame around text."),
    "alert": _("A highlighted message."),
    "status": _("A small status indicator."),
    "progress": _("A progress bar."),
    "radial_progress": _("A circular progress indicator."),
    "loading": _("A loading spinner."),
    "toast": _("A floating notification."),
    "modal": _("A dialog opened from a trigger."),
    "tooltip": _("A short message shown on hover."),
    "steps": _("A sequence of steps."),
    "input": _("A single-line text input."),
    "textarea": _("A multi-line text input."),
    "select": _("A dropdown select."),
    "checkbox": _("One or more checkboxes."),
    "toggle": _("A toggle switch."),
    "radio": _("A set of radio options."),
    "range": _("A slider."),
    "rating": _("A star rating."),
    "file": _("A file upload."),
    "fieldset": _("A group of inputs with a legend."),
    "newsletter": _("A newsletter sign-up form."),
}

#: Block group -> how-to page slug.
GROUP_HOWTO = {
    "Text": "text-blocks",
    "Media": "media-blocks",
    "Layout": "layout-blocks",
    "List": "layout-blocks",
    "Cards": "build-a-page",
    "Accordion": "layout-blocks",
    "Accordion Item": "layout-blocks",
    "Display": "display-blocks",
    "Table": "display-blocks",
    "Mockups": "display-blocks",
    "Feedback": "feedback-and-input-blocks",
    "Data input": "feedback-and-input-blocks",
    "Link": "buttons-and-actions",
    "Actions": "buttons-and-actions",
    "Navigation": "menus",
    "Menu items": "menus",
    "Branding": "menus",
    "Menu": "menus",
    "Data": "feeds",
    "Newsletter": "emails",
}


def _label(block, name):
    label = getattr(block, "label", "") or getattr(block.meta, "label", "")
    return str(label) if label else name.replace("_", " ").capitalize()


def build_block_reference():
    """Return ``[{group, howto, blocks: [{name, label, description}]}]``."""
    seen = {}
    for name, block in PAGE_CONTENT_BLOCKS:
        seen.setdefault(name, block)

    groups = {}
    for name, block in seen.items():
        group = str(getattr(block.meta, "group", "") or _("Other"))
        groups.setdefault(group, []).append(
            {
                "name": name,
                "label": _label(block, name),
                "description": str(BLOCK_DESCRIPTIONS.get(name, "")),
            }
        )

    return [
        {
            "group": group,
            "howto": GROUP_HOWTO.get(group),
            "blocks": sorted(blocks, key=lambda item: item["label"].lower()),
        }
        for group, blocks in sorted(groups.items())
    ]
