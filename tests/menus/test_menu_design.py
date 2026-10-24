import pytest

from django.template import Context, Template

from wagtail_daisIE.blocks.menu_items import is_static_menu_block
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


class TestMenuStaticItems:
    def test_static_classifier(self):
        for block_type in (
            "header",
            "text",
            "search",
            "newsletter",
            "inline_card",
            "link_list",
        ):
            assert is_static_menu_block(block_type)
        for block_type in ("link", "button", "action", "accordion", "reusable"):
            assert not is_static_menu_block(block_type)

    def test_static_menu_items_opt_out_of_hover(self):
        menu = DaisyUIMenu.objects.create(name="Static", layout="horizontal")
        menu.body = [
            {"type": "header", "value": {"text": "Heading"}},
            {"type": "text", "value": {"text": "Body"}},
        ]
        menu.save()
        html = _render("Static")
        assert html.count('class="menu-static"') == 2

    def test_links_are_not_static(self):
        menu = DaisyUIMenu.objects.create(name="Links", layout="horizontal")
        menu.body = [
            {
                "type": "link",
                "value": {
                    "text": "Home",
                    "destination": [{"type": "link_url", "value": "/"}],
                    "open_in_new_tab": False,
                },
            }
        ]
        menu.save()
        assert 'class="menu-static"' not in _render("Links")

    def test_all_menu_layouts_use_static_class(self):
        for layout in ("navbar", "horizontal", "vertical", "sidebar"):
            menu = DaisyUIMenu.objects.create(name=f"Static {layout}", layout=layout)
            menu.body = [{"type": "header", "value": {"text": "Heading"}}]
            menu.save()
            assert 'class="menu-static"' in _render(f"Static {layout}")


def test_top_level_search_fields_are_removed():
    from django.core.exceptions import FieldDoesNotExist

    for name in (
        "show_search",
        "search_url",
        "search_parameter",
        "search_placeholder",
    ):
        with pytest.raises(FieldDoesNotExist):
            DaisyUIMenu._meta.get_field(name)
