# CSS pipeline (runtime Tailwind + daisyUI)

`wagtail-daisIE` compiles Tailwind CSS from the classes rendered on each page.
Python stores the compilation input in the shared cache and writes a per-page
JSON config. The browser fetches or compiles the stylesheet and injects it into
the placeholder. Python never writes compiled CSS into the HTML.

```text
Django response
  └─ TailwindCSSMiddleware
       ├─ extract class + data-daisie-selected-class tokens
       ├─ build the Tailwind input
       ├─ store input in cache under a content token
       ├─ blocking / executor / Celery / browser plan
       └─ inject JSON config only

Browser
  ├─ loads committed daisie-base.css
  ├─ tailwind_jit.js reads the config
  ├─ fetch/poll artifact, HTTP POST, or WebSocket
  ├─ validates and injects into #daisyui-jit-styles
  └─ emits document events
```

## Installation

```python
# settings.py
INSTALLED_APPS += ["django_tailwind_cli"]
TAILWIND_CLI_USE_DAISY_UI = True

MIDDLEWARE += [
    "django_htmx.middleware.HtmxMiddleware",
    "wagtail_daisIE.middleware.TailwindCSSMiddleware",
]
```

```python
# urls.py
(path("daisie/tailwind/", include("wagtail_daisIE.tailwindcss.urls")),)
```

```django
{% load wagtail_daisIE_tags %}
<head>
    {% daisyui_all_themes_css daisyui_theme %}
    {% daisyui_jit_placeholder %}
</head>
```

The tag emits:

1. `<link rel="stylesheet" href=".../daisie-base.css">`
2. `<style id="daisyui-jit-styles"></style>`
3. an empty JSON config element
4. `tailwind_jit.js` as a module

## Base stylesheet

The minimal input lives in `src/wagtail_daisIE/tailwind/input.css`:

```css
@import "tailwindcss" source(none);
@plugin "@tailwindcss/typography";
@plugin "daisyui" { include: button, input, menu, megamenu, navbar, footer }
```

Build it with:

```bash
just build-css
```

The output is the committed
`src/wagtail_daisIE/static/wagtail_daisIE/css/daisie-base.css`. It includes
preflight and the six core components, reducing the flash before JIT CSS
arrives.

The JIT stylesheet deliberately imports only theme and utilities:

```css
@layer theme, base, components, utilities;

@import 'tailwindcss/theme.css' layer(theme);
@import 'tailwindcss/utilities.css' layer(utilities) source(none);
```

The three directives are required: theme supplies build-time theme values,
utilities emits utilities, and the layer order keeps components below
utilities. Preflight is omitted because the base stylesheet already contains
it.

## Compilation modes

| Server | Celery | API | Mode | Execution |
|---|---|---|---|---|
| WSGI | no | none | `fetch` | Python blocks, compiles, stores |
| WSGI | no | HTTP | `http` | Browser fetches input, POSTs |
| WSGI | no | WS | `ws` | Browser streams over WebSocket |
| WSGI | yes | none | `poll` | Celery compiles and stores |
| WSGI | yes | HTTP/WS | same as no Celery | Browser |
| ASGI | no | none | `poll` | bounded executor compiles |
| ASGI | no | HTTP | `poll` | executor calls HTTP API |
| ASGI | no | WS | `ws` | Browser WebSocket |
| ASGI | yes | none | `poll` | Celery |
| ASGI | yes | HTTP/WS | same as ASGI no Celery | Python HTTP / Browser WS |
| any | any | cache hit | `fetch` | immutable artifact |

API configuration:

```python
TAILWIND_CSS_API = {
    "url": "https://css.example/compile",
    "transport": "http",  # or "websocket"
    "token": "",  # Python-only
    "timeout": 30,
}
```

A legacy URL string is accepted and its transport is inferred. The token is
never rendered into HTML: token-protected HTTP APIs use Python paths; a
token-protected WebSocket API requires a project proxy (W007).

HTTP contract:

```http
POST /compile?nonce=<64 lowercase hex characters>
{"stylesheet": "..."}
```

Response: `{"stylesheet": "..."}`.

WebSocket contract:

```text
wss://api.example.com/compile?nonce=<64 lowercase hex characters>

{"type": "compile", "stylesheet": "..."}
{"type": "chunk", "css": "..."}
{"type": "done"}
{"type": "error", "message": "..."}
```

Nonces are always generated in Python (`secrets.token_hex(32)`). Python appends
the nonce to the final HTTP/WS URL before calling the API. Browser API configs
receive the finished URL; JavaScript never generates, appends or forwards a
nonce. Existing query parameters are preserved exactly and any previous
`nonce` parameter is replaced. Each config produces one request/connection, so
no nonce is reused by the client. The API server must validate single use and
reject replays. Query parameters can appear in access logs and proxies; redact
the `nonce` parameter if required. It is not a secret, but must not be logged at
INFO or placed in event details.

## Browser behavior

`tailwind_jit.js`:

- scans config scripts at load and watches for htmx fragment configs with a
  `MutationObserver`;
- emits `daisie:tailwind-pending`, `daisie:tailwind-ready` and
  `daisie:tailwind-error` on `document`;
- fetches immutable artifacts, polls with 250 ms → 2 s backoff and a 60 s
  timeout, or streams WebSocket chunks;
- validates CSS before sending and after receiving;
- buffers WebSocket chunks and flushes only complete CSS statements;
- injects into `#daisyui-jit-styles`;
- never reads or sends an API token.

Consumers can listen for `daisie:tailwind-pending` to display plain content
styled by `daisie-base.css` while compilation runs.

## Artifact URLs

- `/daisie/tailwind/input/<token>.css` — compilation input for browser HTTP/WS.
- `/daisie/tailwind/artifact/<token>.css` — compiled CSS.
- Tokens are SHA-256 content hashes.
- Responses use `text/css`, `Cache-Control: public, max-age=31536000,
  immutable` and `X-Content-Type-Options: nosniff`.
- Pending artifacts 404; failed artifacts return a generic 500.

Use a shared cache (Redis/DB) for Celery, multiple ASGI workers, or multiple
web workers. `LocMemCache` is only safe for a single process; W009 warns.

## Failure behavior

- Compilation errors are logged and stored as a generic error artifact.
- The browser emits `daisie:tailwind-error`.
- The base stylesheet remains loaded.
- A missing URLconf/compiler/base stylesheet produces system-check warnings
  W003–W009.
- Unknown response encodings are skipped; gzip/deflate are supported.

## Verification

1. `just build-css`.
2. Render a page: base CSS is linked and the JSON config is present.
3. Confirm compiled CSS is **not** in the HTML.
4. Check the mode matches the matrix; cache hits use `fetch`.
5. Trigger an htmx fragment and confirm the observer processes its config.
6. Listen for the three `daisie:tailwind-*` events.
7. `just lint && just test`.
