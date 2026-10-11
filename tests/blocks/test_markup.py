import pytest

from django.template import Context, Template

from wagtail_daisIE.base_blocks.markup import (
    render_inline_markup,
    strip_inline_markup,
)


class TestInlineMarkup:
    def test_each_feature(self):
        assert "<strong>x</strong>" in render_inline_markup("**x**")
        assert "<em>x</em>" in render_inline_markup("_x_")
        assert "<u>x</u>" in render_inline_markup("__x__")
        assert "<s>x</s>" in render_inline_markup("~~x~~")
        assert '<a href="https://a.test" class="link">x</a>' in render_inline_markup(
            "[x](https://a.test)"
        )

    def test_underline_beats_italic(self):
        assert render_inline_markup("__x__") == "<u>x</u>"

    def test_underline_parses_nested_markup(self):
        assert render_inline_markup("__a**b**__") == "<u>a<strong>b</strong></u>"

    def test_link_new_tab(self):
        assert render_inline_markup("[x](https://a.test){target=_blank}") == (
            '<a href="https://a.test" class="link" target="_blank" '
            'rel="noopener noreferrer">x</a>'
        )

    def test_colour_shorthand_named(self):
        assert (
            render_inline_markup("[x]{color=primary}")
            == '<span style="color: var(--color-primary)">x</span>'
        )

    def test_colour_shorthand_hex(self):
        assert (
            render_inline_markup("[x]{color=#e11d48}")
            == '<span style="color: #e11d48">x</span>'
        )

    def test_style_is_sanitised(self):
        rendered = render_inline_markup(
            '[x]{style="font-size: 2em; background: url(javascript:alert(1))"}'
        )
        assert "font-size: 2em" in rendered
        assert "url(" not in rendered and "javascript" not in rendered

    def test_allow_links_false(self):
        assert render_inline_markup("[x](https://a.test)", allow_links=False) == "x"

    def test_url_allow_list(self):
        rendered = render_inline_markup("[x](javascript:alert(1))")
        assert "<a" not in rendered

    def test_escaped_literals(self):
        assert "&lt;script&gt;" in render_inline_markup("&lt;script&gt;")

    def test_strip(self):
        assert strip_inline_markup("**a** [b](https://c.test)") == "a b"


@pytest.mark.django_db
class TestMarkupTag:
    def test_tag_substitutes_and_renders(self):
        template = Template("{% load notifications %}{% daisie_markup value %}")
        rendered = template.render(
            Context({"value": "**{{ payload.name }}**", "payload": {"name": "Rye"}})
        )
        assert rendered == "<strong>Rye</strong>"

    def test_tag_rejects_links_when_disabled(self):
        template = Template(
            "{% load notifications %}{% daisie_markup value allow_links=False %}"
        )
        rendered = template.render(Context({"value": "[x](https://a.test)"}))
        assert rendered == "x"
