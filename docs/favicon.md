# Favicon and PWA manifest

Admins set a favicon and web-app metadata under **Design → Favicon**. Templates
render whichever favicon is configured, using the PWA technique (icon set plus a
`manifest.json`, `browserconfig.xml` and theme colour).

Provided by the required `wagtail_daisIE.assets` app (alongside
`DaisyUIIconSource`).

## Configuration

Open **Design → Favicon**. One global row covers every site; add a row with a
**Site** set to override it for that site.

| Field | Purpose |
|-------|---------|
| **Favicon image** | A square, transparent PNG (1024×1024 works best). |
| **App name** / **Short name** | `name` / `short_name` in the manifest. |
| **Theme colour** / **Background colour** | Hex colours for the manifest and `theme-color`. |
| **Display** | `standalone`, `minimal-ui`, `fullscreen` or `browser`. |

## URLs

Include the favicon URLs in your project root URLconf, **before** the Wagtail
page serving rules:

```python
# urls.py
(path("", include("wagtail_daisIE.favicon.urls")),)
```

This exposes:

* `/manifest.json` — the web-app manifest;
* `/browser-config.xml` — the Microsoft tile definition;
* `/favicon.ico` — redirects to the 32×32 rendition.

## Rendering

Add the tag to your `<head>`:

```django
{% load wagtail_daisIE_tags %}
<head>
    ...
    {% daisyui_favicon %}
</head>
```

It emits nothing when no favicon is configured. The bundled page templates (error
pages, form pages, allauth layouts and the demo base) already include it.

The reference implementation this follows is the unmaintained
[`wagtail-favicon`](https://github.com/octavenz/wagtail-favicon) project; here it
is a snippet in the Design menu rather than a `wagtail.contrib.settings` model.
