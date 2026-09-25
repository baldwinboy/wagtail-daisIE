from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def daisyui_global_css():
    return static("wagtail_daisIE/css/global.css")


@register.inclusion_tag("wagtail_daisIE/tags/theme.html")
def daisyui_theme_css(theme):
    return {"theme": theme}


@register.simple_tag
def daisyui_theme_inline_css(theme):
    colors = theme.colors.first()
    radii = theme.radii.first()
    sizes = theme.sizes.first()
    effects = theme.effects.first()

    lines = [f'[data-theme="{theme.name}"] {{']
    lines.append(f"  color-scheme: {theme.color_scheme};")

    if colors:
        lines.append("")
        for var_name, value in (
            ("--color-primary", colors.primary),
            ("--color-primary-content", colors.primary_content),
            ("--color-secondary", colors.secondary),
            ("--color-secondary-content", colors.secondary_content),
            ("--color-accent", colors.accent),
            ("--color-accent-content", colors.accent_content),
            ("--color-neutral", colors.neutral),
            ("--color-neutral-content", colors.neutral_content),
            ("--color-base-100", colors.base_100),
            ("--color-base-200", colors.base_200),
            ("--color-base-300", colors.base_300),
            ("--color-base-content", colors.base_content),
            ("--color-info", colors.info),
            ("--color-info-content", colors.info_content),
            ("--color-success", colors.success),
            ("--color-success-content", colors.success_content),
            ("--color-warning", colors.warning),
            ("--color-warning-content", colors.warning_content),
            ("--color-error", colors.error),
            ("--color-error-content", colors.error_content),
        ):
            lines.append(f"  {var_name}: {value};")

    if radii:
        lines.append("")
        lines.append(f"  --radius-selector: {radii.selector};")
        lines.append(f"  --radius-field: {radii.field};")
        lines.append(f"  --radius-box: {radii.box};")

    if sizes:
        lines.append("")
        lines.append(f"  --size-selector: {sizes.selector};")
        lines.append(f"  --size-field: {sizes.field};")
        lines.append(f"  --border: {sizes.border};")

    if effects:
        lines.append("")
        lines.append(f"  --depth: {1 if effects.depth else 0};")
        lines.append(f"  --noise: {1 if effects.noise else 0};")

    lines.append("}")

    return mark_safe("\n".join(lines))  # noqa: S308


# ---------------------------------------------------------------------------
# Blocks extra template tags
# ---------------------------------------------------------------------------


@register.inclusion_tag("wagtail_daisIE/blocks/menu_block.html", takes_context=True)
def daisyui_menu(context, menu_name, css_class=""):
    """Render a DaisyUIMenu snippet by name.

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_menu "Main Navigation" css_class="bg-base-200" %}
    """
    from ..dynamic.resolvers import parse_bindings, resolve_context_models
    from ..models import DaisyUIMenu
    from ..notifications.context import build_context

    request = context.get("request")
    values = build_context(request=request)

    try:
        menu = DaisyUIMenu.objects.get(name=menu_name)
    except DaisyUIMenu.DoesNotExist:
        return {
            "menu": None,
            "menu_items": [],
            "menu_css": css_class,
            "request": request,
            "menu_theme": None,
            "menu_item_css": "",
            **values,
        }

    values.update(resolve_context_models(request, bindings=parse_bindings(menu)))

    return {
        "menu": menu,
        "menu_items": menu.body,
        "menu_css": css_class,
        "request": request,
        "daisyui_theme": context.get("daisyui_theme"),
        "menu_theme": menu.get_theme(),
        "menu_item_css": menu.get_item_css(),
        **values,
    }


@register.inclusion_tag("wagtail_daisIE/tags/background_css.html")
def daisyui_theme_background_css(theme):
    """Render background CSS for a theme.

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_theme_background_css daisyui_theme %}
    """
    return {"theme": theme}


@register.simple_tag
def daisyui_theme_background_inline_css(theme):
    """Return background CSS string for a theme.

    Supports multiple layers: solid colours, gradients with stops, and
    images with positioning, size, and repeat.
    """
    bg = theme.background.first()
    if not bg:
        return ""

    css_value = bg.get_effective_background()
    if not css_value:
        return ""

    lines = [
        f'[data-theme="{theme.name}"], :root:has(.theme-controller[value="{theme.name}"]:checked) {{',
        f"  background: {css_value};",
        "}",
    ]
    return mark_safe("\n".join(lines))  # noqa: S308


@register.inclusion_tag("wagtail_daisIE/tags/font_cdns.html")
def daisyui_theme_font_cdns(theme):
    """Render font CDNs for a theme.

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_theme_font_cdns daisyui_theme %}
    """
    return {"theme": theme}


@register.simple_tag
def daisyui_theme_font_inline_cdns(theme):
    """Return font CDNs string for a theme."""
    font_cdns = theme.font_cdns.all()
    if not font_cdns:
        return ""

    lines = [f'<link rel="stylesheet" href="{cdn.url}">' for cdn in font_cdns]

    return mark_safe("\n".join(lines))  # noqa: S308


@register.inclusion_tag("wagtail_daisIE/tags/font_css.html")
def daisyui_theme_font_css(theme):
    """Render font CSS for a theme.

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_theme_font_css daisyui_theme %}
    """
    return {"theme": theme}


@register.simple_tag
def daisyui_theme_font_inline_css(theme):
    """Return font CSS string for a theme."""
    fonts = theme.fonts.first()
    if not fonts:
        return ""

    font_families = fonts.font_families.all()
    if not font_families:
        return ""

    lines = [
        f'[data-theme="{theme.name}"], :root:has(.theme-controller[value="{theme.name}"]:checked) {{',
        *[f"  --font-{family.__str__}: {family.css_value}" for family in font_families],
        f"  --font-size-base: {fonts.base_font_size};",
        f"  --line-height: {fonts.line_height};",
        "}",
    ]

    return mark_safe("\n".join(lines))  # noqa: S308


@register.inclusion_tag("wagtail_daisIE/tags/full_css.html")
def daisyui_theme_full_css(theme):
    """Render complete theme CSS (colors + radii + sizes + effects + background + fonts).

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_theme_full_css daisyui_theme %}
    """
    return {"theme": theme}


@register.simple_tag
def daisyui_theme_full_inline_css(theme):
    """Return complete theme CSS string."""
    base_css = daisyui_theme_inline_css(theme)
    bg_css = daisyui_theme_background_inline_css(theme)
    font_css = daisyui_theme_font_inline_css(theme)

    parts = [css for css in [base_css, bg_css, font_css] if css]
    return mark_safe("\n\n".join(parts))  # noqa: S308


# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------


@register.simple_tag
def daisyui_icon(value, size=None, color=None, label=None):
    """Render a stored universal icon value.

    Usage::

        {% load wagtail_daisIE_tags %}
        {% daisyui_icon item.icon size="1.25em" label="Home" %}
    """
    from ..icons import render_icon

    return render_icon(value, size=size, color=color, label=label)


@register.inclusion_tag("wagtail_daisIE/tags/icon_assets.html")
def daisyui_icon_assets():
    """Render the head assets required by the enabled icon providers."""
    from ..icons import icon_assets

    return {"assets": icon_assets()}


@register.filter
def is_active(item, request):
    """Return whether a menu item points at the current request path."""
    checker = getattr(item, "is_active", None)
    if callable(checker):
        return checker(request)
    return False


@register.simple_tag
def unplaced_form_fields(page, form):
    """Return the bound fields that ``page.body`` does not already render.

    Fields the author placed with the ``form_field`` body block are skipped so
    they are not repeated in the form's own field loop.
    """
    if form is None:
        return []
    getter = getattr(page, "get_placed_field_names", None)
    placed = set(getter()) if callable(getter) else set()
    return [form[name] for name in form.fields if name not in placed]
