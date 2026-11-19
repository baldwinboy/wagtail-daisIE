import re

import pytest

from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import redirect
from django.urls import reverse

from wagtail_daisIE.blocks.cards import CardBlock
from wagtail_daisIE.blocks.layout_components import TabsBlock
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


def _checkbox_field(label, helper_text, block_id, field_layout=None):
    value = {
        "label": label,
        "helper_text": helper_text,
        "design": {},
        "audience": {},
    }
    if field_layout is not None:
        value["field_layout"] = field_layout
    return {
        "type": "checkbox",
        "id": block_id,
        "value": value,
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
    assert dialogs[0][0].value["header"]["text"] == "Confirm"

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


def test_confirm_dialog_header_and_body_blocks():
    block = ActionButtonBlock()
    value = block.to_python(
        {
            "text": "Delete",
            "confirm": {
                "header": {
                    "text": "Delete item?",
                    "design": {"typography": {"text_color": "text-primary"}},
                    "audience": {},
                },
                "body": {
                    "text": "This cannot be undone.",
                    "design": {"typography": {"text_color": "text-secondary"}},
                    "audience": {},
                },
                "confirm_label": "Delete",
            },
            "design": {},
            "audience": {},
        }
    )
    html = block.render(value)

    assert "<h2" in html
    assert "Delete item?" in html
    assert "This cannot be undone." in html
    assert "text-primary" in html
    assert "text-secondary" in html

    prepared = block.get_prep_value(value)["confirm"][0]["value"]
    assert prepared["header"]["text"] == "Delete item?"
    assert prepared["body"]["text"] == "This cannot be undone."
    assert "title" not in prepared
    assert "text" not in prepared


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


PRESET_ACTIONS = {
    "demo": {
        "label": "Demo",
        "handler": "handler",
        "fields": [
            {
                "type": "input",
                "name": "display_name",
                "label": "Display name",
                "required": True,
                "helper_text": "Shown publicly",
            },
            {
                "type": "select",
                "name": "diet",
                "label": "Diet",
                "options": ["Omnivore", "Vegetarian"],
            },
            {
                "type": "checkbox",
                "name": "newsletter",
                "label": "Newsletter",
            },
            {
                "type": "checkbox",
                "name": "alerts",
                "label": "Alerts",
            },
        ],
    }
}


def _form_value(fields=None, **overrides):
    value = {
        "action": "demo",
        "target_expression": "",
        "button": {"text": "Save", "design": {}, "audience": {}},
        "behaviour": "inline",
    }
    if fields is not None:
        value["fields"] = fields
    value.update(overrides)
    return value


def _input_value(name, label="Field"):
    return {
        "label": label,
        "name": name,
        "design": {},
        "audience": {},
    }


def _clean_error(block, value):
    with pytest.raises(ValidationError) as exc_info:
        block.clean(value)
    return exc_info.value


def _field_errors(error):
    stream_error = error.block_errors["fields"]
    return {
        index: child_error.messages
        for index, child_error in stream_error.block_errors.items()
    }


def test_action_form_field_list_and_wrapper_layouts(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            fields_layout={"layout": "row", "gap": "gap-4"},
            field_wrapper_layout={"width": "w-1/2"},
        )
    )
    html = block.render(value)

    stack = re.search(r'<div class="([^"]*flex flex-row[^"]*)">', html)
    assert stack is not None
    assert "gap-4" in stack.group(1)
    assert "flex-col" not in stack.group(1)
    assert html.count('class="w-1/2"') == 4


def test_action_form_grid_wrapper_spans(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            fields_layout={"layout": "grid", "columns": 2},
            field_wrapper_layout={"grid_column_span": "col-span-2"},
        )
    )
    html = block.render(value)

    stack = re.search(r'<div class="([^"]*\bgrid\b[^"]*)">', html)
    assert stack is not None
    assert "grid-cols-1 sm:grid-cols-2" in stack.group(1)
    assert html.count('class="col-span-2"') == 4


def test_editor_field_overrides_matching_preset(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            [
                {
                    "type": "input",
                    "value": {
                        "label": "Custom name",
                        "name": "display_name",
                        "helper_text": "Custom help",
                        "design": {"padding": {"all_padding": "p-2"}},
                        "audience": {},
                    },
                }
            ]
        )
    )
    html = block.render(value)

    assert "Custom name" in html
    assert "Custom help" in html
    assert "p-2" in html
    assert "Display name" not in html
    assert "Diet" in html and "Vegetarian" in html


def test_editor_only_fields_are_preserved(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {}
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            [
                {
                    "type": "input",
                    "value": {
                        "label": "Editor only",
                        "name": "editor_only",
                        "design": {},
                        "audience": {},
                    },
                }
            ]
        )
    )
    html = block.render(value)

    assert "Editor only" in html
    assert "daisie-demo-1-editor_only" in html
    assert "None" not in re.findall(r'id="daisie-[^"]+"', html)[0]


@pytest.mark.parametrize(
    ("fields", "error_index", "message"),
    [
        (
            [{"type": "input", "value": _input_value("extra", "Extra")}],
            0,
            "not a field declared by this action",
        ),
        (
            [
                {"type": "input", "value": _input_value("display_name", "One")},
                {"type": "input", "value": _input_value("display_name", "Two")},
            ],
            1,
            "used by more than one field",
        ),
        (
            [{"type": "input", "value": _input_value("", "No name")}],
            0,
            "Enter a field name",
        ),
        (
            [
                {
                    "type": "select",
                    "value": {
                        "label": "Wrong type",
                        "name": "display_name",
                        "options": "One\nTwo",
                        "design": {},
                        "audience": {},
                    },
                }
            ],
            0,
            "is configured as input, but this field is select",
        ),
    ],
)
def test_action_form_rejects_invalid_editor_fields(
    settings, fields, error_index, message
):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(_form_value(fields))

    error = _clean_error(block, value)
    errors = _field_errors(error)

    assert set(errors) == {error_index}
    assert message in errors[error_index][0]
    assert "fields" in error.as_json_data()["blockErrors"]


def test_action_form_editor_only_requires_named_unique_fields(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    block = ActionFormBlock()

    unnamed = block.to_python(
        _form_value([{"type": "input", "value": _input_value("", "No name")}])
    )
    error = _clean_error(block, unnamed)
    assert "Enter a field name" in _field_errors(error)[0][0]

    duplicate = block.to_python(
        _form_value(
            [
                {"type": "input", "value": _input_value("editor_only")},
                {"type": "input", "value": _input_value("editor_only")},
            ]
        )
    )
    error = _clean_error(block, duplicate)
    assert "used by more than one field" in _field_errors(error)[1][0]


def test_action_form_accepts_valid_partial_override_and_contract(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            [
                {
                    "type": "input",
                    "value": {
                        **_input_value("display_name", "Custom name"),
                        "required": False,
                    },
                }
            ]
        )
    )

    cleaned = block.clean(value)
    field = cleaned["fields"][0]

    assert field.value["name"] == "display_name"
    assert field.value["required"] is True
    assert field.value["label"] == "Custom name"


def test_action_form_editor_only_fields_are_valid(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    block = ActionFormBlock()
    value = block.to_python(
        _form_value([{"type": "input", "value": _input_value("editor_only")}])
    )

    cleaned = block.clean(value)
    assert cleaned["fields"][0].value["name"] == "editor_only"


def test_action_form_config_only_fields_are_valid(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(_form_value())

    cleaned = block.clean(value)
    assert list(cleaned["fields"]) == []


def test_action_form_render_uses_configured_required(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            [
                {
                    "type": "input",
                    "value": {
                        **_input_value("display_name"),
                        "required": False,
                    },
                }
            ]
        )
    )

    html = block.render(value)
    tag = re.search(r'<input[^>]*name="display_name"[^>]*>', html)

    assert tag is not None
    assert "required" in tag.group(0)
    assert value["fields"][0].value["required"] is False


def test_action_form_render_ignores_mismatched_override(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = PRESET_ACTIONS
    block = ActionFormBlock()
    value = block.to_python(
        _form_value(
            [
                {
                    "type": "select",
                    "value": {
                        "label": "Custom select",
                        "name": "display_name",
                        "options": "One\nTwo",
                        "design": {},
                        "audience": {},
                    },
                }
            ]
        )
    )

    html = block.render(value)

    assert "Display name" in html
    assert "Custom select" not in html
    assert re.search(r'<select[^>]*name="display_name"', html) is None


def test_action_form_checkbox_fields_with_layout_do_not_overlap(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    fields = [
        _checkbox_field(
            "First",
            "One",
            "cb1",
            {"layout": {"layout": "row"}},
        ),
        _checkbox_field(
            "Second",
            "Two",
            "cb2",
            {"layout": {"layout": "grid", "columns": 2}},
        ),
    ]
    html = _render_action_form(fields, {})

    assert html.count('data-daisie-field-part="input"') == 2
    assert html.count('data-daisie-field-part="label"') == 2
    assert html.count('data-daisie-field-part="help"') == 2
    assert html.count("w-full") >= 4
    assert "flex flex-row grow" in html
    assert "grid grow grid-cols-1 sm:grid-cols-2" in html
    assert "absolute" not in html


def test_action_form_with_no_fields_renders_button_only(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    block = ActionFormBlock()
    html = block.render(block.to_python(_form_value()))

    assert "<fieldset" not in html
    assert "Save" in html


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
    assert prepared[0]["value"]["header"]["text"] == "Are you sure?"
    assert prepared[0]["value"]["body"]["text"] == "This cannot be undone."


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


CONFIRMATION_POST = {
    "daisie_message": "Saved now",
    "daisie_message_icon": "wagtail:home",
    "daisie_message_tags": "alert-success alert-soft alert-vertical",
    "daisie_message_level": "success",
}


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


FILE_AUTOCOMPLETE_FIELDS = [
    {"type": "file", "name": "attachment", "label": "Attachment"},
    {
        "type": "autocomplete",
        "name": "tags",
        "label": "Tags",
        "options": ["One", "Two"],
    },
]


@pytest.mark.parametrize("behaviour", ["inline", "reload", "navigate"])
def test_action_form_htmx_behaviours(settings, client, behaviour):
    def handler(request, data):
        if data.get("daisie_behaviour") == "navigate":
            return redirect("/next/")
        return None

    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": handler}}
    response = client.post(
        _action_endpoint(),
        {**CONFIRMATION_POST, "daisie_behaviour": behaviour},
        HTTP_HX_REQUEST="true",
    )

    if behaviour == "inline":
        assert response.status_code == 200
        assert "Saved now" in response.content.decode()
    elif behaviour == "reload":
        assert response["HX-Refresh"] == "true"
    else:
        assert response["HX-Redirect"] == "/next/"


@pytest.mark.parametrize("behaviour", ["inline", "reload", "navigate"])
def test_action_form_plain_post_behaviours(settings, client, behaviour):
    def handler(request, data):
        if data.get("daisie_behaviour") == "navigate":
            return redirect("/next/")
        return None

    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": handler}}
    response = client.post(
        _action_endpoint(),
        {**CONFIRMATION_POST, "daisie_behaviour": behaviour},
        HTTP_REFERER="/back/",
    )

    assert response.status_code == 302
    expected = "/next/" if behaviour == "navigate" else "/back/"
    assert response["Location"] == expected

    message = list(get_messages(response.wsgi_request))[0]
    assert "Saved now" in str(message)
    assert message.level_tag == "success"


def test_action_form_file_and_autocomplete_presets(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {
        "demo": {
            "label": "Demo",
            "handler": "handler",
            "fields": FILE_AUTOCOMPLETE_FIELDS,
        }
    }
    block = ActionFormBlock()
    html = block.render(block.to_python(_form_value()))

    form_tag = re.search(r"<form\b[^>]*>", html, re.S)
    assert form_tag is not None
    form = form_tag.group(0)
    assert 'enctype="multipart/form-data"' in form
    assert 'hx-encoding="multipart/form-data"' in form
    assert 'hx-target="find .daisie-action-form-status"' in form
    assert 'name="attachment"' in html
    assert re.search(r'<select[^>]*name="tags"[^>]*multiple', html, re.S)
    assert html.count('class="daisie-action-form-status"') == 1


def test_action_form_without_file_fields_has_no_multipart_encoding(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}
    block = ActionFormBlock()
    html = block.render(
        block.to_python(_form_value([{"type": "input", "value": _input_value("name")}]))
    )

    form_tag = re.search(r"<form\b[^>]*>", html, re.S)
    assert form_tag is not None
    assert "multipart/form-data" not in form_tag.group(0)


@pytest.mark.parametrize("htmx", [False, True])
def test_action_form_file_upload_reaches_handler(settings, client, htmx):
    captured = {}

    def handler(request, data):
        upload = request.FILES.get("attachment")
        captured["name"] = upload.name
        captured["content"] = upload.read()
        captured["tags"] = data.getlist("tags")
        return None

    settings.WAGTAIL_DAISIE_ACTIONS = {
        "demo": {
            "label": "Demo",
            "handler": handler,
            "fields": FILE_AUTOCOMPLETE_FIELDS,
        }
    }
    upload = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")
    data = {"attachment": upload, "tags": ["One", "Two"]}

    if htmx:
        response = client.post(
            _action_endpoint(),
            {**data, "daisie_behaviour": "inline"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
    else:
        response = client.post(_action_endpoint(), data, HTTP_REFERER="/back/")
        assert response.status_code == 302

    assert captured == {
        "name": "note.txt",
        "content": b"hello",
        "tags": ["One", "Two"],
    }


def test_multiple_action_forms_in_tabs_keep_their_own_status(settings):
    settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"label": "Demo", "handler": "handler"}}

    def form(field_name, label, block_id):
        return {
            "type": "action_form",
            "id": block_id,
            "value": _form_value(
                [{"type": "input", "value": _input_value(field_name, label)}]
            ),
        }

    tabs = TabsBlock().to_python(
        {
            "tabs": [
                {
                    "label": "First",
                    "content": [form("first_name", "First name", "form-first")],
                    "audience": {},
                },
                {
                    "label": "Second",
                    "content": [form("second_name", "Second name", "form-second")],
                    "audience": {},
                },
            ],
            "style": "tabs-box",
        }
    )
    html = TabsBlock().render(tabs)
    forms = re.findall(r"<form\b.*?</form>", html, re.S)

    assert len(forms) == 2
    first = next(form_html for form_html in forms if 'name="first_name"' in form_html)
    second = next(form_html for form_html in forms if 'name="second_name"' in form_html)

    for form_html in (first, second):
        assert 'hx-target="find .daisie-action-form-status"' in form_html
        assert form_html.count('class="daisie-action-form-status"') == 1

    assert 'name="second_name"' not in first
    assert 'name="first_name"' not in second
    assert "daisie-action-form-status-" not in html
