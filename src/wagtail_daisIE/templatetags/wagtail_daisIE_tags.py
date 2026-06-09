from django import template
from django.utils.safestring import mark_safe


register = template.Library()


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
