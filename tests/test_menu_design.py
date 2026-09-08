import pytest

from django.template import Context, Template

from wagtail_daisIE.models import DaisyUIMenu, DaisyUITheme


pytestmark = pytest.mark.django_db


def _render(menu_name):
    template = Template(
        '{% load wagtail_daisIE_tags %}{% daisyui_menu "' + menu_name + '" %}'
    )
    return template.render(Context({}))


class TestMenuItemDesign:
    def test_item_design_is_merged_with_block_design(self):
        menu = DaisyUIMenu.objects.create(name="Cascade", layout="horizontal")
        menu.item_design = [
            ("item", {"typography": {"text_color": "text-primary-content"}})
        ]
        menu.body = [
            {
                "type": "text",
                "value": {
                    "text": "Hello",
                    "design": {"typography": {"text_color": "text-secondary"}},
                },
            }
        ]
        menu.save()
        html = _render("Cascade")
        assert "text-primary-content" in html  # menu default
        assert "text-secondary" in html  # per-block override

    def test_menu_theme_sets_data_theme(self):
        other = DaisyUITheme.objects.create(name="other-theme")
        menu = DaisyUIMenu.objects.create(
            name="Themed", layout="horizontal", menu_theme=other
        )
        menu.save()
        html = _render("Themed")
        assert 'data-theme="other-theme"' in html
        assert menu.get_theme() == other

    def test_menu_theme_falls_back_to_default(self):
        default = DaisyUITheme.objects.create(name="default-theme", default=True)
        menu = DaisyUIMenu.objects.create(name="Fallback", layout="horizontal")
        assert menu.get_theme() == default


class TestMenuBranding:
    def test_branding_wordmark_is_wrapped_in_link(self):
        menu = DaisyUIMenu.objects.create(name="Branded", layout="navbar")
        menu.branding = [
            (
                "branding",
                {
                    "wordmark": {"text": "Acme"},
                    "destination": [
                        {"type": "link_url", "value": "https://example.com"}
                    ],
                    "open_in_new_tab": True,
                },
            )
        ]
        menu.save()
        html = _render("Branded")
        assert "Acme" in html
        assert 'href="https://example.com"' in html
        assert 'target="_blank"' in html
