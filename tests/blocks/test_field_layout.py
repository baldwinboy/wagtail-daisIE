from wagtail_daisIE.base_blocks import (
    FieldGroupLayoutBlock,
    FieldLayoutBlock,
    FieldLayoutMixin,
    FieldOptionLayoutBlock,
    FieldPartLayoutBlock,
)
from wagtail_daisIE.base_blocks.css import build_layout_item_css
from wagtail_daisIE.base_blocks.field_layout import (
    build_field_group_css,
    build_field_layout_context,
    build_field_option_context,
    build_field_part_context,
    build_field_part_css,
)


def test_field_layout_block_structure():
    block = FieldLayoutBlock()

    assert set(block.child_blocks) == {
        "layout",
        "input",
        "label",
        "help",
        "error",
        "options",
    }
    assert set(FieldGroupLayoutBlock().child_blocks) == {"layout", "size"}
    assert set(FieldOptionLayoutBlock().child_blocks) == {"input", "label"}
    assert set(FieldPartLayoutBlock().child_blocks) == {
        "visibility",
        "placement",
        "max_lines",
        "item",
    }


def test_field_layout_defaults_for_row_and_column():
    row = build_field_layout_context({"layout": {"layout": "row"}})

    assert row["field_layout_css"] == "flex flex-row grow"
    assert row["field_input_css"] == "order-first"
    assert row["field_label_css"] == "order-none"
    assert row["field_help_css"] == "order-last"
    assert row["field_error_css"] == ""

    column = build_field_layout_context({"layout": {"layout": "column"}})

    assert column["field_layout_css"] == "flex flex-col grow"
    assert column["field_label_css"] == "order-first"
    assert column["field_input_css"] == "order-none"
    assert column["field_help_css"] == "order-last"


def test_field_layout_defaults_for_grid():
    context = build_field_layout_context({"layout": {"layout": "grid", "columns": 2}})

    assert context["field_layout_css"] == "grid grow grid-cols-1 sm:grid-cols-2"
    assert context["field_layout_grid"] is True
    assert context["field_input_css"] == ""
    assert context["field_label_css"] == ""
    assert context["field_help_css"] == ""


def test_field_part_explicit_placement_and_visibility():
    context = build_field_layout_context(
        {
            "layout": {"layout": "row"},
            "input": {"placement": "end", "visibility": "sr-only"},
            "label": {"placement": "start", "visibility": "hidden"},
            "help": {"placement": "middle", "max_lines": 2},
        }
    )

    assert context["field_input_css"] == "sr-only order-last"
    assert context["field_input_sr_only"] is True
    assert context["field_label_css"] == "hidden order-first"
    assert context["field_label_hidden"] is True
    assert context["field_help_css"] == "order-none line-clamp-2"
    assert context["field_help_sr_only"] is False


def test_field_part_max_lines_is_only_applied_to_text_parts():
    help_context = build_field_part_context(
        {"placement": "end", "max_lines": 3}, layout="row", part="help"
    )
    input_context = build_field_part_context(
        {"placement": "end", "max_lines": 3}, layout="row", part="input"
    )

    assert help_context["css"] == "order-last line-clamp-3"
    assert input_context["css"] == "order-last"


def test_field_part_item_order_overrides_placement():
    css = build_field_part_css(
        {
            "placement": "start",
            "item": {"order": "order-2"},
        },
        layout="row",
        part="input",
    )

    assert css == "order-2"


def test_field_layout_grid_part_placement():
    context = build_field_layout_context(
        {
            "layout": {"layout": "grid", "columns": 2},
            "input": {
                "placement": "grid",
                "item": {
                    "grid_column_start": "col-start-2",
                    "grid_column_span": "col-span-2",
                    "grid_row_start": "row-start-1",
                    "grid_row_span": "row-span-2",
                    "justify_self": "justify-self-end",
                    "grow": "grow",
                },
            },
        }
    )

    assert context["field_input_css"].split() == [
        "grow",
        "col-start-2",
        "col-span-2",
        "row-start-1",
        "row-span-2",
        "justify-self-end",
    ]


def test_field_group_layout_css():
    css = build_field_group_css(
        {
            "layout": {
                "layout": "grid",
                "columns": 2,
                "gap": "gap-4",
                "justify": "justify-between",
                "align": "items-center",
            },
            "size": {
                "size": "size-5",
                "width": {"max_width": "max-w-sm"},
                "height": {"max_height": "max-h-40"},
                "scroll": "overflow-y-auto",
            },
        }
    )

    tokens = css.split()
    assert {
        "grid",
        "grow",
        "grid-cols-1",
        "sm:grid-cols-2",
        "gap-4",
        "justify-between",
        "items-center",
        "size-5",
        "max-w-sm",
        "max-h-40",
        "overflow-y-auto",
    }.issubset(set(tokens))


def test_field_option_layout_context():
    context = build_field_option_context(
        {
            "input": {"placement": "end", "visibility": "sr-only"},
            "label": {"placement": "start"},
        },
        layout="row",
    )

    assert context["option_input_css"] == "sr-only order-last"
    assert context["option_input_sr_only"] is True
    assert context["option_label_css"] == "order-first"
    assert context["option_label_hidden"] is False


def test_field_layout_mixin_injects_context():
    class _Base:
        def get_context(self, value, parent_context=None):
            return {"base": True, "value": value}

    class _Block(FieldLayoutMixin, _Base):
        pass

    context = _Block().get_context({"field_layout": {"layout": {"layout": "column"}}})

    assert context["base"] is True
    assert context["field_label_css"] == "order-first"
    assert context["field_input_css"] == "order-none"
    assert context["field_help_css"] == "order-last"


def test_layout_item_grid_starts():
    css = build_layout_item_css(
        {
            "grid_column_start": "col-start-2",
            "grid_row_start": "row-start-3",
            "grid_column_span": "col-span-2",
            "grid_row_span": "row-span-2",
            "justify_self": "justify-self-end",
        },
        grid=True,
    )

    assert css.split() == [
        "col-start-2",
        "col-span-2",
        "row-start-3",
        "row-span-2",
        "justify-self-end",
    ]
    assert (
        build_layout_item_css(
            {
                "grid_column_start": "col-start-2",
                "grid_column_span": "col-span-2",
            },
            grid=False,
        )
        == ""
    )


def test_field_group_layout_normalises_legacy_flat_value():
    from wagtail_daisIE.base_blocks import FieldGroupLayoutBlock
    from wagtail_daisIE.base_blocks.field_layout import build_field_group_context

    value = FieldGroupLayoutBlock().to_python({"layout": "row", "gap": "gap-4"})
    context = build_field_group_context(value)
    assert "flex flex-row grow" in context["field_group_css"]
    assert "gap-4" in context["field_group_css"]
