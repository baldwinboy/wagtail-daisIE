import re

from types import SimpleNamespace

import pytest

from wagtail_daisIE.base_blocks import LinkDestinationBlock
from wagtail_daisIE.base_blocks.css import (
    build_border_css,
    build_design_css,
    build_margin_css,
    build_size_css,
    build_typography_css,
    merge_block_css,
)
from wagtail_daisIE.base_blocks.link import link_is_active, link_url
from wagtail_daisIE.base_blocks.utils import build_class
from wagtail_daisIE.blocks.accordion import AccordionBlock


# Rendering blocks runs ``{% daisie_markup %}``, which resolves the current
# site from the database, so the render test needs database access.
pytestmark = pytest.mark.django_db


class TestBuildClass:
    def test_joins_and_skips_empty_values(self):
        assert build_class("bg-primary", "p-4", "rounded-lg") == (
            "bg-primary p-4 rounded-lg"
        )
        assert build_class("bg-primary", "", None, "p-4") == "bg-primary p-4"


class TestMergeBlockCss:
    def test_prepends_inherited_and_handles_missing(self):
        assert merge_block_css({"block_css": "font-body"}, "p-4") == "font-body p-4"
        # ``parent_context or {}`` is the root case: no channels at all.
        assert merge_block_css(None, "p-4") == "p-4"
        assert merge_block_css({}, "p-4") == "p-4"
        assert merge_block_css({"block_css": ""}, "p-4") == "p-4"


class TestBuildTypographyCss:
    def test_font_family_prefixing(self):
        assert build_typography_css({"font_family": "heading"}) == "font-heading"
        assert build_typography_css({"font_family": "font-body"}) == "font-body"


class TestAutoSpacingCss:
    def test_prefixed_margin_autos(self):
        assert (
            build_margin_css(
                {
                    "all_margins": "m-auto",
                    "top": "mt-auto",
                    "right": "mr-auto",
                    "bottom": "mb-auto",
                    "left": "ml-auto",
                }
            )
            == "m-auto mt-auto mr-auto mb-auto ml-auto"
        )

    def test_legacy_bare_margin_autos_are_prefixed(self):
        css = build_margin_css({"right": "auto", "left": "auto"})
        assert css.split() == ["mr-auto", "ml-auto"]
        assert "auto auto" not in css

    def test_prefixed_size_autos(self):
        assert (
            build_size_css(
                {
                    "size": "size-auto",
                    "width": {
                        "width": "w-auto",
                        "min_width": "min-w-auto",
                        "max_width": "max-w-auto",
                    },
                    "height": {
                        "height": "h-auto",
                        "min_height": "min-h-auto",
                        "max_height": "max-h-auto",
                    },
                }
            )
            == "size-auto w-auto min-w-auto h-auto min-h-auto"
        )

    def test_legacy_bare_size_autos_are_prefixed(self):
        assert (
            build_size_css(
                {
                    "size": "auto",
                    "width": {"width": "auto", "min_width": "auto"},
                    "height": {"height": "auto", "min_height": "auto"},
                }
            )
            == "size-auto w-auto min-w-auto h-auto min-h-auto"
        )

    def test_max_width_and_height_never_emit_auto(self):
        assert (
            build_size_css(
                {
                    "width": {"max_width": "auto"},
                    "height": {"max_height": "auto"},
                }
            )
            == ""
        )

    def test_scroll_is_emitted_from_the_size_block(self):
        assert build_size_css({"scroll": "overflow-y-auto"}) == "overflow-y-auto"


class TestBlockSizeScroll:
    def test_only_block_size_blocks_expose_scroll(self):
        from wagtail_daisIE.base_blocks.size import (
            BlockSizeBlock,
            InlineSizeBlock,
            MediaSizeBlock,
        )

        assert "scroll" in BlockSizeBlock().child_blocks
        assert "scroll" not in InlineSizeBlock().child_blocks
        assert "scroll" not in MediaSizeBlock().child_blocks


class TestRowScroll:
    def _context(self, *, scroll, wrap="flex-wrap"):
        from wagtail_daisIE.blocks.layout import RowBlock

        value = {
            "wrap": wrap,
            "design": {"size": {"scroll": scroll}},
            "content": [],
        }
        return RowBlock().get_context(value, {"request": None})

    def test_horizontal_scroll_forces_nowrap_and_non_shrinking_items(self):
        context = self._context(scroll="overflow-x-auto")
        assert context["row_wrap_css"] == ""
        assert context["row_scroll_css"] == "flex-nowrap"
        assert context["row_item_css"] == "shrink-0"
        assert "overflow-x-auto" in context["block_css"].split()

    def test_vertical_scroll_keeps_the_configured_wrap(self):
        context = self._context(scroll="overflow-y-auto", wrap="flex-wrap")
        assert context["row_wrap_css"] == "flex-wrap"
        assert context["row_scroll_css"] == ""
        assert context["row_item_css"] == "flex-1 min-w-0"
        assert "overflow-y-auto" in context["block_css"].split()


class TestBuildDesignCss:
    def test_aggregates_known_groups(self):
        css = build_design_css(
            {
                "typography": {"text_color": "text-base-content"},
                "padding": {"all_padding": "p-4"},
            }
        )
        assert "text-base-content" in css
        assert "p-4" in css

    def test_size_scroll_is_aggregated(self):
        assert (
            "overflow-y-auto"
            in build_design_css({"size": {"scroll": "overflow-y-auto"}}).split()
        )

    def test_button_appearance_controls_the_btn_class(self):
        """``btn`` comes from the appearance group, never from typography."""
        without = build_design_css({"typography": {"text_color": "text-base-content"}})
        assert "btn" not in without.split()
        with_appearance = build_design_css(
            {"button_appearance": {"normal": {}, "hover": {}, "active": {}}}
        )
        assert "btn" in with_appearance.split()

    def test_border_width(self):
        assert (
            build_border_css(
                {
                    "border_width": None,
                    "border_color": "border-primary-content",
                    "border_style": "solid",
                }
            )
            == ""
        )
        assert "border" in build_border_css({"border_width": 1}).split()


class TestLinkUrl:
    def test_stream_value_legacy_dicts_and_active(self):
        value = LinkDestinationBlock().to_python(
            [{"type": "link_url", "value": "https://example.com"}]
        )
        assert link_url(value) == "https://example.com"
        assert link_url({"link_url": "https://example.com"}) == "https://example.com"
        assert link_url({"link_email": "a@b.com"}) == "mailto:a@b.com"
        assert link_url({"link_phone": "+123"}) == "tel:+123"

        class FakePage:
            url_path = "/blog/"

        request = type("R", (), {"path": "/blog/x/"})()
        assert link_is_active({"link_page": FakePage()}, request) is True


class TestAccordion:
    def test_radio_group_scoped_to_the_accordion(self):
        def _value(labels):
            return {
                "items": [
                    {"heading": {"text": label}, "content": [], "collapsed": True}
                    for label in labels
                ],
                "design": {},
                "audience": {},
            }

        block = AccordionBlock()
        # ``block`` is supplied by the page template loop in real rendering.
        html_a = block.render(
            block.to_python(_value(["A", "B"])),
            context={"block": SimpleNamespace(id="a")},
        )
        html_b = block.render(
            block.to_python(_value(["C"])),
            context={"block": SimpleNamespace(id="b")},
        )

        names_a = re.findall(r'name="(accordion-[^"]+)"', html_a)
        names_b = re.findall(r'name="(accordion-[^"]+)"', html_b)

        assert names_a == ["accordion-a", "accordion-a"]  # items share one group
        assert names_b == ["accordion-b"]  # different accordion, different group
        assert names_a[0] != names_b[0]  # the cross-accordion bug is fixed


class TestReusableBlock:
    def test_renders_referenced_content_with_inherited_design(self):
        from wagtail_daisIE.blocks.reusable import ReusableBlockBlock
        from wagtail_daisIE.models import ReusableBlock

        reusable = ReusableBlock.objects.create(name="promo")
        reusable.content = [
            {
                "type": "text",
                "value": {
                    "text": "Hello",
                    "design": {"typography": {"text_color": "text-primary"}},
                    "audience": {},
                },
            }
        ]
        reusable.save()

        block = ReusableBlockBlock()
        value = block.to_python({"reusable": reusable.pk, "design": {}, "audience": {}})
        html = block.render(
            value,
            context={"container_css": "p-4", "menu_default_css": "font-body"},
        )
        assert "Hello" in html
        assert "p-4" in html  # the wrapper inherits the container channel
        assert "font-body" in html  # menu item defaults flow through
        assert "text-primary" in html  # the saved block's own design

    def test_missing_snippet_renders_nothing(self):
        from wagtail_daisIE.blocks.reusable import ReusableBlockBlock

        block = ReusableBlockBlock()
        value = block.to_python({"reusable": None, "design": {}, "audience": {}})
        assert block.render(value, context={}).strip() == ""


class TestInputWidgetDesign:
    def test_file_block_renders_tray_and_item_design(self):
        from wagtail_daisIE.blocks.inputs import FileInputBlock

        block = FileInputBlock()
        value = block.to_python(
            {
                "label": "Files",
                "name": "files",
                "display": "attachments",
                "multiple": True,
                "render": "thumbnail",
                "fallback": "icon",
                "accept": "",
                "color": "",
                "size": "",
                "helper_text": "",
                "tray_design": {"layout": "row", "gap": "gap-2", "wrap": "flex-wrap"},
                "item_design": {"shape": "rounded-full"},
                "design": {},
                "audience": {},
            }
        )
        html = block.render(value, context={})
        assert "data-daisie-file-attachments" in html
        assert "data-daisie-file-template" in html
        assert "gap-2" in html
        assert "rounded-full" in html

    def test_autocomplete_block_renders_tray_and_token_design(self):
        from wagtail_daisIE.blocks.inputs import AutocompleteSelectMultipleBlock

        block = AutocompleteSelectMultipleBlock()
        value = block.to_python(
            {
                "label": "Tags",
                "name": "tags",
                "options_source": "",
                "options": "a,b",
                "selected": "",
                "value_field": "pk",
                "label_field": "__str__",
                "placeholder": "",
                "color": "",
                "size": "",
                "required": False,
                "helper_text": "",
                "error_text": "",
                "tray_design": {"justify": "justify-center"},
                "item_design": {"shape": "rounded-full"},
                "design": {},
                "audience": {},
            }
        )
        html = block.render(value, context={})
        assert "data-daisyui-autocomplete-token" in html
        assert "justify-center" in html
        assert "rounded-full" in html
