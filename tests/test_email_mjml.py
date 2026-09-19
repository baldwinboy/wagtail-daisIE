from wagtail_daisIE.base_blocks.mjml import (
    build_design_style,
    flatten_hex,
    resolve_color,
    resolve_font_family,
    split_style,
    style_to_css,
)
from wagtail_daisIE.emails.mjml import (
    ATTR_MAPS,
    ENDING_TAGS,
    MJML_ATTRS,
    MJML_CHILDREN,
    MJML_PARENTS,
    can_contain,
    is_ending,
)


class TestRegistryConsistency:
    def test_every_component_has_attrs(self):
        assert set(MJML_CHILDREN) <= set(MJML_ATTRS)

    def test_children_and_parents_agree(self):
        for parent, children in MJML_CHILDREN.items():
            for child in children:
                assert parent in MJML_PARENTS[child], (parent, child)

    def test_ending_tags_have_no_children(self):
        for tag in ENDING_TAGS:
            assert MJML_CHILDREN[tag] == frozenset()
            assert is_ending(tag)

    def test_can_contain(self):
        assert can_contain("mj-section", "mj-column")
        assert not can_contain("mj-column", "mj-section")
        assert not can_contain("mj-body", "mj-text")

    def test_navbar_link_only_inside_navbar(self):
        assert MJML_PARENTS["mj-navbar-link"] == frozenset({"mj-navbar"})


class TestAttrMaps:
    def test_targets_are_valid_attributes(self):
        for tag, mapping in ATTR_MAPS.items():
            assert set(mapping.values()) <= MJML_ATTRS[tag], tag

    def test_text_background_uses_container_background(self):
        assert ATTR_MAPS["mj-text"]["background-color"] == (
            "container-background-color"
        )

    def test_accordion_background_uses_container_background(self):
        assert ATTR_MAPS["mj-accordion"]["background-color"] == (
            "container-background-color"
        )

    def test_section_background_is_direct(self):
        assert ATTR_MAPS["mj-section"]["background-color"] == "background-color"

    def test_button_padding_maps_to_inner_padding(self):
        assert ATTR_MAPS["mj-button"]["padding"] == "inner-padding"

    def test_text_align_falls_back_to_align(self):
        assert ATTR_MAPS["mj-text"]["text-align"] == "align"


class TestColorAndFont:
    def test_flatten_hex(self):
        assert flatten_hex("#422ad5ff") == "#422ad5"
        assert flatten_hex("#abcd") == "#abc"
        assert flatten_hex("#422ad5") == "#422ad5"

    def test_resolve_class_hex(self):
        assert resolve_color("bg-[#0080ff]") == "#0080ff"
        assert resolve_color("text-[#0080ffaa]") == "#0080ff"

    def test_resolve_raw_hex(self):
        assert resolve_color("#ff0000ff") == "#ff0000"

    def test_custom_font_without_theme_is_stripped(self):
        assert resolve_font_family("font-heading", None) == "heading"
        assert resolve_font_family("serif", None) == "serif"


class TestDesignStyle:
    def test_padding(self):
        style = build_design_style({"padding": {"all_padding": "p-4"}})
        assert style == {"padding": "1rem"}

    def test_padding_side_overrides_all(self):
        style = build_design_style({"padding": {"all_padding": "p-4", "top": "pt-8"}})
        assert style["padding"] == "1rem"
        assert style["padding-top"] == "2rem"

    def test_typography_without_theme(self):
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

    def test_large_font_size_uses_theme_scale(self):
        style = build_design_style({"typography": {"font_size": "text-10xl"}})
        assert style["font-size"] == "8.25rem"

    def test_border(self):
        style = build_design_style(
            {"border": {"border_width": 2, "border_style": "dashed"}}
        )
        assert style == {"border": "2px dashed #000000"}

    def test_box_shadow(self):
        style = build_design_style(
            {"box": {"rounded": "rounded-lg", "shadow": "shadow-sm"}}
        )
        assert style["border-radius"] == "0.5rem"
        assert "box-shadow" in style

    def test_spacing_has_no_attribute(self):
        assert build_design_style({"spacing": {"all": "gap-4"}}) == {}


class TestSplitStyle:
    def test_splits_attrs_and_leftovers(self):
        attrs, leftover = split_style(
            {"padding": "1rem", "box-shadow": "0 1px black"},
            ATTR_MAPS["mj-text"],
        )
        assert attrs == {"padding": "1rem"}
        assert leftover == {"box-shadow": "0 1px black"}

    def test_style_to_css(self):
        assert style_to_css({"padding": "1rem", "color": "#000"}) == (
            "padding: 1rem; color: #000"
        )
