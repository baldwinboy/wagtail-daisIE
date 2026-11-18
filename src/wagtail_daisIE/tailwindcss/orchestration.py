"""Resolve and execute a Tailwind compilation plan for one response."""

from __future__ import annotations

import logging

from importlib.util import find_spec

from django.conf import settings
from django.utils.module_loading import import_string

from . import artifacts, compiler, executor, placeholder
from .api import TailwindAPI, get_tailwind_api, js_api_config, new_nonce


logger = logging.getLogger(__name__)

_DEFAULT_CELERY_TASK = "wagtail_daisIE.tailwindcss.tasks.compile_tailwind_css"


def prepare_html(request, html_text: str, *, fragment: bool) -> str | None:
    """Extract classes, plan compilation, and inject the JS configuration."""
    classnames = compiler.extract_class_names(html_text, fragment=fragment)
    if not classnames:
        return None

    input_stylesheet = compiler.build_input_stylesheet(
        classnames,
        fragment=fragment,
    )
    if not input_stylesheet:
        return None

    token = artifacts.store_input(input_stylesheet)
    config = _plan(request, token, input_stylesheet)
    return placeholder.inject_config(
        html_text,
        config,
        fragment=fragment,
        key=token,
    )


def _plan(request, token: str, input_stylesheet: str) -> dict:
    if artifacts.get_output(token) is not None:
        return _config("fetch", token)

    api = get_tailwind_api()
    is_asgi = _is_asgi(request)
    celery = _celery_available()

    if api is not None and api.transport == "http":
        if api.token:
            # A token is Python-only. Browser HTTP would expose it.
            if is_asgi:
                if _submit(_compile_http_and_store, token, input_stylesheet, api):
                    return _config("poll", token)
                _compile_http_and_store(token, input_stylesheet, api)
                return _config("fetch", token)
            if celery and _dispatch_celery(token):
                return _config("poll", token)
            _compile_http_and_store(token, input_stylesheet, api)
            return _config("fetch", token)

        if is_asgi:
            if _submit(_compile_http_and_store, token, input_stylesheet, api):
                return _config("poll", token)
            _compile_http_and_store(token, input_stylesheet, api)
            return _config("fetch", token)
        return _config("http", token, api)

    if api is not None and api.transport == "websocket":
        if api.token:
            logger.warning(
                "Token-protected WebSocket Tailwind APIs cannot be used from "
                "the browser; falling back to the no-API path."
            )
        else:
            return _config("ws", token, api)

    if celery and _dispatch_celery(token):
        return _config("poll", token)

    if is_asgi:
        if _submit(_compile_and_store, token, input_stylesheet):
            return _config("poll", token)
        _compile_and_store(token, input_stylesheet)
        return _config("fetch", token)

    _compile_and_store(token, input_stylesheet)
    return _config("fetch", token)


def _config(mode: str, token: str, api: TailwindAPI | None = None) -> dict:
    config: dict = {
        "mode": mode,
        "poll": {
            "initial": _int_setting("WAGTAIL_DAISIE_TAILWIND_POLL_INTERVAL", 250),
            "max": _int_setting("WAGTAIL_DAISIE_TAILWIND_POLL_MAX_INTERVAL", 2000),
            "timeout": _int_setting("WAGTAIL_DAISIE_TAILWIND_POLL_TIMEOUT", 60000),
        },
    }

    if mode in {"fetch", "poll"}:
        url = artifacts.output_url(token)
        if not url:
            return {"mode": "error", "poll": config["poll"]}
        config["cssUrl"] = url
        return config

    if mode in {"http", "ws"}:
        url = artifacts.input_url(token)
        api_config = js_api_config(api, nonce=new_nonce()) if api is not None else None
        if not url or api_config is None:
            return {"mode": "error", "poll": config["poll"]}
        config["inputUrl"] = url
        config["api"] = api_config
        return config

    return {"mode": "error", "poll": config["poll"]}


def _submit(fn, *args) -> bool:
    return executor.submit_background(fn, *args)


def _compile_and_store(token: str, input_stylesheet: str) -> None:
    try:
        output = compiler.compile_input_stylesheet(input_stylesheet)
    except Exception:  # boundary: never fail the page or worker
        logger.exception("Tailwind compilation failed for %s", token)
        artifacts.store_error(token, "compilation failed")
        return
    artifacts.store_output(token, output)


def _compile_http_and_store(
    token: str,
    input_stylesheet: str,
    api: TailwindAPI,
) -> None:
    try:
        from .api import compile_via_http

        output = compile_via_http(input_stylesheet, api)
    except Exception:  # boundary: never fail the page or worker
        logger.exception("Tailwind HTTP compilation failed for %s", token)
        artifacts.store_error(token, "compilation failed")
        return
    artifacts.store_output(token, output)


def _dispatch_celery(token: str) -> bool:
    task_path = getattr(
        settings,
        "WAGTAIL_DAISIE_TAILWIND_CELERY_TASK",
        _DEFAULT_CELERY_TASK,
    )
    try:
        task = import_string(task_path)
        delay = getattr(task, "delay", None)
        if not callable(delay):
            logger.warning("Celery task %s has no delay()", task_path)
            return False
        delay(token)
    except Exception:  # boundary: broker or import failure
        logger.warning("Could not dispatch Tailwind Celery task", exc_info=True)
        return False
    return True


def _celery_available() -> bool:
    if find_spec("celery") is None:
        return False
    return any(
        getattr(settings, name, "")
        for name in (
            "CELERY_BROKER_URL",
            "CELERY_BROKER_READ_URL",
            "CELERY_BROKER_WRITE_URL",
        )
    )


def _is_asgi(request) -> bool:
    if hasattr(request, "scope"):
        return True
    return bool(getattr(settings, "ASGI_APPLICATION", None))


def _int_setting(name: str, default: int) -> int:
    try:
        value = int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default
