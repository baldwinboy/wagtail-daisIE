from django.test import override_settings

from wagtail_daisIE.checks import check_action_fields
from wagtail_daisIE.dynamic.actions import get_action_fields


VALID_ACTIONS = {
    "profile.update": {
        "label": "Update profile",
        "handler": "myapp.actions.update_profile",
        "fields": [
            {
                "type": "input",
                "name": "display_name",
                "label": "Display name",
                "required": True,
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
        ],
    }
}


def _errors(actions):
    with override_settings(WAGTAIL_DAISIE_ACTIONS=actions):
        return check_action_fields(None)


@override_settings(WAGTAIL_DAISIE_ACTIONS=VALID_ACTIONS)
def test_valid_action_fields_are_quiet():
    assert check_action_fields(None) == []
    assert [field["name"] for field in get_action_fields("profile.update")] == [
        "display_name",
        "diet",
        "newsletter",
    ]


@override_settings(
    WAGTAIL_DAISIE_ACTIONS={"legacy": {"label": "Legacy", "handler": "handler"}}
)
def test_action_config_without_fields_is_quiet():
    assert check_action_fields(None) == []
    assert get_action_fields("legacy") == []
    assert get_action_fields("missing") == []


def test_unsupported_type_is_reported():
    errors = _errors(
        {
            "bad": {
                "label": "Bad",
                "handler": "handler",
                "fields": [{"type": "unknown", "name": "x", "label": "X"}],
            }
        }
    )
    assert [error.id for error in errors] == ["wagtail_daisIE.E002"]
    assert "unsupported type" in errors[0].msg


def test_duplicate_names_are_reported():
    errors = _errors(
        {
            "bad": {
                "label": "Bad",
                "handler": "handler",
                "fields": [
                    {"type": "input", "name": "x", "label": "X"},
                    {"type": "input", "name": "x", "label": "X again"},
                ],
            }
        }
    )
    assert [error.id for error in errors] == ["wagtail_daisIE.E002"]
    assert "duplicates field name" in errors[0].msg


def test_missing_options_are_reported():
    errors = _errors(
        {
            "bad": {
                "label": "Bad",
                "handler": "handler",
                "fields": [{"type": "select", "name": "size", "label": "Size"}],
            }
        }
    )
    assert [error.id for error in errors] == ["wagtail_daisIE.E002"]
    assert "needs options" in errors[0].msg


def test_fields_must_be_a_list():
    errors = _errors(
        {
            "bad": {
                "label": "Bad",
                "handler": "handler",
                "fields": {"type": "input"},
            }
        }
    )
    assert [error.id for error in errors] == ["wagtail_daisIE.E002"]
    assert "fields must be a list" in errors[0].msg


def test_unsupported_field_keys_are_reported():
    errors = _errors(
        {
            "bad": {
                "label": "Bad",
                "handler": "handler",
                "fields": [
                    {
                        "type": "input",
                        "name": "x",
                        "label": "X",
                        "option": "typo",
                    }
                ],
            }
        }
    )
    assert [error.id for error in errors] == ["wagtail_daisIE.E002"]
    assert "unsupported keys: option" in errors[0].msg
