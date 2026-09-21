import pytest

from wagtail_daisIE.blocks.content import ALL_CONTENT_BLOCKS
from wagtail_daisIE.blocks.feedback import (
    AlertBlock,
    LoadingBlock,
    ProgressBlock,
    RadialProgressBlock,
    StatusBlock,
    StepsBlock,
    ToastBlock,
    TooltipBlock,
)
from wagtail_daisIE.blocks.inputs import (
    CheckboxBlock,
    FieldsetBlock,
    FileInputBlock,
    InputBlock,
    RadioBlock,
    RangeBlock,
    RatingBlock,
    SelectBlock,
    TextareaBlock,
    ToggleBlock,
)


pytestmark = pytest.mark.django_db


def _render(block, value):
    return block.render(value)


class TestRegistration:
    def test_all_blocks_are_registered(self):
        names = [name for name, _block in ALL_CONTENT_BLOCKS]
        for expected in (
            "alert",
            "status",
            "progress",
            "radial_progress",
            "loading",
            "toast",
            "modal",
            "tooltip",
            "steps",
            "input",
            "textarea",
            "select",
            "checkbox",
            "toggle",
            "radio",
            "range",
            "rating",
            "file",
            "fieldset",
        ):
            assert expected in names


class TestFeedbackBlocks:
    def test_alert(self):
        html = _render(
            AlertBlock(),
            {
                "content": "<p>Heads up</p>",
                "color": "alert-error",
                "design": {},
                "audience": {},
            },
        )
        assert 'role="alert"' in html
        assert "alert-error" in html
        assert "Heads up" in html

    def test_status(self):
        html = _render(
            StatusBlock(),
            {
                "label": "Online",
                "color": "status-success",
                "size": "status-sm",
                "design": {},
                "audience": {},
            },
        )
        assert "status" in html
        assert "status-success" in html
        assert "Online" in html

    def test_progress(self):
        html = _render(
            ProgressBlock(),
            {
                "value": 150,
                "maximum": 100,
                "color": "progress-primary",
                "design": {},
                "audience": {},
            },
        )
        assert "<progress" in html
        assert 'value="100"' in html
        assert "progress-primary" in html

    def test_radial_progress(self):
        html = _render(
            RadialProgressBlock(),
            {
                "value": 70,
                "size": 5,
                "thickness": "0.25rem",
                "design": {},
                "audience": {},
            },
        )
        assert "radial-progress" in html
        assert "--value:70" in html
        assert 'role="progressbar"' in html

    def test_loading(self):
        html = _render(
            LoadingBlock(),
            {
                "style": "loading-dots",
                "size": "loading-lg",
                "label": "Saving",
                "design": {},
                "audience": {},
            },
        )
        assert "loading loading-dots loading-lg" in html
        assert 'role="status"' in html
        assert 'aria-label="Saving"' in html

    def test_toast(self):
        html = _render(
            ToastBlock(),
            {
                "content": "<p>Saved</p>",
                "color": "alert-success",
                "position": "toast-end toast-bottom",
                "design": {},
                "audience": {},
            },
        )
        assert "toast" in html
        assert "alert-success" in html
        assert "Saved" in html

    def test_tooltip(self):
        html = _render(
            TooltipBlock(),
            {
                "text": "More info",
                "content": "Hover",
                "position": "tooltip-right",
                "color": "",
                "design": {},
                "audience": {},
            },
        )
        assert "tooltip-right" in html
        assert 'data-tip="More info"' in html

    def test_steps(self):
        html = _render(
            StepsBlock(),
            {
                "steps": ["One", "Two", "Three"],
                "active": 2,
                "direction": "steps-horizontal",
                "color": "step-primary",
                "design": {},
                "audience": {},
            },
        )
        assert "steps" in html
        assert html.count("step-primary") == 2
        assert "Three" in html


class TestInputBlocks:
    def test_input_error_state(self):
        html = _render(
            InputBlock(),
            {
                "label": "Email",
                "input_type": "email",
                "name": "email",
                "error_text": "Required",
                "required": True,
                "design": {},
                "audience": {},
            },
        )
        assert 'type="email"' in html
        assert "validator" in html
        assert 'aria-invalid="true"' in html
        assert 'role="alert"' in html

    def test_textarea(self):
        html = _render(
            TextareaBlock(),
            {
                "label": "Bio",
                "rows": 4,
                "design": {},
                "audience": {},
            },
        )
        assert "<textarea" in html
        assert 'rows="4"' in html
        assert "textarea" in html

    def test_select_options(self):
        html = _render(
            SelectBlock(),
            {
                "label": "Pick",
                "options": "One\nTwo",
                "design": {},
                "audience": {},
            },
        )
        assert html.count("<option") == 2

    def test_checkbox(self):
        html = _render(
            CheckboxBlock(),
            {"label": "Agree", "checked": True, "design": {}, "audience": {}},
        )
        assert 'type="checkbox"' in html
        assert "checkbox" in html
        assert "checked" in html

    def test_toggle(self):
        html = _render(
            ToggleBlock(),
            {"label": "On", "design": {}, "audience": {}},
        )
        assert "toggle" in html
        assert 'role="switch"' in html

    def test_radio(self):
        html = _render(
            RadioBlock(),
            {"label": "Choose", "options": "A,B", "design": {}, "audience": {}},
        )
        assert html.count('type="radio"') == 2

    def test_range(self):
        html = _render(
            RangeBlock(),
            {
                "label": "Size",
                "minimum": 0,
                "maximum": 10,
                "step": 1,
                "value": 4,
                "design": {},
                "audience": {},
            },
        )
        assert 'type="range"' in html
        assert 'max="10"' in html

    def test_rating(self):
        html = _render(
            RatingBlock(),
            {
                "label": "Rate",
                "maximum": 5,
                "value": 3,
                "design": {},
                "audience": {},
            },
        )
        assert html.count("mask-star") == 5
        assert 'value="3"' in html

    def test_file(self):
        html = _render(
            FileInputBlock(),
            {"label": "Upload", "accept": "image/*", "design": {}, "audience": {}},
        )
        assert "file-input" in html
        assert 'accept="image/*"' in html

    def test_fieldset(self):
        html = _render(
            FieldsetBlock(),
            {
                "legend": "Details",
                "description": "Fill in",
                "content": [],
                "design": {},
                "audience": {},
            },
        )
        assert "fieldset-legend" in html
        assert "Details" in html
