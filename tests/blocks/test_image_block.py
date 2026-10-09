from wagtail_daisIE.blocks.media import ImageBlock


def test_image_block_uses_stimulus_controller():
    """The image-block field toggle is wired through a Stimulus controller.

    Previously a custom ``StructBlockAdapter`` shipped ``image_block.js`` (via
    the adapter's media) and reimplemented the telepath render protocol. The
    behaviour now declares ``Meta.form_attrs`` so Wagtail's default StructBlock
    adapter attaches the controller to the block element.
    """
    assert ImageBlock().meta.form_attrs == {"data-controller": "daisie-image-block"}
