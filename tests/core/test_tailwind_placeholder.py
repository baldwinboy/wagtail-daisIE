from wagtail_daisIE.tailwindcss import placeholder


def test_placeholder_contains_base_style_config_and_script():
    html = placeholder.placeholder_html()
    assert "wagtail_daisIE/css/daisie-base.css" in html
    assert '<style id="daisyui-jit-styles"></style>' in html
    assert 'id="daisyui-jit-config"' in html
    assert "application/json" in html
    assert "wagtail_daisIE/js/tailwind_jit.js" in html
    assert 'type="module"' in html


def test_inject_replaces_full_page_config():
    html = (
        "<html><head>"
        '<script id="daisyui-jit-config" type="application/json">{}</script>'
        "</head><body></body></html>"
    )
    config = {"mode": "fetch", "cssUrl": "/css/abc.css"}
    updated = placeholder.inject_config(html, config, fragment=False, key="a" * 64)
    assert updated is not None
    assert '"mode": "fetch"' in updated
    assert '"cssUrl": "/css/abc.css"' in updated
    assert "<style" not in updated


def test_inject_returns_none_without_config_element():
    assert (
        placeholder.inject_config(
            "<html><head></head></html>",
            {"mode": "fetch"},
            fragment=False,
            key="a" * 64,
        )
        is None
    )


def test_fragment_config_is_prepended():
    updated = placeholder.inject_config(
        '<div class="flex"></div>',
        {"mode": "ws", "inputUrl": "/input.css"},
        fragment=True,
        key="b" * 64,
    )
    assert updated is not None
    assert updated.startswith('<script id="daisyui-jit-config-')
    assert '<div class="flex"></div>' in updated
