def get_draftail_color_palette():
    """
    Return the default DaisyUI theme's colours as a
    draftail_text_utils-compatible colour palette list.

    Returns a list of dicts with "key", "label", and "value" (hex) keys,
    or an empty list if no default theme exists.
    """
    from .models import DaisyUITheme

    try:
        theme = DaisyUITheme.objects.filter(default=True).first()
        if not theme:
            return []
        colors = theme.colors.first()
        if not colors:
            return []
    except Exception:
        return []

    color_fields = [
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("accent", "Accent"),
        ("neutral", "Neutral"),
        ("base_100", "Base"),
        ("base_200", "Base Dark"),
        ("base_300", "Base Darker"),
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    return [
        {
            "key": field_name,
            "label": label,
            "value": getattr(colors, field_name)[:7],
        }
        for field_name, label in color_fields
    ]
