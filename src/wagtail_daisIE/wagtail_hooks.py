import json

from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.urls import include, path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.i18n import JavaScriptCatalog
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet

from .context import (
    get_current_form_fields,
    set_current_form_fields,
    set_current_theme,
    theme_from_instance,
)
from .dynamic.views import object_options
from .errors.view_sets import ErrorViewSetGroup
from .help import GuideIndexView, GuidePageView
from .icons.providers.iconify import ICONIFY_ICON_SCRIPT
from .icons.views import icon_search
from .view_sets import DaisyUIViewSetGroup


# Register the design view set group.
# -- START --
@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        "wagtail_daisIE/icons/palette.svg",
    ]


register_snippet(DaisyUIViewSetGroup)
# -- END --

# Register the email snippet view set group (optional notifications app).
if apps.is_installed("wagtail_daisIE.notifications"):
    from .notifications.view_sets import EmailViewSetGroup

    register_snippet(EmailViewSetGroup)


@hooks.register("register_admin_viewset")
def register_allauth_page_viewset():
    if not apps.is_installed("wagtail_daisIE.allauth_ui"):
        return []
    from .allauth_ui.view_sets import AllauthPageOverrideViewSet

    return AllauthPageOverrideViewSet()


@hooks.register("register_admin_viewset")
def register_email_template_viewset():
    if not apps.is_installed("wagtail_daisIE.notifications"):
        return []
    from .notifications.view_sets import EmailTemplateViewSet

    return EmailTemplateViewSet()


@hooks.register("register_admin_viewset")
def register_audience_viewset():
    if not apps.is_installed("wagtail_daisIE.notifications"):
        return []
    from .notifications.view_sets import AudienceViewSet

    return AudienceViewSet()


@hooks.register("register_admin_viewset")
def register_email_campaign_viewset():
    if not apps.is_installed("wagtail_daisIE.notifications"):
        return []
    from .notifications.view_sets import EmailCampaignViewSet

    return EmailCampaignViewSet()


@hooks.register("register_admin_viewset")
def register_allauth_email_viewset():
    if not apps.is_installed("wagtail_daisIE.allauth_emails"):
        return []
    from .allauth_emails.view_sets import AllauthEmailOverrideViewSet

    return AllauthEmailOverrideViewSet()


# Register the error page snippet view set group.
register_snippet(ErrorViewSetGroup)


# Set the current theme for the page/menu being created/edited.
# -- START --
@hooks.register("before_create_page")
def _set_theme_before_create_page(request, parent_page, page_class):
    set_current_theme(theme_from_instance(parent_page))


@hooks.register("before_edit_page")
def _set_theme_before_edit_page(request, page):
    set_current_theme(theme_from_instance(page))


@hooks.register("before_create_snippet")
def _set_theme_before_create_snippet(request, model):
    set_current_theme(theme_from_instance(model))


@hooks.register("before_edit_snippet")
def _set_theme_before_edit_snippet(request, instance):
    set_current_theme(theme_from_instance(instance))


# -- END --


# Register the coloris script and CSS.
# -- START --
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


# -- END --


# Offer the page's form fields as choices for the ``form_field`` body block.
# -- START --
def _form_page_fields(page):
    from .forms.models import DaisieFormPage

    if not isinstance(page, DaisieFormPage):
        return []
    return [
        {"name": field.clean_name, "label": field.label}
        for field in page.get_form_fields()
        if field.clean_name
    ]


@hooks.register("before_create_page")
def _set_form_fields_before_create_page(request, parent_page, page_class):
    set_current_form_fields(())


@hooks.register("before_edit_page")
def _set_form_fields_before_edit_page(request, page):
    set_current_form_fields(_form_page_fields(page))


# -- END --


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
        path(
            "dynamic/objects/",
            object_options,
            name="dynamic_object_options",
        ),
        path("guide/", GuideIndexView.as_view(), name="guide"),
        path(
            "guide/<slug:slug>/",
            GuidePageView.as_view(),
            name="guide-page",
        ),
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


@hooks.register("register_help_menu_item")
def register_help_menu_item():
    return MenuItem(
        _("DaisyUI Editor Guide"),
        reverse("wagtail_daisIE:guide"),
        name="daisyui-editor-guide",
        icon_name="help",
        order=1200,
    )


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


# Register the block settings script.


@hooks.register("insert_global_admin_js")
def register_block_settings_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/block_settings.js"),
    )


# Register the feed model help script.


@hooks.register("insert_global_admin_js")
def register_feed_help_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/feed_help.js"),
    )


# Register the dynamic context-model metadata for the binding block.
# -- START --
@hooks.register("insert_global_admin_js")
def register_context_models_js():
    from .dynamic.registry import get_context_models_state

    state_json = json.dumps(get_context_models_state())
    return format_html(
        "<script type='text/javascript'>window.WAGTAIL_DAISIE_CONTEXT_MODELS = {};</script>",
        mark_safe(state_json),  # noqa: S308
    )


@hooks.register("insert_global_admin_js")
def register_context_binding_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/context_binding_block.js"),
    )


# Feed available context values to the draftail_text_utils dynamic-link control.
@hooks.register("insert_global_admin_js")
def register_dynamic_link_context_js():
    if not apps.is_installed("draftail_text_utils"):
        return ""
    from .dynamic.link_context import get_dynamic_link_groups

    groups_json = json.dumps(get_dynamic_link_groups(), cls=DjangoJSONEncoder)
    script = (
        "window.draftailTextUtils = window.draftailTextUtils || {};"
        "window.draftailTextUtils.dynamicLinkContext = "
        f"{groups_json};"
    )
    return format_html(
        "<script type='text/javascript'>{}</script>",
        mark_safe(script),  # noqa: S308
    )


@hooks.register("insert_global_admin_js")
def register_forms_admin_js():
    return format_html(
        '<script src="{}"></script>',
        static("wagtail_daisIE/js/forms_admin.js"),
    )


@hooks.register("insert_global_admin_js")
def register_form_fields_js():
    state_json = json.dumps(get_current_form_fields())
    return format_html(
        "<script type='text/javascript'>window.WAGTAIL_DAISIE_FORM_FIELDS = {};</script>",
        mark_safe(state_json),  # noqa: S308
    )


@hooks.register("insert_global_admin_css")
def register_block_settings_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_daisIE/css/block_settings.css"),
    )


# -- END --


# Register the context binding styles.


@hooks.register("insert_global_admin_css")
def register_context_binding_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_daisIE/css/context_binding.css"),
    )


# Register the icon chooser script and CSS.
# -- START --
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


# -- END --


# Detail page admin shortcuts: jump between a page and its source record.
# -- START --
@hooks.register("register_page_listing_more_buttons")
def detail_page_listing_buttons(page, user, next_url=None):
    from django.contrib.admin.utils import quote
    from django.urls import NoReverseMatch, reverse
    from wagtail.admin import widgets as wagtailadmin_widgets

    source = getattr(page.specific, "source", None)
    if source is None or source.pk is None:
        return
    model = type(source)
    try:
        url = reverse(
            f"wagtailsnippets_{model._meta.app_label}_{model._meta.model_name}:edit",
            args=[quote(source.pk)],
        )
    except NoReverseMatch:
        return
    yield wagtailadmin_widgets.Button(
        _("Edit source record"), url, icon_name="edit", priority=60
    )


@hooks.register("register_snippet_listing_buttons")
def detail_snippet_listing_buttons(snippet, user, next_url=None):
    from wagtail.admin.ui.menus import MenuItem

    from .detail_pages.bridges import find_detail_page
    from .detail_pages.registry import detail_page_for_instance

    try:
        config = detail_page_for_instance(snippet)
        if config is None:
            return
        page = find_detail_page(config, snippet)
    except Exception:
        return
    if page is None or not page.live:
        return
    yield MenuItem(_("View detail page"), page.url, icon_name="doc-empty", priority=90)


# -- END --
