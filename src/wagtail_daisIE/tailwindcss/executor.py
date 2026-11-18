"""Bounded background executor for ASGI and fallback compilation."""

from __future__ import annotations

import logging
import threading

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings


logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_EXECUTOR: ThreadPoolExecutor | None = None


def submit_background(fn: Callable, *args) -> bool:
    """Submit work to the shared executor; return whether it was accepted."""
    try:
        _get_executor().submit(_guarded, fn, args)
    except RuntimeError:  # pragma: no cover - interpreter shutdown
        logger.warning("Tailwind background executor is unavailable", exc_info=True)
        return False
    return True


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        with _LOCK:
            if _EXECUTOR is None:
                workers = int(
                    getattr(settings, "WAGTAIL_DAISIE_TAILWIND_EXECUTOR_WORKERS", 2)
                )
                _EXECUTOR = ThreadPoolExecutor(
                    max_workers=max(1, workers),
                    thread_name_prefix="daisie-tailwind",
                )
    return _EXECUTOR


def _guarded(fn: Callable, args: tuple) -> None:
    try:
        fn(*args)
    except Exception:  # pragma: no cover - worker boundary
        logger.exception("Tailwind background compilation failed")
