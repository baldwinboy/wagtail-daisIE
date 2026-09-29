import pytest

from wagtail_daisIE.blocks.feedback import (
    ProgressBlock,
    RadialProgressBlock,
    StepsBlock,
)
from wagtail_daisIE.blocks.inputs import (
    InputBlock,
    RadioBlock,
    RatingBlock,
    SelectBlock,
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
