import re

from wagtail_daisIE.base_blocks.mjml import (
    build_design_style,
    build_spacing_style,
    flatten_hex,
    resolve_color,
    resolve_font_family,
    split_style,
    style_to_css,
)
from wagtail_daisIE.notifications.mjml import ATTR_MAPS, can_contain


class TestComponents:
    def test_can_contain(self):
        assert can_contain("mj-section", "mj-column")
        assert not can_contain("mj-column", "mj-section")
        assert not can_contain("mj-body", "mj-text")

    def test_attr_maps_target_real_attributes(self):
        """A typo in ATTR_MAPS silently drops a declaration in the output."""
        for tag, mapping in ATTR_MAPS.items():
            for source, target in mapping.items():
                assert target, (tag, source)
                assert re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", target), (
                    tag,
                    source,
                    target,
                )


class TestColorAndFont:
    def test_resolve_color_and_font(self):
        for value, expected in [
            ("#422ad5ff", "#422ad5"),
            ("#abcd", "#abc"),
            ("#422ad5", "#422ad5"),
            ("bg-[#0080ff]", "#0080ff"),
            ("text-[#0080ffaa]", "#0080ff"),
        ]:
            assert resolve_color(value) == expected
        # Not 4 or 8 digits, and not a colour at all: returned verbatim.
        assert flatten_hex("#12345") == "#12345"
        assert flatten_hex(None) is None

        assert resolve_font_family("font-heading", None) == "heading"
        assert resolve_font_family("serif", None) == "serif"


class TestDesignStyle:
    def test_padding_and_border(self):
        assert build_design_style({"padding": {"all_padding": "p-4"}}) == {
            "padding": "1rem"
        }
        style = build_design_style({"padding": {"all_padding": "p-4", "top": "pt-8"}})
        assert style["padding"] == "1rem" and style["padding-top"] == "2rem"
        assert build_design_style(
            {"border": {"border_width": 2, "border_style": "dashed"}}
        ) == {"border": "2px dashed #000000"}

    def test_typography_size_and_box(self):
        style = build_design_style(
            {
                "typography": {
                    "font_size": "text-lg",
                    "font_weight": "font-bold",
                    "text_align": "text-center",
                    "line_height": "leading-tight",
                    "letter_spacing": "tracking-wide",
                }
            }
        )
        assert style == {
            "font-size": "1.125rem",
            "font-weight": "700",
            "text-align": "center",
            "line-height": "1.25",
            "letter-spacing": "0.025em",
        }
        assert (
            build_design_style({"typography": {"font_size": "text-10xl"}})["font-size"]
            == "8.25rem"
        )
        box = build_design_style(
            {"box": {"rounded": "rounded-lg", "shadow": "shadow-sm"}}
        )
        assert box["border-radius"] == "0.5rem" and "box-shadow" in box

    def test_spacing_has_no_attribute(self):
        """Spacing is deliberately a no-op: MJML margins are structural."""
        assert build_spacing_style({"all": "gap-4"}) == {}
        assert build_design_style({"spacing": {"all": "gap-4"}}) == {}


class TestSplitStyle:
    def test_splits_attrs_and_leftovers(self):
        attrs, leftover = split_style(
            {"padding": "1rem", "box-shadow": "0 1px black"},
            ATTR_MAPS["mj-text"],
        )
        assert attrs == {"padding": "1rem"}
        assert leftover == {"box-shadow": "0 1px black"}
        assert style_to_css({"padding": "1rem", "color": "#000"}) == (
            "padding: 1rem; color: #000"
        )
