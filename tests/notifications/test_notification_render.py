import itertools

from datetime import datetime

import pytest

from django.template import Context, Template
from django.test import RequestFactory

from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.models import EmailTemplate
from wagtail_daisIE.notifications.rendering import html_to_text


pytestmark = pytest.mark.django_db

_template_seq = itertools.count()


def _template(subject="", body_text="Hello"):
    theme, _created = DaisyUITheme.objects.get_or_create(
        name="email-theme", defaults={"default": True}
    )
    template = EmailTemplate.objects.create(
        name=f"Welcome {next(_template_seq)}", subject=subject
    )
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
    def test_mjml_substitution_and_date_filter(self):
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

        template = _template(body_text='{{ now|date:"j F Y" }}')
        mjml = template.get_mjml(
            context={"payload": {}, "now": datetime(2026, 11, 12), "site": None}
        )
        assert "12 November 2026" in mjml

    def test_subject_render_and_preview(self):
        template = _template(
            subject="Hi {{ payload.name }}", body_text="Hi {{ payload.name }}"
        )
        rendered = template.render(payload={"name": "Ada"})
        assert rendered.subject == "Hi Ada"
        assert "Ada" in rendered.html and "{{ payload.name }}" not in rendered.html
        assert "Ada" in rendered.text

        context = template.get_preview_context(RequestFactory().get("/"), "html")
        assert "mjml_source" in context
        assert "{{ payload.name }}" not in context["mjml_source"]

    def test_daisie_text_and_richtext_tags(self):
        result = Template("{% load notifications %}{% daisie_text value %}").render(
            Context({"value": "Hi {{ payload.name }}", "payload": {"name": "Ada"}})
        )
        assert result == "Hi Ada"

        result = Template("{% load notifications %}{% daisie_richtext value %}").render(
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
        assert "Hello" in text and "World" in text
        assert "alert" not in text and ".x{}" not in text
