import re

import pytest

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory

from wagtail_daisIE.blocks.menu_items import MenuBranding, is_static_menu_block
from wagtail_daisIE.menus.models import MENU_LAYOUT_CHOICES, DaisyUIMenu
from wagtail_daisIE.models import DaisyUITheme


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()

PAGE_DESIGN_CONTEXT = {
    "container_css": "p-8",
    "text_css": "text-primary",
    "button_css": "btn-primary",
    "media_css": "aspect-video",
}
LOGO_URL = "https://example.com/logo.png"


def _render(menu_name, context=None):
    template = Template(
        '{% load wagtail_daisIE_tags %}{% daisyui_menu "' + menu_name + '" %}'
    )
    return template.render(Context(context or {}))


def _menu_with_designs(name, layout, theme, text="Text item", *, branding=True):
    menu = DaisyUIMenu.objects.create(name=name, layout=layout, menu_theme=theme)
    menu.menu_design = [
        (
            "menu",
            {
                "padding": {"all_padding": "p-6"},
                "background": [
                    {
                        "type": "layer",
                        "value": {"layer_type": "solid", "color": "#123456"},
                    }
                ],
            },
        )
    ]
    menu.item_design = [("item", {"typography": {"text_color": "text-secondary"}})]
    if branding:
        menu.branding = [
            (
                "branding",
                {
                    "logo": {
                        "image_source": "dynamic",
                        "image_expression": "{{ logo_url }}",
                        "alt": "Acme logo",
                    },
                    "wordmark": {"text": "Acme"},
                    "destination": [],
                    "open_in_new_tab": False,
                },
            )
        ]
    menu.body = [
        {
            "type": "text",
            "value": {
                "text": text,
                "design": {},
                "audience": {},
            },
        },
        {
            "type": "button",
            "value": {
                "text": "Button item",
                "destination": [{"type": "link_url", "value": "/"}],
                "open_in_new_tab": False,
            },
        },
        {
            "type": "inline_card",
            "value": {
                "content": [
                    {
                        "type": "text",
                        "value": {
                            "text": "Card item",
                            "design": {},
                            "audience": {},
                        },
                    }
                ],
                "design": {},
                "audience": {},
            },
        },
    ]
    menu.save()
    return menu


LINK_LIST_DESIGN = {
    "padding": {"all_padding": "p-3"},
    "background": [
        {
            "type": "layer",
            "value": {"layer_type": "solid", "color": "#abcdef"},
        }
    ],
}


def _link_list_value():
    return {
        "heading": {
            "text": "More",
            "design": {"typography": {"text_color": "text-accent"}},
            "audience": {},
        },
        "content": [
            {
                "text": "Nested",
                "destination": [{"type": "link_url", "value": "/nested"}],
                "design": {"typography": {"text_color": "text-accent"}},
                "audience": {},
            }
        ],
        "design": LINK_LIST_DESIGN,
        "audience": {},
    }


def _link_menu(name, layout, *, include_plain=False, item_style=False):
    menu = DaisyUIMenu.objects.create(name=name, layout=layout)
    item_design = {"typography": {"text_color": "text-secondary"}}
    if item_style:
        item_design["background"] = [
            {"type": "layer", "value": {"layer_type": "solid", "color": "#ff0000"}}
        ]
    menu.item_design = [("item", item_design)]
    body = []
    if include_plain:
        body.append(
            {
                "type": "link",
                "value": {
                    "text": "Plain",
                    "destination": [{"type": "link_url", "value": "/plain"}],
                    "open_in_new_tab": False,
                },
            }
        )
    body.append({"type": "link_list", "value": _link_list_value()})
    menu.body = body
    menu.save()
    return menu


def _classes(tag):
    match = re.search(r'class="([^"]*)"', tag)
    assert match is not None
    return set(match.group(1).split())


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


class TestMenuPageDesignIsolation:
    @pytest.mark.parametrize("layout", [value for value, _label in MENU_LAYOUT_CHOICES])
    def test_page_design_does_not_reach_menu(self, layout):
        page_theme = DaisyUITheme.objects.create(name=f"page-{layout}")
        menu_theme = DaisyUITheme.objects.create(name=f"menu-{layout}")
        user = USER_MODEL.objects.create(username=f"menu-{layout}")
        menu = _menu_with_designs(
            f"Isolated {layout}",
            layout,
            menu_theme,
            text="Text item {{ user.username }}",
        )
        request = RequestFactory().get("/")

        context = menu.get_preview_context(request, "html")
        context.update(
            {
                **PAGE_DESIGN_CONTEXT,
                "daisyui_theme": page_theme,
                "daisie_visibility_scope": "menu",
                "logo_url": LOGO_URL,
                "menu_css": "",
                "request": request,
                "user": user,
            }
        )
        html = render_to_string("wagtail_daisIE/blocks/menu_block.html", context)

        for css in PAGE_DESIGN_CONTEXT.values():
            assert css not in html

        assert "p-6" in html
        assert "background: #123456" in html
        assert "text-secondary" in html
        assert f'[data-theme="{menu_theme.name}"]' in html
        assert f"Text item {user.username}" in html
        assert "Button item" in html
        assert "Card item" in html
        assert "Acme" in html
        assert html.count(f'src="{LOGO_URL}"') == 1
        assert html.count('alt="Acme logo"') == 1

    def test_preview_and_live_menu_markup_match(self):
        menu_theme = DaisyUITheme.objects.create(name="preview-theme")
        menu = _menu_with_designs(
            "Preview Menu", "horizontal", menu_theme, branding=False
        )
        request = RequestFactory().get("/")

        preview_context = menu.get_preview_context(request, "html")
        preview_context.update(
            {
                **PAGE_DESIGN_CONTEXT,
                "daisie_visibility_scope": "menu",
                "logo_url": LOGO_URL,
                "menu_css": "",
                "request": request,
            }
        )
        preview = render_to_string(
            "wagtail_daisIE/blocks/menu_block.html", preview_context
        )

        live = _render(
            menu.name,
            {
                **PAGE_DESIGN_CONTEXT,
                "daisyui_theme": preview_context["daisyui_theme"],
                "logo_url": LOGO_URL,
                "request": request,
            },
        )

        assert live == preview
        for css in PAGE_DESIGN_CONTEXT.values():
            assert css not in live


class TestMegamenuLinkList:
    def test_plain_link_and_trigger_share_item_contract(self):
        menu = _link_menu(
            "Megamenu contract", "megamenu", include_plain=True, item_style=True
        )
        html = _render(menu.name)

        plain_tag = re.search(r'<a href="/plain"[^>]*>', html)
        assert plain_tag is not None
        plain_classes = _classes(plain_tag.group(0))
        assert {"link", "link-hover", "text-secondary"} <= plain_classes
        assert 'style="background: #ff0000"' in plain_tag.group(0)

        trigger_tag = re.search(r'<button type="button"[^>]*>', html)
        assert trigger_tag is not None
        trigger_classes = _classes(trigger_tag.group(0))
        assert {
            "megamenu-trigger",
            "link",
            "link-hover",
            "text-secondary",
            "text-accent",
        } <= trigger_classes
        assert f'popovertarget="daisie-mm-{menu.pk}-2"' in trigger_tag.group(0)
        assert 'style="background: #ff0000"' in trigger_tag.group(0)

    def test_megamenu_link_list_renders_panel_design_and_isolates_nested_links(self):
        menu = _link_menu("Megamenu panel", "megamenu", item_style=True)
        html = _render(menu.name)

        panel_tag = re.search(r'<div id="daisie-mm-[^"]+"[^>]*>', html)
        assert panel_tag is not None
        panel_classes = _classes(panel_tag.group(0))
        assert "p-3" in panel_classes
        assert "text-secondary" not in panel_classes
        assert "background: #abcdef" in panel_tag.group(0)
        assert "background: #ff0000" not in panel_tag.group(0)

        nested_tag = re.search(r'<a href="/nested"[^>]*>', html)
        assert nested_tag is not None
        nested_classes = _classes(nested_tag.group(0))
        assert {"link", "link-hover", "text-accent"} <= nested_classes
        assert "text-secondary" not in nested_classes
        assert "background: #ff0000" not in nested_tag.group(0)

    def test_link_list_design_renders_in_normal_menu_layout(self):
        menu = _link_menu("Horizontal list", "horizontal")
        html = _render(menu.name)

        wrapper_tag = re.search(r'<div class="[^"]*\bp-3\b[^"]*"[^>]*>', html)
        assert wrapper_tag is not None
        wrapper_classes = _classes(wrapper_tag.group(0))
        assert "p-3" in wrapper_classes
        assert "text-secondary" in wrapper_classes
        assert "background: #abcdef" in wrapper_tag.group(0)

        nested_tag = re.search(r'<a href="/nested"[^>]*>', html)
        assert nested_tag is not None
        nested_classes = _classes(nested_tag.group(0))
        assert "text-secondary" not in nested_classes
        assert "text-accent" in nested_classes


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

    def test_branding_ignores_item_defaults_and_keeps_own_design(self):
        block = MenuBranding()
        value_data = {
            "logo": {
                "image_source": "dynamic",
                "image_expression": "{{ logo_url }}",
                "alt": "Acme logo",
                "design": {"size": {"size": "h-8"}},
            },
            "wordmark": {
                "text": "Acme",
                "design": {"typography": {"text_color": "text-accent"}},
            },
            "destination": [],
            "open_in_new_tab": False,
            "design": {
                "padding": {"all_padding": "p-3"},
                "background": [
                    {
                        "type": "layer",
                        "value": {"layer_type": "solid", "color": "#abcdef"},
                    }
                ],
            },
            "audience": {},
        }
        parent_context = {
            "menu_default_css": "p-4 text-secondary",
            "menu_default_style": "background: red",
            "logo_url": LOGO_URL,
        }

        html = block.render(block.to_python(value_data), context=parent_context)
        assert "p-3" in html
        assert "background: #abcdef" in html
        assert "text-accent" in html
        assert "h-8" in html
        assert f'src="{LOGO_URL}"' in html
        assert 'alt="Acme logo"' in html
        assert "p-4" not in html
        assert "text-secondary" not in html
        assert "background: red" not in html

        value_data["logo"]["alt"] = ""
        fallback_html = block.render(
            block.to_python(value_data), context=parent_context
        )
        assert 'alt="Acme"' in fallback_html


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
