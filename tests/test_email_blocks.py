import pytest

from wagtail_daisIE.emails.models import EmailTemplate
from wagtail_daisIE.models import (
    DaisyUITheme,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)


pytestmark = pytest.mark.django_db


def _template(**kwargs):
    theme = DaisyUITheme.objects.create(name="email-theme", default=True)
    template = EmailTemplate.objects.create(name="Welcome")
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {
                    "padding": {"all_padding": "p-4"},
                    "background": {"bg_color": "bg-base-200"},
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
    def test_hierarchy_and_attributes(self):
        mjml = _template().get_mjml()

        assert "<mj-section" in mjml
        assert "<mj-column>" in mjml
        assert "<mj-text" in mjml
        assert "<mj-button" in mjml
        # padding p-4 -> 1rem, background resolved from the theme palette
        assert 'padding="1rem"' in mjml
        assert 'background-color="#f8f8f8"' in mjml
        # button primary colour resolved from the theme palette
        assert 'background-color="#422ad5"' in mjml
        assert 'href="https://example.com"' in mjml

    def test_theme_defaults_are_emitted_in_mj_attributes(self):
        mjml = _template().get_mjml()
        assert "<mj-attributes>" in mjml
        # No fonts configured, but text colour defaults come from the palette.
        assert "<mj-text" in mjml

    def test_category_defaults_become_mj_classes(self):
        template = _template()
        template.design = [
            (
                "defaults",
                {"text": {"typography": {"text_color": "text-primary"}}},
            )
        ]
        template.save()
        mjml = template.get_mjml()
        assert '<mj-class name="daisie-text"' in mjml
        assert 'mj-class="daisie-text"' in mjml

    def test_leftover_declarations_use_mj_style(self):
        mjml = _template().get_mjml()
        # box-shadow has no MJML attribute and is emitted as scoped CSS.
        assert '<mj-style inline="inline">' in mjml
        assert "box-shadow" in mjml
        assert 'css-class="daisie-' in mjml

    def test_compiles_to_html(self):
        from mjml.mjml import mjml2html

        html = mjml2html(_template().get_mjml())
        assert "Hello there" in html
        assert "Click me" in html

    def test_preview_template_renders_html(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "wagtail_daisIE/emails/blocks/preview.html",
            {"mjml_source": _template().get_mjml()},
        )
        assert "Hello there" in html
        assert "Click me" in html


class TestHierarchyValidation:
    def test_section_only_contains_leaf_components(self):
        from wagtail_daisIE.emails.blocks.layout import (
            EMAIL_SECTION_CHILDREN,
            EmailSectionBlock,
        )
        from wagtail_daisIE.emails.mjml import MJML_CHILDREN

        assert EmailSectionBlock.email_mjml_tag == "mj-section"
        assert EMAIL_SECTION_CHILDREN <= MJML_CHILDREN["mj-column"]

    def test_body_blocks_are_valid_body_children(self):
        from wagtail_daisIE.emails.blocks.content import EMAIL_BODY_BLOCKS
        from wagtail_daisIE.emails.mjml import BODY_LEVEL

        for _name, block in EMAIL_BODY_BLOCKS:
            if hasattr(block, "email_mjml_tag"):
                assert block.email_mjml_tag in BODY_LEVEL


class TestEmailFonts:
    def test_family_with_url_emits_mj_font(self):
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

    def test_family_without_url_is_omitted(self):
        template = _template()
        fonts = DaisyUIThemeFonts.objects.create(theme=template.email_theme)
        DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="body", font_family="Inter"
        )
        assert "<mj-font" not in template.get_mjml()
