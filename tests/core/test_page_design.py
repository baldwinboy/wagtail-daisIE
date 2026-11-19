from wagtail_daisIE.base_blocks import PageDesignBlock
from wagtail_daisIE.base_blocks.background_layer import BackgroundStreamBlock
from wagtail_daisIE.base_blocks.css import build_background_style
from wagtail_daisIE.base_blocks.design import (
    ThemedBlock,
    ThemedButtonBlock,
    ThemedMediaBlock,
    ThemedTableBlock,
    ThemedTypographyBlock,
)
from wagtail_daisIE.blocks.cards import CardBlock
from wagtail_daisIE.blocks.layout_components import TabsBlock


def _get_context(block, design, parent):
    return block.get_context({"design": design, "audience": {}}, dict(parent))


class TestPageDesignBlock:
    def test_maps_each_category_to_its_builder(self):
        css = PageDesignBlock().get_default_css(
            {
                "container": {"padding": {"all_padding": "p-4"}},
                "text": {"typography": {"text_color": "text-primary"}},
                "button": {"button_appearance": {"normal": {"color": "btn-primary"}}},
                "media": {"padding": {"all_padding": "p-2"}},
            }
        )
        assert set(css) == {"container", "text", "button", "media"}
        assert css["container"] == "p-4"
        assert css["text"] == "text-primary"
        assert css["button"] == "btn btn-primary"
        assert css["media"] == "p-2"


class TestCategoryIsolation:
    def test_typography_uses_only_text_channel(self):
        parent = {
            "container_css": "p-8",
            "text_css": "text-primary",
            "button_css": "btn-primary",
            "media_css": "aspect-video",
            "menu_default_css": "font-body",
        }
        ctx = _get_context(
            ThemedTypographyBlock(),
            {"typography": {"text_color": "text-secondary"}},
            parent,
        )
        classes = ctx["block_css"].split()
        assert "text-primary" in classes and "font-body" in classes
        assert "text-secondary" in classes
        assert "p-8" not in classes and "btn-primary" not in classes
        assert "aspect-video" not in classes
        # The channel stays page-level; the block's own design is not
        # written back for descendants.
        assert ctx["text_css"] == "text-primary"

    def test_block_inherits_only_its_own_channel(self):
        """Cross-category leakage is the bug this guards against."""
        for block, parent, inherited, forbidden in [
            (
                ThemedButtonBlock,
                {"text_css": "text-primary", "button_css": "btn btn-primary"},
                "btn-primary",
                "text-primary",
            ),
            (
                ThemedMediaBlock,
                {"text_css": "text-primary", "media_css": "aspect-video"},
                "aspect-video",
                "text-primary",
            ),
            (
                ThemedBlock,
                {"container_css": "p-4", "text_css": "text-primary"},
                "p-4",
                "text-primary",
            ),
        ]:
            classes = _get_context(block(), {}, parent)["block_css"].split()
            assert inherited in classes and forbidden not in classes

    def test_parent_design_does_not_cascade_but_page_channel_does(self):
        parent = {"text_css": "text-primary"}
        outer = _get_context(
            ThemedTypographyBlock(), {"typography": {"font_size": "text-xl"}}, parent
        )
        assert outer["block_css"].split() == ["text-primary", "text-xl"]
        assert outer["text_css"] == "text-primary"

        inner = ThemedTypographyBlock().get_context(
            {
                "design": {"typography": {"text_color": "text-secondary"}},
                "audience": {},
            },
            outer,
        )
        classes = inner["block_css"].split()
        assert classes == ["text-primary", "text-secondary"]
        assert inner["text_css"] == "text-primary"

        other = ThemedButtonBlock().get_context({"design": {}, "audience": {}}, outer)
        assert "text-xl" not in other["block_css"].split()

    def test_page_channel_reaches_every_nested_category(self):
        cases = [
            (ThemedBlock, {"container_css": "p-4"}),
            (ThemedTypographyBlock, {"text_css": "text-primary"}),
            (ThemedButtonBlock, {"button_css": "btn btn-primary"}),
            (ThemedMediaBlock, {"media_css": "aspect-video"}),
        ]
        for block_class, parent in cases:
            outer = _get_context(block_class(), {}, parent)
            inner = block_class().get_context({"design": {}, "audience": {}}, outer)
            for css in parent.values():
                for token in css.split():
                    assert token in inner["block_css"].split()

    def test_menu_defaults_apply_to_the_top_level_item_only(self):
        menu = {
            "menu_default_css": "font-body",
            "menu_default_style": "background: red",
        }
        for block in (
            ThemedTypographyBlock(),
            ThemedButtonBlock(),
            ThemedMediaBlock(),
            ThemedBlock(),
        ):
            item = _get_context(block, {}, menu)
            assert "font-body" in item["block_css"].split()
            assert item["block_style"] == "background: red"
            assert item["menu_default_css"] == ""
            assert item["menu_default_style"] == ""

            nested = ThemedTypographyBlock().get_context(
                {"design": {}, "audience": {}}, item
            )
            assert "font-body" not in nested["block_css"].split()
            assert nested["block_style"] == ""

    def test_table_cells_seeded_from_text_channel(self):
        ctx = ThemedTableBlock().get_context(
            {"design": {}, "cell_design": {}, "header_cell_design": {}, "audience": {}},
            {"text_css": "text-primary"},
        )
        assert "text-primary" in ctx["cell_css"].split()
        assert "text-primary" in ctx["header_cell_css"].split()


class TestTabsInheritance:
    def test_tab_designs_stay_on_their_elements(self):
        context = TabsBlock().get_context(
            {
                "tabs": [{"label": "One", "content": [], "audience": {}}],
                "style": "tabs-box",
                "size": "",
                "placement": "",
                "design": {"padding": {"all_padding": "p-8"}},
                "panel_design": {"padding": {"all_padding": "p-6"}},
                "audience": {},
            },
            {"container_css": "p-4"},
        )
        assert "p-8" in context["block_css"].split()
        assert "p-6" in context["tab_panel_css"].split()

        child = CardBlock().get_context(
            {"content": [], "design": {}, "audience": {}, "alignment": {}},
            context,
        )
        classes = child["block_css"].split()
        assert "p-4" in classes
        assert "p-8" not in classes
        assert "p-6" not in classes


def test_build_background_style_from_design_value():
    background = BackgroundStreamBlock().to_python(
        [{"type": "layer", "value": {"layer_type": "solid", "color": "#ff0000"}}]
    )
    assert build_background_style({"background": background}) == ("background: #ff0000")
    assert build_background_style({"background": {}}) == ""
    assert build_background_style(None) == ""
