"""Migration-only block definitions.

The public ``FeedItemVariantBlock`` was removed when alternate feed item
designs were dropped. Historical migrations still reference its frozen key, so
this private class preserves the key and field shape for those migrations.
It is never exported, registered in admin, or added to a palette.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.compact import DaisieStreamBlock, DaisieStructBlock
from ..dynamic.conditions import (
    FEED_CONDITION_OPERATOR_CHOICES,
    get_feed_condition_choices,
)
from .blocks_data import ITEM_BLOCKS


class LegacyFeedItemVariantBlock(DaisieStructBlock):
    label = blocks.CharBlock(max_length=255, required=False, blank=True)
    expression = blocks.CharBlock(max_length=255, required=False, blank=True)
    operator = blocks.ChoiceBlock(
        choices=FEED_CONDITION_OPERATOR_CHOICES,
        default="is_true",
    )
    rule = blocks.ChoiceBlock(choices=get_feed_condition_choices, required=False)
    compare_value = blocks.CharBlock(max_length=255, required=False, blank=True)
    item = DaisieStreamBlock(ITEM_BLOCKS, label=_("Design"))

    class Meta:
        migration_key = "wagtail_daisIE.FeedItemVariantBlock"
        label = _("Item variant")
        icon = "copy"
        collapsed = True
