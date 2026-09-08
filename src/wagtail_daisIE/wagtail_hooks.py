import json

from django.conf import settings
from django.templatetags.static import static
from django.urls import include, path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.i18n import JavaScriptCatalog
from wagtail import hooks
from wagtail.snippets.models import register_snippet

from .context import set_current_theme, theme_from_instance
from .icons.providers.iconify import ICONIFY_ICON_SCRIPT
from .icons.views import icon_search
from .view_sets import DaisyUIViewSetGroup


# Register the design view set group.


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        "wagtail_daisIE/icons/palette.svg",
    ]


register_snippet(DaisyUIViewSetGroup)

# Set the current theme for the page/menu being created/edited.


@hooks.register("before_create_page")
def _set_theme_before_create_page(request, page):
    set_current_theme(theme_from_instance(page))


@hooks.register("before_edit_page")
def _set_theme_before_edit_page(request, page):
    set_current_theme(theme_from_instance(page))


@hooks.register("before_create_snippet")
def _set_theme_before_create_snippet(request, page):
    set_current_theme(theme_from_instance(page))


@hooks.register("before_edit_snippet")
def _set_theme_before_edit_snippet(request, instance):
    set_current_theme(theme_from_instance(instance))


# Register admin views


@hooks.register("register_admin_urls")
def register_admin_urls():
    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["wagtail_daisIE"]),
            name="javascript_catalog",
        ),
        path("icons/search/", icon_search, name="icon_search"),
        # Add other package-scoped URLs here so they are access-restricted to the admin.
    ]

    return [
        path(
            "wagtail_daisIE/",
            include(
                (urls, "wagtail_daisIE"),
                namespace="wagtail_daisIE",
            ),
        )
    ]


# Register the audience rules JS.


@hooks.register("insert_global_admin_js")
def register_audience_rules_js():
    rules = getattr(settings, "WAGTAIL_DAISIE_AUDIENCE_RULES", {})
    rules_json = json.dumps(rules)
    rules_js = f"window.WAGTAIL_DAISIE_AUDIENCE_RULES = {rules_json};"
    return format_html(
        "<script type='text/javascript'>{}</script>",
        mark_safe(rules_js),  # noqa: S308
    )


# Register the background layer admin JS.


@hooks.register("insert_global_admin_js")
def register_background_layer_admin_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/background_layer_admin.js"),
    )


# Register the block settings script and CSS.


@hooks.register("insert_global_admin_js")
def register_block_settings_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/block_settings.js"),
    )


@hooks.register("insert_global_admin_css")
def register_block_settings_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_daisIE/css/block_settings.css"),
    )


# Register the icon chooser script and CSS.


@hooks.register("insert_global_admin_css")
def register_icon_chooser_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_daisIE/css/icon_chooser.css"),
    )


@hooks.register("insert_global_admin_js")
def register_icon_chooser_js():
    return format_html(
        '<script src="{}"></script><script src="{}"></script>',
        ICONIFY_ICON_SCRIPT,
        static("wagtail_daisIE/js/icon_chooser.js"),
    )


# Register the coloris script and CSS.


@hooks.register("insert_global_admin_css")
def register_coloris_css():
    coloris_css = "colorfield/coloris/coloris.css"
    if not settings.DEBUG:
        coloris_css = "colorfield/coloris/coloris.min.css"
    return format_html('<link rel="stylesheet" href="{}">', static(coloris_css))


@hooks.register("insert_global_admin_js")
def register_coloris_js():
    coloris_js = "colorfield/coloris/coloris.js"
    if not settings.DEBUG:
        coloris_js = "colorfield/coloris/coloris.min.js"
    return format_html('<script src="{}"></script>', static(coloris_js))
