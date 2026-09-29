from wagtail_daisIE.base_blocks import DesignBlock


def _design():
    return DesignBlock()


class TestOptionalBackground:
    def test_empty_background_validates(self):
        block = _design()
        value = {name: {} for name in block.child_blocks}
        value["background"] = []
        block.clean(value)

    def test_solid_layer_validates(self):
        block = _design()
        background = block.child_blocks["background"]
        value = {name: {} for name in block.child_blocks}
        value["background"] = background.to_python(
            [("layer", {"layer_type": "solid", "color": "bg-primary"})]
        )
        block.clean(value)
