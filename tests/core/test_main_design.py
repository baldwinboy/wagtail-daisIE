from django.template import Context, Template

from wagtail_daisIE.base_blocks import MainDesignBlock
from wagtail_daisIE.base_blocks.css import build_design_css


class TestMainDesign:
    def test_layout_choices(self):
        block = MainDesignBlock()
        assert block.child_blocks["layout"].field.choices

    def test_layout_classes(self):
        assert build_design_css({"layout": "column"}) == "flex flex-col grow"
        assert build_design_css({"layout": "row"}) == "flex flex-row grow"
        assert build_design_css({"layout": "grid"}) == "grid grow"

    def test_builder_combines_layout_and_size(self):
        css = build_design_css({"layout": "grid", "padding": {"all_padding": "p-8"}})
        classes = css.split()
        assert "grid" in classes and "grow" in classes and "p-8" in classes


class TestMainAttrsTag:
    def test_renders_class(self):
        rendered = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_main_attrs %}"
        ).render(Context({"daisyui_main_css": "grid grow"}))
        assert 'class="grid grow"' in rendered

    def test_empty_when_unset(self):
        rendered = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_main_attrs %}"
        ).render(Context({}))
        assert rendered == ""
