from pathlib import Path

import wagtail_daisIE

from wagtail_daisIE.base_blocks.css import build_table_css
from wagtail_daisIE.base_blocks.table import TableBorderSpacingBlock
from wagtail_daisIE.blocks.table import TableBlock


class TestBuildTableCss:
    def test_border_spacing_is_flattened(self):
        css = build_table_css(
            {
                "table_border_spacing": {
                    "all_spacing": 8,
                    "horizontal": 4,
                    "vertical": None,
                }
            }
        ).split()
        assert "table" in css
        assert "border-spacing-8" in css
        assert "border-spacing-x-4" in css
        assert not any(cls.startswith("border-spacing-y") for cls in css)

    def test_missing_border_spacing_does_not_raise(self):
        assert build_table_css({"table_border_spacing": None}) == "table"

    def test_pin_modifiers_use_daisyui_names(self):
        css = build_table_css(
            {"table_pin_rows": True, "table_pin_columns": True}
        ).split()
        assert "table-pin-rows" in css
        assert "table-pin-cols" in css


class TestTableBorderSpacingBlock:
    def test_fields_are_capped_at_the_tailwind_scale(self):
        block = TableBorderSpacingBlock()
        for name in ("all_spacing", "horizontal", "vertical"):
            assert block.child_blocks[name].field.max_value == 96


class TestTableBlockRender:
    def _value(self, block):
        return block.to_python(
            {
                "content": {
                    "table_header_choice": "row",
                    "first_row_is_table_header": True,
                    "first_col_is_header": False,
                    "data": [["Name", "Job"], ["Alice", "Designer"]],
                    "table_caption": "People",
                },
                "cell_design": {"typography": {"text_color": "text-base-content"}},
                "design": {
                    "table_appearance": {
                        "table_size": "table-sm",
                        "table_border_style": "border-separate",
                        "table_border_spacing": {
                            "all_spacing": 2,
                            "horizontal": None,
                            "vertical": None,
                        },
                        "table_zebra_rows": True,
                        "table_pin_rows": True,
                        "table_pin_columns": True,
                    }
                },
            }
        )

    def test_renders_content_and_design(self):
        block = TableBlock()
        html = block.render(self._value(block))

        assert "<table" in html
        assert "table-sm" in html
        assert "border-separate" in html
        assert "border-spacing-2" in html
        assert "table-zebra" in html
        assert "table-pin-rows" in html
        assert "table-pin-cols" in html
        assert "text-base-content" in html
        assert "Alice" in html


class TestBorderSpacingSafelist:
    def test_source_css_safelists_numeric_border_spacing(self):
        source = (
            Path(wagtail_daisIE.__file__).parent
            / "static"
            / "wagtail_daisIE"
            / "css"
            / "source.css"
        ).read_text()
        assert "border-spacing-{0..96}" in source
        assert "border-spacing-x-{0..96}" in source
        assert "border-spacing-y-{0..96}" in source
