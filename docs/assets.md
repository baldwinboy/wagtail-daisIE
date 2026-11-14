# CSS pipeline (runtime Tailwind + daisyUI)

`wagtail-daisIE` compiles Tailwind CSS from the classes that are actually
rendered on each page. There is no committed stylesheet, no safelist and no CSS
build step.

```text
rendered HTML ──► candidate parser ──► @source inline() patterns
      │                                      │
      └─ class + data-daisie-selected-class  └─ Tailwind + daisyUI compiler
                                              │
                              <style id="daisyui-jit-styles"> in the page
```

## How it works

1. **Render** — templates include `{% daisyui_jit_placeholder %}` in `<head>`.
   The tag emits an empty `<style id="daisyui-jit-styles">`.
2. **Extract** — `TailwindCSSMiddleware` parses the response and reads every
   `class` attribute and every `data-daisie-selected-class` attribute. The
   latter covers classes that `feed_controls.js` applies at runtime. The
   candidate grammar matches Tailwind's Oxide extractor: variants, arbitrary
   values/properties/variables, modifiers, important markers and balanced
   brackets.
3. **Compact** — candidates are grouped into `@source inline()` patterns
   without lossy cross-products. A group is emitted as separate patterns when a
   brace alternative would contain a comma, brace or backslash.
4. **Compile** — the compiler appends the package's frontend CSS sources
   (`typography.css`, `file-picker.css`, `marquee.css`, `menu.css`,
   `richtext.css`, `visibility.css`) to a Tailwind input stylesheet. It uses:
   - `django_tailwind_cli` by default (the **unsafe** path: a local binary), or
   - `TAILWIND_CSS_API` when set (the **safe** path: a remote compiler).
5. **Cache** — the compiled CSS is cached by the sorted class set and mode
   (`full` or `fragment`) in the Django cache for one week.
6. **Inject** — the placeholder is filled. HTML outside the placeholder is not
   reserialized or otherwise changed.

## Configuration

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_tailwind_cli",
]

MIDDLEWARE += [
    "django_htmx.middleware.HtmxMiddleware",
    "wagtail_daisIE.middleware.TailwindCSSMiddleware",
]

TAILWIND_CLI_USE_DAISY_UI = True

# Optional remote compiler (safe path). When set, django_tailwind_cli is not
# imported or required.
TAILWIND_CSS_API = "https://css.example.com/compile"
TAILWIND_CSS_TIMEOUT = 30
```

```django
{% load wagtail_daisIE_tags %}
<head>
    {% daisyui_all_themes_css daisyui_theme %}
    {% daisyui_jit_placeholder %}
</head>
```

`django_tailwind_cli` must be installed and `TAILWIND_CLI_USE_DAISY_UI` must be
`True` for local compilation; system checks W003/W004 warn when either is
missing. The remote service receives:

```json
{"stylesheet": "@import 'tailwindcss' source(none); ..."}
```

and must return:

```json
{"stylesheet": "/* compiled CSS */"}
```

## Outputs and failure modes

- **Full pages** — CSS is written into the existing placeholder. Pages with no
  placeholder are left untouched (admin pages, for example).
- **Error pages** — non-200 HTML responses are processed, so 404/500 templates
  are styled.
- **htmx fragments** — a fragment without a placeholder gets a prepended
  `<style data-daisie-jit>` built without Tailwind preflight. The style is
  swapped in with the fragment.
- **Missing compiler / compile error / cache outage** — the middleware logs and
  leaves the response untouched. A page never fails because CSS failed.
- **Unknown content encodings** — responses using `br`/`zstd` are skipped;
  gzip/deflate are decoded and re-encoded.

## Scanned attributes

Only classes in these attributes are compiled:

- `class`
- `data-daisie-selected-class`

Classes applied by JavaScript must be present in one of them. The package's
own JavaScript already satisfies this: feed toggles use the data attribute and
autocomplete/file-picker classes also appear in the rendered templates or in
the bundled custom CSS.

## Verifying

1. Render a page and confirm the placeholder contains CSS.
2. Render a 404/500 page and confirm it is styled too.
3. Trigger a feed swap and confirm the fragment contains
   `<style data-daisie-jit>`.
4. Add a class only through `data-daisie-selected-class` and confirm it appears
   in the generated `@source inline` input.
5. Run `just lint && just test`.
