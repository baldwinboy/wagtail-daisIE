from wagtail_daisIE.base_blocks import PageDesignBlock
from wagtail_daisIE.base_blocks.design import (
    ThemedBlock,
    ThemedButtonBlock,
    ThemedMediaBlock,
    ThemedTableBlock,
    ThemedTypographyBlock,
)


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
        assert ctx["text_css"] == "text-primary text-secondary"

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

    def test_nesting_and_menu_default(self):
        parent = {"text_css": "text-primary"}
        outer = _get_context(
            ThemedTypographyBlock(), {"typography": {"font_size": "text-xl"}}, parent
        )
        assert outer["text_css"] == "text-primary text-xl"

        inner = ThemedTypographyBlock().get_context(
            {
                "design": {"typography": {"text_color": "text-secondary"}},
                "audience": {},
            },
            outer,
        )
        assert inner["text_css"] == "text-primary text-xl text-secondary"
        other = ThemedButtonBlock().get_context({"design": {}, "audience": {}}, outer)
        assert "text-xl" not in other["block_css"].split()

        menu = {"menu_default_css": "font-body"}
        for block in (
            ThemedTypographyBlock(),
            ThemedButtonBlock(),
            ThemedMediaBlock(),
            ThemedBlock(),
        ):
            assert "font-body" in _get_context(block, {}, menu)["block_css"].split()

    def test_table_cells_seeded_from_text_channel(self):
        ctx = ThemedTableBlock().get_context(
            {"design": {}, "cell_design": {}, "header_cell_design": {}, "audience": {}},
            {"text_css": "text-primary"},
        )
        assert "text-primary" in ctx["cell_css"].split()
        assert "text-primary" in ctx["header_cell_css"].split()
