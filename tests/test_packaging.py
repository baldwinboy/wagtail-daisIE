"""Guards against build-config regressions that strip package assets.

The 2.1.0 wheel shipped no JavaScript because ``source-exclude`` contained
bare ``*.js`` / ``*.json`` globs. These tests fail if that regresses or if the
expected static assets are missing from the source tree.
"""

import tomllib

from pathlib import Path

import wagtail_daisIE


REPO_ROOT = Path(__file__).resolve().parents[1]
JS_DIR = Path(wagtail_daisIE.__file__).parent / "static" / "wagtail_daisIE" / "js"


def test_build_backend_does_not_exclude_javascript():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    source_exclude = config["tool"]["uv"]["build-backend"]["source-exclude"]
    assert "*.js" not in source_exclude
    assert "*.json" not in source_exclude


def test_static_js_assets_present():
    names = {path.name for path in JS_DIR.glob("*.js")}
    assert "theme_persistence.js" in names
    assert len(names) >= 12
