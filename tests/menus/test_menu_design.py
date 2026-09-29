import pytest

from django.template import Context, Template

from wagtail_daisIE.menus.models import DaisyUIMenu
from wagtail_daisIE.models import DaisyUITheme


pytestmark = pytest.mark.django_db


def _render(menu_name):
    template = Template(
        '{% load wagtail_daisIE_tags %}{% daisyui_menu "' + menu_name + '" %}'
    )
    return template.render(Context({}))


class TestMenuItemDesign:
    def test_item_design_and_menu_theme(self):
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

        other = DaisyUITheme.objects.create(name="other-theme")
        themed = DaisyUIMenu.objects.create(
            name="Themed", layout="horizontal", menu_theme=other
        )
        themed.save()
        assert 'data-theme="other-theme"' in _render("Themed")


class TestMenuBranding:
    def test_branding_wordmark_wrapped_or_plain(self):
        for open_in_new_tab in (True, False):
            menu = DaisyUIMenu.objects.create(
                name=f"Branded {open_in_new_tab}", layout="navbar"
            )
            menu.branding = [
                (
                    "branding",
                    {
                        "wordmark": {"text": "Acme"},
                        "destination": [
                            {"type": "link_url", "value": "https://example.com"}
                        ],
                        "open_in_new_tab": open_in_new_tab,
                    },
                )
            ]
            menu.save()
            html = _render(f"Branded {open_in_new_tab}")
            assert "Acme" in html and 'href="https://example.com"' in html
            if open_in_new_tab:
                assert 'target="_blank"' in html
                # Without noopener the destination gets window.opener.
                assert 'rel="noopener noreferrer"' in html
            else:
                assert 'target="_blank"' not in html

        plain = DaisyUIMenu.objects.create(name="Plain", layout="navbar")
        plain.branding = [
            (
                "branding",
                {
                    "wordmark": {"text": "Acme"},
                    "destination": [],
                    "open_in_new_tab": False,
                },
            )
        ]
        plain.save()
        html = _render("Plain")
        assert "Acme" in html and "https://example.com" not in html
