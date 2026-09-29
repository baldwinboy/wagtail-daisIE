from importlib import resources

from wagtail.admin.telepath import registry

from wagtail_daisIE.blocks.media import ImageBlock


def test_image_block_adapter_is_registered():
    adapter = registry.find_adapter(ImageBlock)
    assert adapter.js_constructor == "wagtail_daisIE.blocks.media.ImageBlock"


def test_image_block_adapter_loads_its_js():
    """The adapter must ship its JS, so Wagtail loads it after the telepath core.

    Loading it via ``insert_global_admin_js`` instead ran it before
    ``window.wagtailStreamField`` existed, which threw and left the StreamField
    widget uninitialised (stripping the hidden ``body-count`` input and making
    page saves fail).
    """
    adapter = registry.find_adapter(ImageBlock)
    assert "wagtail_daisIE/js/image_block.js" in adapter.media._js


def test_image_block_js_registers_the_adapter_constructor():
    adapter = registry.find_adapter(ImageBlock)
    js = (
        resources.files("wagtail_daisIE")
        / "static"
        / "wagtail_daisIE"
        / "js"
        / "image_block.js"
    )
    source = js.read_text()
    assert adapter.js_constructor in source
    assert "window.telepath.register" in source
