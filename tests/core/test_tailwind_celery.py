from unittest.mock import Mock

import pytest

from django.core.cache import cache
from django.test import override_settings

from wagtail_daisIE.tailwindcss import artifacts, orchestration, tasks


pytestmark = pytest.mark.django_db


def test_task_stores_output(monkeypatch):
    cache.clear()
    token = artifacts.store_input("input")
    monkeypatch.setattr(
        tasks.compiler,
        "compile_input_stylesheet",
        lambda stylesheet: "/* compiled */",
    )
    assert tasks.compile_tailwind_css(token) is True
    assert artifacts.get_output(token) == "/* compiled */"
    cache.clear()


def test_task_stores_generic_error(monkeypatch):
    cache.clear()
    token = artifacts.store_input("input")
    monkeypatch.setattr(
        tasks.compiler,
        "compile_input_stylesheet",
        lambda stylesheet: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert tasks.compile_tailwind_css(token) is False
    assert artifacts.get_error(token) == "compilation failed"
    cache.clear()


def test_celery_availability_requires_broker(monkeypatch):
    monkeypatch.setattr(orchestration, "find_spec", lambda name: object())
    with override_settings(CELERY_BROKER_URL="redis://localhost/0"):
        assert orchestration._celery_available() is True
    with override_settings(CELERY_BROKER_URL=""):
        assert orchestration._celery_available() is False


def test_dispatch_uses_task_delay(monkeypatch):
    task = Mock()
    monkeypatch.setattr(orchestration, "import_string", lambda path: task)
    assert orchestration._dispatch_celery("token") is True
    task.delay.assert_called_once_with("token")


def test_dispatch_failure_returns_false(monkeypatch):
    task = Mock()
    task.delay.side_effect = RuntimeError("broker down")
    monkeypatch.setattr(orchestration, "import_string", lambda path: task)
    assert orchestration._dispatch_celery("token") is False
