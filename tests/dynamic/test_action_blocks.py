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
