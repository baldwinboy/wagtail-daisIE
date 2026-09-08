def icon_assets(request):
    """Expose the enabled icon providers' head assets to templates.

    Add ``wagtail_daisIE.icons.context_processors.icon_assets`` to the
    ``context_processors`` option of your ``TEMPLATES`` setting to include the
    assets automatically; otherwise use ``{% daisyui_icon_assets %}``.
    """
    from .registry import icon_assets as get_icon_assets

    return {"daisyui_icon_assets": get_icon_assets()}
