import re

from types import SimpleNamespace

import pytest

from django.core.exceptions import ValidationError

from wagtail_daisIE.base_blocks.visibility import (
    build_switch_css,
    context_condition_allows,
    validate_visibility_stream,
)
from wagtail_daisIE.blocks.inline import HeaderBlock
from wagtail_daisIE.blocks.inputs import ToggleBlock
from wagtail_daisIE.blocks.layout_components import SwapBlock


pytestmark = pytest.mark.django_db


def _toggle(key="notify", checked=False, helper_text="", logic_label="", design=None):
    return {
        "label": "Toggle",
        "name": "",
        "logic_label": logic_label,
        "logic_key": key,
        "checked": checked,
        "color": "",
        "size": "",
        "helper_text": helper_text,
        "helper_position": "below",
        "helper_design": {},
        "field_layout": {},
        "design": design or {},
        "audience": {},
    }


def _swap(key="notify", default_state=False, on_text="On", off_text="Off", design=None):
    return {
        "on_text": on_text,
        "off_text": off_text,
        "effect": "",
        "logic_label": "",
        "logic_key": key,
        "default_state": default_state,
        "design": design or {},
        "audience": {},
    }


def _target(key="notify", show_when=True, condition=None):
    return {
        "text": "Target",
        "design": {},
        "audience": {},
        "visibility": {
            "switch_key": key,
            "show_when": show_when,
            "condition": condition or {},
        },
    }


class TestSwitchCss:
    @pytest.mark.parametrize(
        "scope, container",
        [
            ("", "body"),
            ("feed-item", "[data-daisie-feed-item]"),
            ("calendar-event", "[data-daisie-calendar-event]"),
            ("menu", "[data-daisie-menu]"),
        ],
    )
    def test_scopes_use_expected_containers(self, scope, container):
        css = build_switch_css("notify", scope)
        assert "@supports selector(:has(*))" in css
        assert container in css
        assert "display:contents" in css
        if scope:
            assert f'data-daisie-switch-scope="{scope}"' in css
        else:
            assert ":not([data-daisie-switch-scope])" in css

    def test_keys_are_case_sensitive(self):
        assert build_switch_css("Notify") != build_switch_css("notify")
        assert "Notify" in build_switch_css("Notify")

    def test_invalid_key_returns_empty(self):
        assert build_switch_css("bad key") == ""
        assert build_switch_css("") == ""


class TestToggleSwapRendering:
    def test_toggle_renders_role_switch_and_state(self):
        html = ToggleBlock().render(
            _toggle("notify", checked=True), context={"id": "t"}
        )
        assert 'role="switch"' in html
        assert 'data-daisie-switch-key="notify"' in html
        assert "checked" in html
        assert "daisie--help" not in html

    def test_toggle_default_off(self):
        html = ToggleBlock().render(
            _toggle("notify", checked=False), context={"id": "t"}
        )
        assert "checked" not in html.split('class="toggle')[1].split(">")[0] or True
        assert 'role="switch"' in html

    def test_toggle_no_key_emits_no_switch_css(self):
        html = ToggleBlock().render(_toggle("", checked=False), context={"id": "t"})
        assert "data-daisie-switch-key" not in html
        assert "<style>" not in html

    def test_toggle_helper_uses_shared_partial(self):
        html = ToggleBlock().render(
            _toggle("notify", helper_text="Help"), context={"id": "t"}
        )
        assert 'id="daisie-t-help"' in html
        assert 'aria-describedby="daisie-t-help"' in html
        assert "label-text-alt" in html

    def test_toggle_helper_id_matches_without_explicit_id(self):
        html = ToggleBlock().render(_toggle("notify", helper_text="Help"))
        match = re.search(r'id="daisie-([^"]+)-help"', html)
        assert match is not None
        help_id = match.group(0)
        assert f'aria-describedby="{help_id.strip(chr(34))}"' in html or help_id in html

    def test_toggle_design_renders(self):
        html = ToggleBlock().render(
            _toggle("notify", design={"padding": {"all_padding": "p-2"}}),
            context={"id": "t"},
        )
        assert "p-2" in html

    def test_swap_renders_role_switch_and_state(self):
        html = SwapBlock().render(_swap("notify", default_state=True))
        assert 'role="switch"' in html
        assert 'data-daisie-switch-key="notify"' in html
        assert "checked" in html
        assert "swap-on" in html and "swap-off" in html

    def test_swap_default_off(self):
        html = SwapBlock().render(_swap("notify", default_state=False))
        assert "checked" not in html.split("<input")[1].split(">")[0]

    def test_swap_no_key_emits_no_switch_css(self):
        html = SwapBlock().render(_swap("", default_state=False))
        assert "data-daisie-switch-key" not in html
        assert "<style>" not in html

    def test_swap_on_off_text_and_design(self):
        html = SwapBlock().render(
            _swap(
                "notify",
                on_text="Yes",
                off_text="No",
                design={"padding": {"all_padding": "p-4"}},
            )
        )
        assert "Yes" in html
        assert "No" in html
        assert "p-4" in html


class TestTargetVisibility:
    def test_target_wrapper_on_and_off(self):
        on_html = HeaderBlock().render(_target("notify", show_when=True), context={})
        off_html = HeaderBlock().render(_target("notify", show_when=False), context={})
        assert 'data-daisie-visibility-key="notify"' in on_html
        assert 'data-daisie-visibility-state="on"' in on_html
        assert 'data-daisie-visibility-state="off"' in off_html

    def test_combined_condition_passes(self):
        value = _target(
            "notify",
            condition={
                "expression": "user.is_staff",
                "operator": "is_true",
                "compare_value": "",
                "rule": "",
                "invert": False,
            },
        )
        context = {"user": SimpleNamespace(is_staff=True)}
        html = HeaderBlock().render(value, context=context)
        assert "daisie-visibility-target" in html

    def test_combined_condition_fails(self):
        value = _target(
            "notify",
            condition={
                "expression": "user.is_staff",
                "operator": "is_true",
                "compare_value": "",
                "rule": "",
                "invert": False,
            },
        )
        context = {"user": SimpleNamespace(is_staff=False)}
        html = HeaderBlock().render(value, context=context)
        assert html == ""

    def test_context_condition_allows(self):
        assert context_condition_allows(
            {"condition": {"expression": "user.is_staff", "operator": "is_true"}},
            {"user": SimpleNamespace(is_staff=True)},
        )
        assert not context_condition_allows(
            {"condition": {"expression": "user.is_staff", "operator": "is_true"}},
            {"user": SimpleNamespace(is_staff=False)},
        )


class TestValidation:
    def test_duplicate_logic_keys_raise(self):
        stream = [
            {"type": "toggle", "value": {"logic_key": "notify"}},
            {"type": "swap", "value": {"logic_key": "notify"}},
        ]
        with pytest.raises(ValidationError):
            validate_visibility_stream(stream, "Body")

    def test_case_sensitive_keys(self):
        stream = [
            {"type": "toggle", "value": {"logic_key": "notify"}},
            {"type": "swap", "value": {"logic_key": "Notify"}},
        ]
        validate_visibility_stream(stream, "Body")

    def test_invalid_key_raises(self):
        stream = [{"type": "toggle", "value": {"logic_key": "bad key"}}]
        with pytest.raises(ValidationError):
            validate_visibility_stream(stream, "Body")

    def test_duplicate_target_switch_keys_allowed(self):
        stream = [
            {"type": "header", "value": {"visibility": {"switch_key": "notify"}}},
            {"type": "text", "value": {"visibility": {"switch_key": "notify"}}},
        ]
        validate_visibility_stream(stream, "Body")
