"""Optional Celery task for background Tailwind compilation."""

from __future__ import annotations

import logging

from . import artifacts, compiler


logger = logging.getLogger(__name__)


def compile_tailwind_css(token: str) -> bool:
    """Compile the cached input for ``token`` and store the result."""
    input_stylesheet = artifacts.get_input(token)
    if input_stylesheet is None:
        logger.warning("Tailwind input artifact %s is missing", token)
        return False

    try:
        output = compiler.compile_input_stylesheet(input_stylesheet)
    except Exception:  # boundary: Celery worker failure
        logger.exception("Tailwind Celery compilation failed for %s", token)
        artifacts.store_error(token, "compilation failed")
        return False

    artifacts.store_output(token, output)
    return True


try:  # pragma: no cover - exercised only when celery is installed
    from celery import shared_task

    compile_tailwind_css = shared_task(
        name="wagtail_daisIE.tailwindcss.compile_tailwind_css"
    )(compile_tailwind_css)
except ImportError:
    pass


__all__ = ["compile_tailwind_css"]
