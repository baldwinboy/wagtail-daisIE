import re

from types import SimpleNamespace

import pytest

from wagtail_daisIE.base_blocks import LinkDestinationBlock
from wagtail_daisIE.base_blocks.css import (
    build_border_css,
    build_design_css,
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
