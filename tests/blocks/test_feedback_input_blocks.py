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
