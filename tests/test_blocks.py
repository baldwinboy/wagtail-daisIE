from wagtail_daisIE.base_blocks import LinkDestinationBlock
from wagtail_daisIE.base_blocks.css import (
    build_border_css,
    build_button_css,
    build_design_css,
    build_typography_css,
    merge_block_css,
)
from wagtail_daisIE.base_blocks.link import link_is_active, link_url
from wagtail_daisIE.base_blocks.utils import build_class
from wagtail_daisIE.blocks import CONTENT_BLOCK, MenuItemStreamBlock


class TestBuildClass:
    def test_builds_css_from_values(self):
        assert build_class("bg-primary", "p-4", "rounded-lg") == (
            "bg-primary p-4 rounded-lg"
        )

    def test_skips_empty_values(self):
        assert build_class("bg-primary", "", "p-4") == "bg-primary p-4"

    def test_empty_input(self):
        assert build_class() == ""


class TestMergeBlockCss:
    def test_prepends_inherited(self):
        assert merge_block_css({"block_css": "font-body"}, "p-4") == "font-body p-4"

    def test_no_parent_context(self):
        assert merge_block_css(None, "p-4") == "p-4"

    def test_own_only(self):
        assert merge_block_css({}, "p-4") == "p-4"


class TestBuildTypographyCss:
    def test_prefixes_font_family_role(self):
        assert build_typography_css({"font_family": "heading"}) == "font-heading"

    def test_does_not_double_prefix(self):
        assert build_typography_css({"font_family": "font-body"}) == "font-body"

    def test_empty(self):
        assert build_typography_css({}) == ""


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

    def test_none(self):
        assert build_design_css(None) == ""


class TestBuildButtonCss:
    def test_none_is_empty(self):
        assert build_button_css(None) == ""

    def test_design_without_button_appearance_has_no_btn(self):
        css = build_design_css({"typography": {"text_color": "text-base-content"}})
        assert "btn" not in css.split()

    def test_button_appearance_adds_btn(self):
        css = build_design_css(
            {"button_appearance": {"normal": {}, "hover": {}, "active": {}}}
        )
        assert "btn" in css.split()


class TestBuildBorderCss:
    def test_no_width_is_empty(self):
        css = build_border_css(
            {
                "border_width": None,
                "border_color": "border-primary-content",
                "border_style": "solid",
            }
        )
        assert css == ""

    def test_width_emits_border(self):
        css = build_border_css({"border_width": 1})
        assert "border" in css.split()


class TestDesignDefaults:
    def test_typography_text_color_defaults_to_inherit(self):
        from wagtail_daisIE.base_blocks.typography import TypographyBlock

        block = TypographyBlock().child_blocks["text_color"]
        assert getattr(block.meta, "default", None) == ""

    def test_padding_defaults_to_none(self):
        from wagtail_daisIE.base_blocks.box import PaddingBlock

        block = PaddingBlock().child_blocks["all_padding"]
        assert getattr(block.meta, "default", None) == ""

    def test_spacing_defaults_to_none(self):
        from wagtail_daisIE.base_blocks.box import SpacingBlock

        block = SpacingBlock().child_blocks["all"]
        assert getattr(block.meta, "default", None) == ""

    def test_border_defaults_to_none(self):
        from wagtail_daisIE.base_blocks.box import BorderBlock

        assert BorderBlock().child_blocks["border_color"].meta.default == ""
        assert BorderBlock().child_blocks["border_style"].meta.default == ""


class TestLinkDestinationBlock:
    def test_max_num_is_one(self):
        assert LinkDestinationBlock().meta.max_num == 1

    def test_min_num_defaults_to_zero(self):
        assert not LinkDestinationBlock().meta.min_num

    def test_min_num_can_be_required(self):
        assert LinkDestinationBlock(min_num=1).meta.min_num == 1


class TestLinkUrl:
    def test_stream_value_url(self):
        value = LinkDestinationBlock().to_python(
            [{"type": "link_url", "value": "https://example.com"}]
        )
        assert link_url(value) == "https://example.com"

    def test_legacy_dict(self):
        assert link_url({"link_url": "https://example.com"}) == "https://example.com"
        assert link_url({"link_email": "a@b.com"}) == "mailto:a@b.com"
        assert link_url({"link_phone": "+123"}) == "tel:+123"

    def test_empty(self):
        assert link_url({}) == ""
        assert link_url(None) == ""


class TestLinkIsActive:
    def test_no_request(self):
        assert link_is_active({"link_url": "x"}, None) is False

    def test_matching_page_path(self):
        class FakePage:
            url_path = "/blog/"

        request = type("R", (), {"path": "/blog/x/"})()
        assert link_is_active({"link_page": FakePage()}, request) is True


class TestMenuBlocks:
    def test_menu_stream_contains_curated_subset(self):
        keys = list(MenuItemStreamBlock().child_blocks)
        assert keys == [
            "link",
            "button",
            "search",
            "inline_card",
            "accordion",
            "link_list",
            "header",
            "text",
            "newsletter",
        ]

    def test_content_block_includes_shared_blocks(self):
        keys = list(CONTENT_BLOCK().child_blocks)
        for name in ("image", "header", "text", "rich_text", "button", "card", "list"):
            assert name in keys
