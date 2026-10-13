from wagtail_daisIE.base_blocks.css import build_design_css


def test_tray_css_composes_layout_and_alignment():
    css = build_design_css(
        {
            "layout": "row",
            "wrap": "flex-wrap",
            "justify": "justify-center",
            "align": "items-center",
            "gap": "gap-2",
        }
    )
    assert {
        "flex",
        "flex-row",
        "grow",
        "flex-wrap",
        "justify-center",
        "items-center",
        "gap-2",
    } <= set(css.split())


def test_item_css_includes_shape_and_typography():
    css = build_design_css(
        {"shape": "rounded-full", "typography": {"font_weight": "font-bold"}}
    )
    tokens = set(css.split())
    assert "rounded-full" in tokens
    assert "font-bold" in tokens
