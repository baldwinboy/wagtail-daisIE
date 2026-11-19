import re

import pytest

from wagtail_daisIE.blocks.cards import CardBlock
from wagtail_daisIE.dynamic.action_blocks import ActionBlock, ActionFormBlock


pytestmark = pytest.mark.django_db


CARD_DESIGN = {
    "padding": {"all_padding": "p-8"},
    "border": {"border_width": 2, "border_style": "solid"},
    "background": [
        {"type": "layer", "value": {"layer_type": "solid", "color": "#ff0000"}}
    ],
}

BUTTON_DESIGN = {
    "button_appearance": {"normal": {"color": "btn-secondary"}},
    "background": [
        {"type": "layer", "value": {"layer_type": "solid", "color": "#00ff00"}}
    ],
}


def _action_value():
    return {
        "action": "demo",
        "target_expression": "",
        "button": {
            "text": "Run",
            "design": BUTTON_DESIGN,
            "confirm": {
                "title": "Confirm",
                "text": "Continue?",
                "confirm_label": "Yes",
            },
            "audience": {},
        },
    }


def test_action_form_resolves_url():
    context = ActionFormBlock().get_context(
        {"action": "demo", "fields": [], "button": {}, "behaviour": "inline"}
    )
    assert context["action_url"] == "/daisie/actions/demo/"


def test_action_inside_card_ignores_container_design():
    card = CardBlock()
    value = card.to_python(
        {
            "design": CARD_DESIGN,
            "audience": {},
            "content": [{"type": "action", "value": _action_value()}],
        }
    )
    html = card.render(value)

    # The card applies its design; the action form must not inherit it.
    assert "p-8" in html

    form_tag = re.search(r"<form[^>]*>", html)
    assert form_tag is not None
    form = form_tag.group(0)
    assert 'class="inline-block"' in form
    assert "p-8" not in form
    assert "border-2" not in form
    assert "border-solid" not in form
    assert "style=" not in form

    trigger_tag = re.search(r'<a[^>]*href="#daisie-action-confirm-[^"]*"[^>]*>', html)
    assert trigger_tag is not None
    trigger = trigger_tag.group(0)
    assert "btn-secondary" in trigger
    assert "background: #00ff00" in trigger


def _input_field(label, design=None):
    return {
        "type": "input",
        "value": {
            "label": label,
            "input_type": "text",
            "design": design or {},
            "audience": {},
        },
    }


def _render_action_form(fields, container_design):
    card = CardBlock()
    value = card.to_python(
        {
            "design": CARD_DESIGN,
            "audience": {},
            "content": [
                {
                    "type": "action_form",
                    "value": {
                        "action": "demo",
                        "target_expression": "",
                        "fields": fields,
                        "button": {"text": "Save", "design": {}, "audience": {}},
                        "behaviour": "inline",
                        "container_design": container_design,
                    },
                }
            ],
        }
    )
    return card.render(value, context={"container_css": "p-4"})


def test_action_form_container_design_applies_only_to_form():
    form_design = {
        "padding": {"all_padding": "p-6"},
        "background": [
            {"type": "layer", "value": {"layer_type": "solid", "color": "#abcdef"}}
        ],
    }
    html = _render_action_form([_input_field("Plain")], form_design)

    form_tag = re.search(r"<form[^>]*>", html)
    assert form_tag is not None
    form = form_tag.group(0)
    assert "p-6" in form
    assert 'style="background: #abcdef"' in form
    assert "p-8" not in form
    assert "background: #ff0000" not in form

    fieldset_tag = re.search(r'<fieldset class="([^"]*)"[^>]*>', html)
    assert fieldset_tag is not None
    assert "p-4" in fieldset_tag.group(1)
    assert "p-6" not in fieldset_tag.group(0)
    assert "p-8" not in fieldset_tag.group(0)
    assert "border-2" not in fieldset_tag.group(0)
    assert "style=" not in fieldset_tag.group(0)

    assert html.count("p-6") == 1
    assert html.count("background: #abcdef") == 1


def test_action_form_fields_use_page_default_and_own_design():
    fields = [
        _input_field("Plain"),
        _input_field("Styled", {"padding": {"all_padding": "p-2"}}),
    ]
    html = _render_action_form(fields, {"padding": {"all_padding": "p-6"}})

    fieldsets = re.findall(r'<fieldset class="([^"]*)"[^>]*>', html)
    assert len(fieldsets) == 2
    assert "p-4" in fieldsets[0]
    assert "p-2" not in fieldsets[0]
    assert "p-4" in fieldsets[1]
    assert "p-2" in fieldsets[1]
    for classes in fieldsets:
        assert "p-6" not in classes
        assert "p-8" not in classes
        assert "border-2" not in classes

    fieldset_tags = re.findall(r'<fieldset class="[^"]*"[^>]*>', html)
    assert all("style=" not in tag for tag in fieldset_tags)


def test_action_button_keeps_menu_defaults_and_own_design():
    block = ActionBlock()
    value = block.to_python(_action_value())
    html = block.render(
        value,
        context={
            "audience_allowed": True,
            "block_css": "p-8 border-2",
            "block_style": "background: #ff0000",
            "menu_default_css": "font-body",
            "menu_default_style": "background: #0000ff",
        },
    )

    form_tag = re.search(r"<form[^>]*>", html)
    assert form_tag is not None
    form = form_tag.group(0)
    assert 'class="inline-block"' in form
    assert "p-8" not in form
    assert "border-2" not in form
    assert "font-body" not in form
    assert "style=" not in form

    trigger_tag = re.search(r'<a[^>]*href="#daisie-action-confirm-[^"]*"[^>]*>', html)
    assert trigger_tag is not None
    trigger = trigger_tag.group(0)
    assert "btn-secondary" in trigger
    assert "font-body" in trigger
    assert "background: #00ff00" in trigger
    assert "background: #0000ff" not in trigger
