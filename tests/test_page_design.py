from wagtail_daisIE.base_blocks import PageDesignBlock
from wagtail_daisIE.base_blocks.design import (
    ThemedBlock,
    ThemedButtonBlock,
    ThemedMediaBlock,
    ThemedTableBlock,
    ThemedTypographyBlock,
)


def _get_context(block, design, parent):
    value = {"design": design, "audience": {}}
    return block.get_context(value, dict(parent))


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

    def test_empty_value_yields_empty_category_strings(self):
        assert PageDesignBlock().get_default_css(None) == {
            "container": "",
            "text": "",
            "button": "",
            "media": "",
        }


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
        assert "text-primary" in classes
        assert "font-body" in classes
        assert "text-secondary" in classes
        assert "p-8" not in classes
        assert "btn-primary" not in classes
        assert "aspect-video" not in classes
        assert ctx["text_css"] == "text-primary text-secondary"

    def test_button_uses_only_button_channel(self):
        parent = {"text_css": "text-primary", "button_css": "btn btn-primary"}
        ctx = _get_context(ThemedButtonBlock(), {}, parent)
        assert "btn-primary" in ctx["block_css"].split()
        assert "text-primary" not in ctx["block_css"].split()

    def test_media_uses_only_media_channel(self):
        parent = {"text_css": "text-primary", "media_css": "aspect-video"}
        ctx = _get_context(ThemedMediaBlock(), {}, parent)
        assert "aspect-video" in ctx["block_css"].split()
        assert "text-primary" not in ctx["block_css"].split()

    def test_container_uses_only_container_channel(self):
        parent = {"container_css": "p-4", "text_css": "text-primary"}
        ctx = _get_context(ThemedBlock(), {}, parent)
        assert "p-4" in ctx["block_css"].split()
        assert "text-primary" not in ctx["block_css"].split()

    def test_same_category_nesting_accumulates(self):
        parent = {"text_css": "text-primary"}
        outer = _get_context(
            ThemedTypographyBlock(),
            {"typography": {"font_size": "text-xl"}},
            parent,
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

    def test_menu_default_applies_cross_category(self):
        parent = {"menu_default_css": "font-body"}
        for block in (
            ThemedTypographyBlock(),
            ThemedButtonBlock(),
            ThemedMediaBlock(),
            ThemedBlock(),
        ):
            ctx = _get_context(block, {}, parent)
            assert "font-body" in ctx["block_css"].split()

    def test_table_cells_seeded_from_text_channel(self):
        ctx = ThemedTableBlock().get_context(
            {
                "design": {},
                "cell_design": {},
                "header_cell_design": {},
                "audience": {},
            },
            {"text_css": "text-primary"},
        )
        assert "text-primary" in ctx["cell_css"].split()
        assert "text-primary" in ctx["header_cell_css"].split()
