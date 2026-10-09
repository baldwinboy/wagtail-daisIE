"""Guards against build-config regressions that strip package assets.

The 2.1.0 wheel shipped no JavaScript because ``source-exclude`` contained
bare ``*.js`` / ``*.json`` globs. These tests fail if that regresses or if the
expected static/template assets are missing from the source tree.
"""

import tomllib

from pathlib import Path

import wagtail_daisIE


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = Path(wagtail_daisIE.__file__).parent
JS_DIR = PACKAGE_DIR / "static" / "wagtail_daisIE" / "js"
CSS_DIR = PACKAGE_DIR / "static" / "wagtail_daisIE" / "css"
TEMPLATES_DIR = PACKAGE_DIR / "templates"


def test_build_backend_does_not_exclude_javascript():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    source_exclude = config["tool"]["uv"]["build-backend"]["source-exclude"]
    assert "*.js" not in source_exclude
    assert "*.json" not in source_exclude


def test_static_js_assets_present():
    names = {path.name for path in JS_DIR.glob("*.js")}
    assert "theme_persistence.js" in names
    assert len(names) >= 11


def test_static_css_assets_present():
    assert (CSS_DIR / "daisie.css").is_file()
    assert (CSS_DIR / "block_settings.css").is_file()


def test_templates_are_present():
    assert (TEMPLATES_DIR / "wagtail_daisIE" / "tags" / "theme.html").is_file()
