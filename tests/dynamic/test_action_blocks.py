from wagtail_daisIE.dynamic.action_blocks import (
    ACTION_FORM_BEHAVIOUR_CHOICES,
    ActionFormBlock,
)


def test_action_form_resolves_url_and_behaviours():
    context = ActionFormBlock().get_context(
        {"action": "demo", "fields": [], "button": {}, "behaviour": "inline"}
    )
    assert context["action_url"] == "/daisie/actions/demo/"
    assert {key for key, _label in ACTION_FORM_BEHAVIOUR_CHOICES} == {
        "inline",
        "reload",
        "navigate",
    }
