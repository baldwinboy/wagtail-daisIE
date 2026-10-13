from wagtail_daisIE.dynamic.action_blocks import ActionFormBlock


def test_action_form_resolves_url():
    context = ActionFormBlock().get_context(
        {"action": "demo", "fields": [], "button": {}, "behaviour": "inline"}
    )
    assert context["action_url"] == "/daisie/actions/demo/"
