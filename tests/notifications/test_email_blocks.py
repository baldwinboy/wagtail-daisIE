import itertools

import pytest

from django.template.loader import render_to_string

from wagtail_daisIE.models import (
    DaisyUITheme,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)
from wagtail_daisIE.notifications.models import EmailTemplate


pytestmark = pytest.mark.django_db

_template_seq = itertools.count()


def _template(**kwargs):
    theme, _created = DaisyUITheme.objects.get_or_create(
        name="email-theme", defaults={"default": True}
    )
    template = EmailTemplate.objects.create(name=f"Welcome {next(_template_seq)}")
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {
                    "padding": {"all_padding": "p-4"},
                    "background": [
                        {
                            "type": "layer",
                            "value": {"layer_type": "solid", "color": "bg-base-200"},
                        }
                    ],
                },
                "content": [
                    {
                        "type": "header",
                        "value": {
                            "text": "Hello there",
                            "design": {
                                "typography": {
                                    "text_color": "text-primary",
                                    "font_size": "text-lg",
                                },
                                "box": {"shadow": "shadow-sm"},
                            },
                        },
                    },
                    {
                        "type": "button",
                        "value": {
                            "text": "Click me",
                            "destination": [
                                {"type": "link_url", "value": "https://example.com"}
                            ],
                            "design": {
                                "button_appearance": {
                                    "normal": {"color": "btn-primary"}
                                }
                            },
                        },
                    },
                ],
            },
        }
    ]
    for key, value in kwargs.items():
        setattr(template, key, value)
    template.save()
    return template


class TestEmailTemplateRender:
    def test_hierarchy_defaults_and_leftovers(self):
        mjml = _template().get_mjml()
        for token in ("<mj-section", "<mj-column>", "<mj-text", "<mj-button"):
            assert token in mjml
        # padding p-4 -> 1rem, colours resolved from the theme palette.
        assert 'padding="1rem"' in mjml
        assert 'background-color="#f8f8f8"' in mjml
        assert 'background-color="#422ad5"' in mjml
        assert 'href="https://example.com"' in mjml
        # box-shadow has no MJML attribute and is emitted as scoped CSS.
        assert '<mj-style inline="inline">' in mjml
        assert "box-shadow" in mjml and 'css-class="daisie-' in mjml

        template = _template()
        template.design = [
            ("defaults", {"text": {"typography": {"text_color": "text-primary"}}})
        ]
        template.save()
        mjml = template.get_mjml()
        assert '<mj-class name="daisie-text"' in mjml
        assert 'mj-class="daisie-text"' in mjml

    def test_preview_template_renders_html(self):
        html = render_to_string(
            "wagtail_daisIE/emails/blocks/preview.html",
            {"mjml_source": _template().get_mjml()},
        )
        assert "Hello there" in html and "Click me" in html
        # The preview must show compiled HTML, not pass MJML through.
        assert "<mj-text" not in html and "<html" in html


class TestEmailFonts:
    def test_font_url_emitted_or_omitted(self):
        template = _template()
        fonts = DaisyUIThemeFonts.objects.create(theme=template.email_theme)
        DaisyUIThemeFontFamily.objects.create(
            fonts=fonts,
            role="body",
            font_family="Inter",
            url="https://fonts.googleapis.com/css2?family=Inter&display=swap",
        )
        mjml = template.get_mjml()
        assert '<mj-font name="Inter"' in mjml
        assert "family=Inter&amp;display=swap" in mjml

        # A distinct theme, so the earlier URL font does not leak in.
        fresh = DaisyUITheme.objects.create(name="no-font-theme")
        without = _template(email_theme=fresh)
        fonts = DaisyUIThemeFonts.objects.create(theme=fresh)
        DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="body", font_family="Inter"
        )
        assert "<mj-font" not in without.get_mjml()
