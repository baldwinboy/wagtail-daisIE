# CSS pipeline (committed Tailwind + daisyUI)

`wagtail-daisIE` ships a **prebuilt, committed stylesheet**. There is no runtime
compiler, no CLI, and no Node.js in production.

```
choices/*  ──►  daisie_safelist  ──►  tailwind/safelist.css
                                        │
tailwind/input.css  ──►  tailwindcss CLI  ──►  static/wagtail_daisIE/css/daisie.css
                                                                   │
                                          {% daisyui_styles %} ────┘  (render-blocking <link>)
```

## How it works

1. **Safelist** — the design system builds class strings at runtime
   (`block_css`), so Tailwind cannot discover them by scanning templates.
   `manage.py daisie_safelist` walks `choices/*` (plus the feed layout literals)
   and writes `@source inline(...)` directives to `tailwind/safelist.css`.
2. **Build** — `tailwind/input.css` (`@import "tailwindcss"` + `@plugin
   "daisyui"` + the extended typography scale + `@import "./safelist.css"`) is
   compiled by the npm `tailwindcss` CLI into the committed
   `src/wagtail_daisIE/static/wagtail_daisIE/css/daisie.css`.
3. **Serve** — `{% daisyui_styles %}` emits a render-blocking
   `<link rel="stylesheet" …>` so there is no flash of unstyled content.
4. **Arbitrary colours** — `bg-[#0080ff]`, `decoration-[#…]` and their
   `hover:`/`active:` variants are unpredictable, so
   `wagtail_daisIE.middleware.ArbitraryCSSMiddleware` scans the rendered HTML and
   injects the handful of rules they need, cached by token-set hash.

`{% daisyui_theme_full_css theme %}` emits the theme's `--color-*`, `--radius-*`,
`--size-*`, `--font-*` custom properties (and `.font-<role>` rules) inline.

## Regenerating

```bash
just build-css   # daisie_safelist, then npm run build:css
```

Commit the updated `tailwind/safelist.css` and `static/wagtail_daisIE/css/daisie.css`
after changing any class choices.

## Configuration

```python
# settings.py
MIDDLEWARE += [
    "wagtail_daisIE.middleware.ArbitraryCSSMiddleware",
]
```

```django
{% load wagtail_daisIE_tags %}
{% daisyui_styles %}
{% daisyui_theme_full_css daisyui_theme %}
```

## Notes

- **Storage** — `daisie.css` is a normal static file (collected by
  `collectstatic`); arbitrary-colour CSS is cached in the default cache
  (`daisie:arbitrary:css:<sha256>`).
- **Failure mode** — if `ArbitraryCSSMiddleware` fails it logs a warning and
  leaves the response untouched; pages never 500.
- **Backgrounds** — design backgrounds are `BackgroundStreamBlock` values
  rendered as an inline `block_style`, not classes.

## Verifying

1. Render a page and confirm `<link rel="stylesheet" href="…/daisie.css">` is in
   `<head>`.
2. Use a custom colour (e.g. `bg-[#0080ff]`) and confirm the rule is injected.
3. Change a choice in `choices/*`, run `just build-css`, and confirm the class
   is present in the rebuilt `daisie.css`.
