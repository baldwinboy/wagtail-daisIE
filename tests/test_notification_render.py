from datetime import datetime

import pytest

from django.template import Context, Template
from django.test import RequestFactory

from wagtail_daisIE.emails.models import EmailTemplate
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.rendering import html_to_text


pytestmark = pytest.mark.django_db


def _template(subject="", body_text="Hello"):
    theme = DaisyUITheme.objects.create(name="email-theme", default=True)
    template = EmailTemplate.objects.create(name="Welcome", subject=subject)
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {},
                "content": [
                    {"type": "text", "value": {"text": body_text, "design": {}}},
                ],
            },
        }
    ]
    template.save()
    return template


class TestPlaceholderInjection:
    def test_mjml_substitutes_values(self):
        template = _template(body_text="Hello {{ payload.name }}")
        mjml = template.get_mjml(
            context={
                "payload": {"name": "Ada"},
                "now": datetime(2026, 11, 12),
                "site": None,
            }
        )
        assert "Hello Ada" in mjml
        assert "{{ payload.name }}" not in mjml

    def test_mjml_applies_date_filter(self):
        template = _template(body_text='{{ now|date:"j F Y" }}')
        mjml = template.get_mjml(
            context={
                "payload": {},
                "now": datetime(2026, 11, 12),
                "site": None,
            }
        )
        assert "12 November 2026" in mjml

    def test_subject_is_substituted(self):
        template = _template(subject="Hi {{ payload.name }}")
        rendered = template.render(payload={"name": "Ada"})
        assert rendered.subject == "Hi Ada"

    def test_render_compiles_html_and_text(self):
        template = _template(body_text="Hi {{ payload.name }}")
        rendered = template.render(payload={"name": "Ada"})
        assert "Ada" in rendered.html
        assert "{{ payload.name }}" not in rendered.html
        assert "Ada" in rendered.text
        assert rendered.subject == ""

    def test_unknown_placeholder_renders_empty(self):
        template = _template(body_text="A{{ payload.nope }}B")
        mjml = template.get_mjml(
            context={"payload": {}, "now": datetime(2026, 11, 12), "site": None}
        )
        assert "AB" in mjml

    def test_preview_context_is_substituted(self):
        template = _template(body_text="Hi {{ payload.name }}")
        request = RequestFactory().get("/")
        context = template.get_preview_context(request, "html")
        assert "mjml_source" in context
        assert "{{ payload.name }}" not in context["mjml_source"]


@pytest.mark.django_db
class TestDaisieTags:
    def test_text_tag_substitutes(self):
        source = "{% load notifications %}{% daisie_text value %}"
        result = Template(source).render(
            Context({"value": "Hi {{ payload.name }}", "payload": {"name": "Ada"}})
        )
        assert result == "Hi Ada"

    def test_text_tag_escapes_literals(self):
        source = "{% load notifications %}{% daisie_text value %}"
        result = Template(source).render(Context({"value": "a < b"}))
        assert result == "a &lt; b"

    def test_richtext_tag_preserves_html(self):
        source = "{% load notifications %}{% daisie_richtext value %}"
        result = Template(source).render(
            Context(
                {
                    "value": "<p>Hi {{ payload.name }}</p>",
                    "payload": {"name": "Ada"},
                }
            )
        )
        assert "<p>Hi Ada</p>" in result


class TestHtmlToText:
    def test_strips_markup_and_scripts(self):
        html = (
            "<html><head><style>.x{}</style></head>"
            "<body><p>Hello</p><p>World</p>"
            "<script>alert(1)</script></body></html>"
        )
        text = html_to_text(html)
        assert "Hello" in text
        assert "World" in text
        assert "alert" not in text
        assert ".x{}" not in text

    def test_empty(self):
        assert html_to_text("") == ""
