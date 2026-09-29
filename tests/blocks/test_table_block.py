from pathlib import Path

import wagtail_daisIE

from wagtail_daisIE.base_blocks.css import build_table_css
from wagtail_daisIE.blocks.table import TableBlock


class TestBuildTableCss:
    def test_border_spacing_and_empty_design(self):
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
        assert "border-spacing-8" in css and "border-spacing-x-4" in css
        assert not any(cls.startswith("border-spacing-y") for cls in css)
        assert build_table_css({}) == "" and build_table_css(None) == ""

    def test_missing_spacing_and_pin_modifiers(self):
        assert build_table_css({"table_border_spacing": None}) == "table"
        css = build_table_css(
            {"table_pin_rows": True, "table_pin_columns": True}
        ).split()
        assert "table-pin-rows" in css and "table-pin-cols" in css


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

    def test_renders_content_design_and_unset_flags(self):
        block = TableBlock()
        html = block.render(self._value(block))
        for token in (
            "<table",
            "table-sm",
            "border-separate",
            "border-spacing-2",
            "table-zebra",
            "table-pin-rows",
            "table-pin-cols",
            "text-base-content",
            "Alice",
            "<th",
        ):
            assert token in html, token

        # A False flag must contribute nothing, not a bare class.
        value = self._value(block)
        appearance = dict(value["design"]["table_appearance"])
        appearance.update(
            {
                "table_zebra_rows": False,
                "table_pin_rows": False,
                "table_pin_columns": False,
            }
        )
        value["design"]["table_appearance"] = appearance
        html = block.render(value)
        assert "table-zebra" not in html
        assert "table-pin-rows" not in html and "table-pin-cols" not in html
        assert "table-sm" in html


class TestJITInputCSS:
    def test_input_css_declares_daisyui_and_extended_typography(self):
        """The JIT source must ship daisyUI and the extended type scale."""
        source = (
            Path(wagtail_daisIE.__file__).parent / "tailwind" / "input.css"
        ).read_text()
        assert "daisyui" in source
        assert "--text-42xl" in source
