from wagtail import blocks

from wagtail_daisIE.dynamic.action_blocks import ActionButtonBlock


def test_action_button_drops_link_fields():
    children = ActionButtonBlock().child_blocks
    assert "destination" not in children
    assert "open_in_new_tab" not in children
    assert "text" in children


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
