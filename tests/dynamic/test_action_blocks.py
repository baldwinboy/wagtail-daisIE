from wagtail import blocks

from wagtail_daisIE.dynamic.action_blocks import (
    ACTION_FORM_BEHAVIOUR_CHOICES,
    ActionButtonBlock,
    ActionFormBlock,
)


def test_action_button_drops_link_fields():
    children = ActionButtonBlock().child_blocks
    assert "destination" not in children
    assert "open_in_new_tab" not in children
    assert "text" in children
    assert "confirm" in children
    assert set(children["confirm"].child_blocks) == {
        "title",
        "text",
        "confirm_label",
    }


def test_action_button_renders_every_nested_stream():
    block = ActionButtonBlock()
    layout = block.meta.form_layout
    names = set()
    for child in [*layout.children, *layout.settings]:
        if isinstance(child, str):
            names.add(child)
    for name, child in block.child_blocks.items():
        if isinstance(child, blocks.StreamBlock):
            assert name in names


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
