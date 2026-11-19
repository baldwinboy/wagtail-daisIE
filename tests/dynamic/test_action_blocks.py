import re

import pytest

from django.contrib.messages import get_messages
from django.shortcuts import redirect
from django.urls import reverse

from wagtail_daisIE.blocks.cards import CardBlock
from wagtail_daisIE.dynamic.action_blocks import (
    ActionBlock,
    ActionButtonBlock,
    ActionConfirmationStreamBlock,
    ActionConfirmStreamBlock,
    ActionFormBlock,
)


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


def _action_value(*, confirm=True):
    button = {
        "text": "Run",
        "design": BUTTON_DESIGN,
        "audience": {},
    }
    if confirm:
        button["confirm"] = {
            "title": "Confirm",
            "text": "Continue?",
            "confirm_label": "Yes",
        }
    return {
        "action": "demo",
        "target_expression": "",
        "button": button,
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


def test_action_without_confirmation_has_no_dialog_or_alert_fields():
    block = ActionBlock()
    value = block.to_python(_action_value(confirm=False))
    assert list(value["button"]["confirm"]) == []

    html = block.render(value, context={"audience_allowed": True})
    assert '<button type="submit"' in html
    assert "daisie-action-confirm-" not in html
    assert 'name="daisie_message"' not in html


def test_legacy_empty_confirmation_dicts_render_nothing():
    button = ActionButtonBlock().to_python(
        {
            "text": "Run",
            "confirm": {"title": "", "text": "", "confirm_label": ""},
            "design": {},
            "audience": {},
        }
    )
    assert len(button["confirm"]) == 0
    assert "daisie-action-confirm-" not in ActionButtonBlock().render(button)

    action = ActionBlock().to_python(
        {
            "action": "demo",
            "button": {"text": "Run", "design": {}, "audience": {}},
            "confirmation": {
                "text": "",
                "icon": "",
                "color": "",
                "style": "",
                "direction": "",
            },
        }
    )
    assert len(action["confirmation"]) == 0
    html = ActionBlock().render(action, context={"audience_allowed": True})
    assert 'name="daisie_message"' not in html


def test_legacy_confirmation_bulk_conversion():
    dialogs = ActionConfirmStreamBlock().bulk_to_python(
        [
            {"title": "Confirm", "text": "", "confirm_label": ""},
            {"title": "", "text": "", "confirm_label": ""},
            None,
        ]
    )
    assert [len(value) for value in dialogs] == [1, 0, 0]

    alerts = ActionConfirmationStreamBlock().bulk_to_python(
        [
            {
                "text": "Saved",
                "icon": "",
                "color": "",
                "style": "",
                "direction": "",
            },
            {"text": "", "icon": "", "color": "", "style": "", "direction": ""},
        ]
    )
    assert [len(value) for value in alerts] == [1, 0]


def test_confirm_dialog_design_appearances_and_accessibility():
    block = ActionButtonBlock()
    value = block.to_python(
        {
            "text": "Delete",
            "confirm": {
                "title": "Delete item?",
                "text": "This cannot be undone.",
                "confirm_label": "Delete",
                "panel_design": {
                    "padding": {"all_padding": "p-4"},
                    "background": [
                        {
                            "type": "layer",
                            "value": {"layer_type": "solid", "color": "#abcdef"},
                        }
                    ],
                },
                "confirm_appearance": {"normal": {"color": "btn-warning"}},
                "cancel_appearance": {"normal": {"color": "btn-ghost"}},
            },
            "design": {},
            "audience": {},
        }
    )
    html = block.render(value)

    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'aria-labelledby="daisie-action-confirm-title-' in html
    assert 'aria-describedby="daisie-action-confirm-text-' in html
    assert "Delete item?" in html
    assert "This cannot be undone." in html
    assert "Delete" in html

    box_tag = re.search(r'<div class="modal-box[^"]*"[^>]*>', html)
    assert box_tag is not None
    assert "p-4" in box_tag.group(0)
    assert 'style="background: #abcdef"' in box_tag.group(0)

    confirm_tag = re.search(r'<button type="submit" class="([^"]*)"', html)
    assert confirm_tag is not None
    assert "btn-warning" in confirm_tag.group(1)

    cancel_tag = re.search(r'<a href="#" class="([^"]*)"', html)
    assert cancel_tag is not None
    assert "btn-ghost" in cancel_tag.group(1)
    assert 'href="#"' in cancel_tag.group(0)


def test_confirm_dialog_renders_in_clickable_card_mode():
    card = CardBlock()
    value = card.to_python(
        {
            "design": CARD_DESIGN,
            "audience": {},
            "content": [
                {
                    "type": "action",
                    "value": {
                        "action": "demo",
                        "target_expression": "",
                        "button": {
                            "text": "Delete",
                            "make_parent_clickable": True,
                            "confirm": {
                                "title": "Delete?",
                                "text": "Permanent.",
                                "confirm_label": "Delete",
                            },
                            "design": {},
                            "audience": {},
                        },
                    },
                }
            ],
        }
    )
    html = card.render(value)

    overlay = re.search(r'<a[^>]*class="absolute! inset-0!"[^>]*>', html)
    assert overlay is not None
    assert 'href="#daisie-action-confirm-' in overlay.group(0)
    assert 'aria-haspopup="dialog"' in overlay.group(0)
    assert not re.search(r'<button type="submit" class="absolute! inset-0!"', html)
    assert 'role="dialog"' in html
    assert "Delete?" in html
    assert "Permanent." in html


def test_action_form_without_fields_is_valid(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    block = ActionFormBlock()
    value = block.to_python(
        {
            "action": "demo",
            "target_expression": "",
            "button": {"text": "Save", "design": {}, "audience": {}},
            "behaviour": "inline",
        }
    )
    block.clean(value)
    assert block.child_blocks["fields"].required is False


def test_action_form_without_confirmation_has_no_alert_fields():
    block = ActionFormBlock()
    value = block.to_python(
        {
            "action": "demo",
            "target_expression": "",
            "fields": [],
            "button": {"text": "Save", "design": {}, "audience": {}},
            "behaviour": "inline",
        }
    )
    html = block.render(value)
    assert 'name="daisie_behaviour"' in html
    assert 'name="daisie_message"' not in html
    assert 'name="daisie_message_level"' not in html


def test_legacy_button_confirmation_dict_normalizes_and_renders():
    block = ActionButtonBlock()
    value = block.to_python(
        {
            "text": "Run",
            "confirm": {
                "title": "Are you sure?",
                "text": "This cannot be undone.",
                "confirm_label": "Go",
            },
            "design": {},
            "audience": {},
        }
    )
    assert len(value["confirm"]) == 1
    assert value["confirm"][0].block_type == "item"

    html = block.render(value)
    assert "Are you sure?" in html
    assert "This cannot be undone." in html
    assert "Go" in html

    prepared = block.get_prep_value(value)["confirm"]
    assert len(prepared) == 1
    assert prepared[0]["type"] == "item"
    assert prepared[0]["value"]["title"] == "Are you sure?"


def test_legacy_action_confirmation_dict_normalizes_and_renders():
    block = ActionBlock()
    value = block.to_python(
        {
            "action": "demo",
            "target_expression": "",
            "button": {"text": "Run", "design": {}, "audience": {}},
            "confirmation": {
                "text": "Saved",
                "icon": "",
                "color": "alert-success",
                "style": "",
                "direction": "",
            },
        }
    )
    assert len(value["confirmation"]) == 1
    assert value["confirmation"][0].block_type == "item"

    html = block.render(value, context={"audience_allowed": True})
    assert 'name="daisie_message" value="Saved"' in html
    assert 'name="daisie_message_level" value="success"' in html

    prepared = block.get_prep_value(value)["confirmation"]
    assert prepared[0]["type"] == "item"
    assert prepared[0]["value"]["text"] == "Saved"


def test_legacy_action_form_confirmation_dict_normalizes_and_renders():
    block = ActionFormBlock()
    value = block.to_python(
        {
            "action": "demo",
            "target_expression": "",
            "fields": [],
            "button": {"text": "Save", "design": {}, "audience": {}},
            "behaviour": "inline",
            "confirmation": {
                "text": "Form saved",
                "icon": "",
                "color": "alert-info",
                "style": "",
                "direction": "",
            },
        }
    )
    assert len(value["confirmation"]) == 1
    html = block.render(value)
    assert 'name="daisie_message" value="Form saved"' in html
    assert 'name="daisie_message_level" value="info"' in html


def test_new_confirmation_streams_render():
    block = ActionBlock()
    value = block.to_python(
        {
            "action": "demo",
            "target_expression": "",
            "button": {
                "text": "Run",
                "design": {},
                "audience": {},
                "confirm": [
                    {
                        "type": "item",
                        "value": {
                            "title": "Proceed?",
                            "text": "Confirm this.",
                            "confirm_label": "Yes",
                        },
                    }
                ],
            },
            "confirmation": [
                {
                    "type": "item",
                    "value": {
                        "text": "Done",
                        "icon": "",
                        "color": "alert-success",
                        "style": "",
                        "direction": "",
                    },
                }
            ],
        }
    )
    assert value["button"]["confirm"][0].block_type == "item"
    assert value["confirmation"][0].block_type == "item"

    html = block.render(value, context={"audience_allowed": True})
    assert "Proceed?" in html
    assert "Confirm this." in html
    assert 'name="daisie_message" value="Done"' in html


def _action_endpoint():
    return reverse("wagtail_daisIE_dynamic:action", args=["demo"])


def test_action_endpoint_configured_confirmation_matches_plain_and_inline(
    settings, client
):
    settings.WAGTAIL_DAISIE_ACTIONS = {
        "demo": {"label": "Demo", "handler": lambda request, data: None}
    }
    url = _action_endpoint()
    data = {
        "daisie_message": "Saved now",
        "daisie_message_icon": "wagtail:home",
        "daisie_message_tags": "alert-success alert-soft alert-vertical invalid-class",
        "daisie_message_level": "success",
    }

    response = client.post(url, data, HTTP_REFERER="/back/")
    assert response.status_code == 302
    message = list(get_messages(response.wsgi_request))[0]
    assert "Saved now" in str(message)
    assert "<svg" in str(message)
    assert message.extra_tags == "alert-success alert-soft alert-vertical"
    assert message.level_tag == "success"

    inline = client.post(
        url,
        {**data, "daisie_behaviour": "inline"},
        HTTP_HX_REQUEST="true",
    )
    content = inline.content.decode()
    assert "alert alert-success alert-soft alert-vertical" in content
    assert "invalid-class" not in content
    assert "Saved now" in content
    assert "<svg" in content

    fallback = client.post(
        url,
        {"daisie_message": "Saved", "daisie_message_level": "error"},
        HTTP_HX_REQUEST="true",
    )
    assert "alert alert-error" in fallback.content.decode()


def test_action_endpoint_without_confirmation_has_no_message_or_fragment(
    settings, client
):
    settings.WAGTAIL_DAISIE_ACTIONS = {
        "demo": {"label": "Demo", "handler": lambda request, data: None}
    }
    url = _action_endpoint()

    response = client.post(url, HTTP_REFERER="/back/")
    assert response.status_code == 302
    assert list(get_messages(response.wsgi_request)) == []

    inline = client.post(url, {"daisie_behaviour": "inline"}, HTTP_HX_REQUEST="true")
    assert inline.content.decode().strip() == ""


def test_action_endpoint_escapes_confirmation_text(settings, client):
    settings.WAGTAIL_DAISIE_ACTIONS = {
        "demo": {"label": "Demo", "handler": lambda request, data: None}
    }
    inline = client.post(
        _action_endpoint(),
        {"daisie_message": "<b>Saved</b>", "daisie_behaviour": "inline"},
        HTTP_HX_REQUEST="true",
    )
    content = inline.content.decode()
    assert "<b>Saved</b>" not in content
    assert "&lt;b&gt;Saved&lt;/b&gt;" in content


def test_action_form_htmx_behaviours(settings, client):
    def handler(request, data):
        if data.get("daisie_behaviour") == "navigate":
            return redirect("/next/")
        return None

    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": handler}}
    url = _action_endpoint()

    inline = client.post(
        url,
        {"daisie_message": "Saved", "daisie_behaviour": "inline"},
        HTTP_HX_REQUEST="true",
    )
    assert inline.status_code == 200
    assert "Saved" in inline.content.decode()

    refresh = client.post(url, {"daisie_behaviour": "reload"}, HTTP_HX_REQUEST="true")
    assert refresh["HX-Refresh"] == "true"

    navigate = client.post(
        url, {"daisie_behaviour": "navigate"}, HTTP_HX_REQUEST="true"
    )
    assert navigate["HX-Redirect"] == "/next/"
