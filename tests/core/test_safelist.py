import re

from pathlib import Path

from django.core.management import call_command

from wagtail_daisIE import choices
from wagtail_daisIE.management.commands.daisie_safelist import _class_tokens


COMMITTED_SAFELIST = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "wagtail_daisIE"
    / "tailwind"
    / "safelist.css"
)


def _generate(tmp_path):
    path = tmp_path / "safelist.css"
    call_command("daisie_safelist", output=str(path))
    return path.read_text(encoding="utf-8")


def _directives(text):
    return set(re.findall(r'@source inline\("(.*)"\);', text))


def test_every_choice_export_resolves():
    missing = [name for name in choices.__all__ if not hasattr(choices, name)]
    assert missing == []


def test_every_choice_token_is_safelisted(tmp_path):
    expected = set()
    for name in choices.__all__:
        expected.update(_class_tokens(getattr(choices, name)))

    assert expected
    assert expected <= _directives(_generate(tmp_path))


def test_spacing_families_are_safelisted(tmp_path):
    directives = _directives(_generate(tmp_path))

    for prefix in ("p-", "pt-", "pr-", "pb-", "pl-"):
        assert f"{prefix}4" in directives
    for prefix in ("m-", "mt-", "mr-", "mb-", "ml-"):
        assert f"{prefix}4" in directives
        assert f"{prefix}auto" in directives
    for prefix in ("gap-", "gap-x-", "gap-y-"):
        assert f"{prefix}4" in directives


def test_runtime_layout_classes_are_safelisted(tmp_path):
    directives = _directives(_generate(tmp_path))

    for value in ("flex", "flex-col", "flex-row", "flex-wrap", "grow", "grid"):
        assert value in directives


def test_numeric_and_template_ranges_are_declared(tmp_path):
    directives = _directives(_generate(tmp_path))

    assert "border" in directives
    for value in (
        "border-{2..999}",
        "border-spacing-{1..96}",
        "border-spacing-x-{1..96}",
        "border-spacing-y-{1..96}",
        "md:grid-cols-{1..6}",
    ):
        assert value in directives
    for value in (
        "alert-info",
        "alert-success",
        "alert-warning",
        "alert-error",
    ):
        assert value in directives


def test_committed_safelist_matches_the_generator(tmp_path):
    assert _generate(tmp_path) == COMMITTED_SAFELIST.read_text(encoding="utf-8")
