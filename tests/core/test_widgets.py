from wagtail_daisIE.dynamic.widgets import ContextBindingValueWidget


def test_context_binding_value_widget_format_value():
    widget = ContextBindingValueWidget()
    assert widget.format_value("42") == {"id": "42", "title": "", "edit_url": ""}
    assert widget.format_value({"id": "7", "title": "Ada", "edit_url": "/edit/7/"}) == {
        "id": "7",
        "title": "Ada",
        "edit_url": "/edit/7/",
    }
    assert widget.format_value(None) == {"id": "", "title": "", "edit_url": ""}


def test_context_binding_value_widget_renders_hidden_input():
    widget = ContextBindingValueWidget()
    html = widget.render("binding", "42", attrs={"id": "id_binding"})
    assert 'type="hidden"' in html
    assert 'name="binding"' in html
    assert 'value="42"' in html
    assert 'id="id_binding"' in html
