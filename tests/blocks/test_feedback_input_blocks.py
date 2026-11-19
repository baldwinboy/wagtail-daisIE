import re

import pytest

from wagtail_daisIE.blocks.feedback import (
    ProgressBlock,
    RadialProgressBlock,
    StepsBlock,
)
from wagtail_daisIE.blocks.inputs import (
    AutocompleteSelectMultipleBlock,
    CheckboxBlock,
    InputBlock,
    RadioBlock,
    RatingBlock,
    SelectBlock,
    ToggleBlock,
)


pytestmark = pytest.mark.django_db


class TestFeedbackBlocks:
    def test_progress_and_radial_progress(self):
        html = ProgressBlock().render(
            {
                "value": 150,
                "maximum": 100,
                "color": "progress-primary",
                "design": {},
                "audience": {},
            }
        )
        assert "<progress" in html and 'value="100"' in html
        assert "progress-primary" in html

        html = RadialProgressBlock().render(
            {
                "value": 70,
                "size": 5,
                "thickness": "0.25rem",
                "design": {},
                "audience": {},
            }
        )
        assert "radial-progress" in html
        assert "--value:70" in html and 'role="progressbar"' in html

    def test_steps_marks_active_steps(self):
        html = StepsBlock().render(
            {
                "steps": ["One", "Two", "Three"],
                "active": 2,
                "direction": "steps-horizontal",
                "color": "step-primary",
                "design": {},
                "audience": {},
            }
        )
        assert "steps" in html
        assert html.count("step-primary") == 2
        assert "Three" in html


class TestInputBlocks:
    def test_input_error_state(self):
        html = InputBlock().render(
            {
                "label": "Email",
                "input_type": "email",
                "name": "email",
                "error_text": "Required",
                "required": True,
                "design": {},
                "audience": {},
            }
        )
        assert 'type="email"' in html
        assert "validator" in html
        assert 'aria-invalid="true"' in html and 'role="alert"' in html

    def test_select_radio_and_rating(self):
        html = SelectBlock().render(
            {"label": "Pick", "options": "One\nTwo", "design": {}, "audience": {}}
        )
        assert html.count("<option") == 2

        html = RadioBlock().render(
            {"label": "Choose", "options": "A,B", "design": {}, "audience": {}}
        )
        assert html.count('type="radio"') == 2

        html = RatingBlock().render(
            {
                "label": "Rate",
                "maximum": 5,
                "value": 3,
                "design": {},
                "audience": {},
            }
        )
        assert html.count("mask-star") == 5 and 'value="3"' in html

    def test_autocomplete_block_design_and_options(self):
        html = AutocompleteSelectMultipleBlock().render(
            {
                "label": "Durations",
                "name": "durations",
                "options_source": "",
                "options": "5-10/5",
                "selected": "5",
                "color": "input-primary",
                "required": True,
                "helper_text": "Pick some",
                "design": {},
                "audience": {},
            }
        )
        assert html.count("<option") == 2
        assert 'value="5" selected' in html
        assert "data-daisyui-autocomplete" in html
        assert "input-primary" in html
        assert "Pick some" in html


def _helper_span(html):
    match = re.search(r'<span\b[^>]*id="[^"]+-help"[^>]*>', html)
    assert match is not None
    return match


def _helper_classes(span):
    match = re.search(r'class="([^"]*)"', span.group(0))
    assert match is not None
    return match.group(1).split()


@pytest.mark.parametrize("block_class", [CheckboxBlock, ToggleBlock])
class TestCheckboxToggleHelper:
    def test_helper_defaults_to_below_label(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "design": {},
                "audience": {},
            }
        )

        span = _helper_span(html)
        classes = _helper_classes(span)
        assert "label-text-alt" in classes
        assert "text-sm" in classes
        assert "block" in classes
        assert span.start() > html.index("</label>")
        assert 'aria-describedby="daisie-' in html
        assert '<p class="label"' not in html

    @pytest.mark.parametrize("position", ["above", "below", "inline"])
    def test_helper_positions(self, block_class, position):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "helper_position": position,
                "design": {},
                "audience": {},
            }
        )

        span = _helper_span(html)
        classes = _helper_classes(span)
        label_start = html.index("<label")
        label_end = html.index("</label>")

        if position == "above":
            assert span.start() < label_start
            assert "block" in classes
        elif position == "below":
            assert span.start() > label_end
            assert "block" in classes
        else:
            assert label_start < span.start() < label_end
            assert "block" not in classes

    def test_helper_design_classes_and_background_render(self, block_class):
        block = block_class()
        value = block.to_python(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "helper_design": {
                    "typography": {"font_weight": "font-bold"},
                    "padding": {"all_padding": "p-2"},
                    "background": [
                        {
                            "type": "layer",
                            "value": {"layer_type": "solid", "color": "#123456"},
                        }
                    ],
                },
                "design": {},
                "audience": {},
            }
        )
        html = block.render(value)

        span = _helper_span(html).group(0)
        assert "font-bold" in span
        assert "p-2" in span
        assert 'style="background: #123456"' in span

    def test_helper_markup_is_absent_without_helper_text(self, block_class):
        html = block_class().render({"label": "Notify", "design": {}, "audience": {}})

        assert "-help" not in html
        assert "aria-describedby" not in html


def _part_classes(html, part):
    match = re.search(rf'<div class="([^"]*)" data-daisie-field-part="{part}">', html)
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("block_class", [CheckboxBlock, ToggleBlock])
class TestCheckboxToggleFieldLayout:
    def test_row_defaults(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {"layout": {"layout": "row"}},
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "flex flex-row grow" in html
        assert _part_classes(html, "input") == "order-first"
        assert _part_classes(html, "label") == "order-none"
        assert _part_classes(html, "help") == "order-last"
        assert 'id="daisie-cb"' in html
        assert 'for="daisie-cb"' in html

    def test_column_defaults(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {"layout": {"layout": "column"}},
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "flex flex-col grow" in html
        assert _part_classes(html, "label") == "order-first"
        assert _part_classes(html, "input") == "order-none"
        assert _part_classes(html, "help") == "order-last"

    def test_explicit_part_placement(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "input": {"placement": "end"},
                    "label": {"placement": "start"},
                    "help": {"placement": "middle"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert _part_classes(html, "input") == "order-last"
        assert _part_classes(html, "label") == "order-first"
        assert _part_classes(html, "help") == "order-none"

    def test_grid_placement(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "grid", "columns": 2},
                    "input": {
                        "placement": "grid",
                        "item": {
                            "grid_column_start": "col-start-2",
                            "grid_column_span": "col-span-2",
                            "grid_row_start": "row-start-1",
                            "grid_row_span": "row-span-2",
                            "justify_self": "justify-self-end",
                        },
                    },
                    "label": {
                        "item": {
                            "grid_row_span": "row-span-2",
                            "align_self": "self-center",
                        }
                    },
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        input_classes = _part_classes(html, "input").split()
        label_classes = _part_classes(html, "label").split()
        assert "grid grow grid-cols-1 sm:grid-cols-2" in html
        assert {
            "col-start-2",
            "col-span-2",
            "row-start-1",
            "row-span-2",
            "justify-self-end",
        }.issubset(set(input_classes))
        assert {"row-span-2", "self-center"}.issubset(set(label_classes))
        assert "order-first" not in input_classes
        assert "order-first" not in label_classes

    def test_visually_hidden_input_keeps_label_and_help(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "input": {"visibility": "sr-only"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "sr-only" in _part_classes(html, "input")
        assert _part_classes(html, "label") == "order-none"
        assert _part_classes(html, "help") == "order-last"
        assert 'for="daisie-cb"' in html
        assert 'aria-describedby="daisie-cb-help"' in html

    def test_hidden_label_uses_aria_label_and_omits_label(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "label": {"visibility": "hidden"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "Notify" not in html or 'data-daisie-field-part="label"' not in html
        assert 'data-daisie-field-part="label"' not in html
        assert 'aria-label="Notify"' in html
        assert 'aria-describedby="daisie-cb-help"' in html

    def test_sr_only_label_keeps_accessibility(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "label": {"visibility": "sr-only"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "sr-only" in _part_classes(html, "label")
        assert 'for="daisie-cb"' in html

    def test_hidden_help_omits_helper_and_aria(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "help": {"visibility": "hidden"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert 'data-daisie-field-part="help"' not in html
        assert "aria-describedby" not in html

    def test_hidden_input_still_renders(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "input": {"visibility": "hidden"},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert 'data-daisie-field-part="input"' in html
        assert "hidden" in _part_classes(html, "input")
        assert 'type="checkbox"' in html

    def test_max_lines_on_text_parts(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {
                    "layout": {"layout": "row"},
                    "label": {"max_lines": 2},
                    "help": {"max_lines": 3},
                },
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "line-clamp-2" in _part_classes(html, "label")
        assert "line-clamp-3" in _part_classes(html, "help")

    def test_helper_design_still_renders_in_layout_mode(self, block_class):
        block = block_class()
        value = block.to_python(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "field_layout": {"layout": {"layout": "column"}},
                "helper_design": {
                    "typography": {"font_weight": "font-bold"},
                    "padding": {"all_padding": "p-2"},
                },
                "design": {},
                "audience": {},
            }
        )
        html = block.render(value, context={"id": "cb"})
        span = re.search(r'<span\b[^>]*id="daisie-cb-help"[^>]*>', html)
        assert span is not None
        classes = re.search(r'class="([^"]*)"', span.group(0)).group(1).split()
        assert "font-bold" in classes
        assert "p-2" in classes

    def test_no_layout_keeps_legacy_markup(self, block_class):
        html = block_class().render(
            {
                "label": "Notify",
                "helper_text": "Weekly digest",
                "design": {},
                "audience": {},
            },
            context={"id": "cb"},
        )

        assert "data-daisie-field-part" not in html
        assert '<label class="label flex w-full cursor-pointer' in html
        assert 'aria-describedby="daisie-cb-help"' in html


class TestToggleVisibilityConsistency:
    def test_toggle_helper_id_matches_block_id(self):
        html = ToggleBlock().render(
            {
                "label": "Notify",
                "helper_text": "Help",
                "design": {},
                "audience": {},
            },
            context={"id": "t"},
        )
        assert 'id="daisie-t-help"' in html
        assert 'aria-describedby="daisie-t-help"' in html

    def test_toggle_helper_id_without_explicit_id(self):
        html = ToggleBlock().render(
            {
                "label": "Notify",
                "helper_text": "Help",
                "design": {},
                "audience": {},
            }
        )
        match = re.search(r'id="daisie-([^"]+)-help"', html)
        assert match is not None
        help_id = match.group(0).split('"')[1]
        assert f'aria-describedby="{help_id}"' in html

    def test_toggle_design_renders(self):
        html = ToggleBlock().render(
            {
                "label": "Notify",
                "color": "toggle-primary",
                "size": "toggle-sm",
                "design": {"padding": {"all_padding": "p-2"}},
                "audience": {},
            },
            context={"id": "t"},
        )
        assert "toggle-primary" in html
        assert "toggle-sm" in html
        assert "p-2" in html

    def test_swap_renders_on_off_and_design(self):
        from wagtail_daisIE.blocks.layout_components import SwapBlock

        html = SwapBlock().render(
            {
                "on_text": "Yes",
                "off_text": "No",
                "effect": "swap-rotate",
                "logic_key": "notify",
                "default_state": True,
                "design": {"padding": {"all_padding": "p-3"}},
                "audience": {},
            }
        )
        assert "Yes" in html
        assert "No" in html
        assert "swap-rotate" in html
        assert 'role="switch"' in html
        assert "checked" in html
        assert "p-3" in html
