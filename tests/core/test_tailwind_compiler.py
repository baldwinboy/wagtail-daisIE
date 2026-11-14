import pytest

from django.core.cache import cache

from wagtail_daisIE.tailwindcss import compiler
from wagtail_daisIE.tailwindcss._extractor import ParsedCandidate, parse_candidate


pytestmark = pytest.mark.django_db


def _parsed(*tokens):
    return [parse_candidate(token) for token in tokens]


def _patterns(*tokens):
    return compiler._compact_classnames(_parsed(*tokens))


def test_compacts_values():
    assert _patterns("h-4", "h-5") == ["h-{4,5}"]
    assert _patterns("bg-red-500", "bg-red-600") == ["bg-red-{500,600}"]
    assert _patterns("bg-red-500", "bg-blue-500") == [
        "bg-blue-500",
        "bg-red-500",
    ]


def test_optional_prefix_is_not_literal_braces():
    assert _patterns("p-4", "lg:p-4") == ["{,lg:}p-4"]


def test_no_cross_product_between_values_and_variants():
    assert _patterns("hover:p-4", "focus:p-8") == ["focus:p-8", "hover:p-4"]


def test_keeps_modifiers_with_matching_prefixes():
    assert _patterns("bg-red-500/20", "bg-red-500/30") == ["bg-red-500/{20,30}"]


def test_comma_arbitrary_values_are_emitted_individually():
    patterns = _patterns(
        "bg-[linear-gradient(red,blue)]",
        "bg-[linear-gradient(green,blue)]",
    )
    assert patterns == [
        "bg-[linear-gradient(green,blue)]",
        "bg-[linear-gradient(red,blue)]",
    ]
    assert not any("{" in pattern for pattern in patterns)


def test_important_markers_are_not_merged():
    assert _patterns("flex", "!flex", "flex!") == ["!flex", "flex", "flex!"]


def test_arbitrary_properties_are_not_merged():
    assert _patterns("[color:red]", "[color:blue]") == [
        "[color:blue]",
        "[color:red]",
    ]


def test_source_inline_escapes_css_strings():
    pattern = compiler._format_source_inline('content-["hello"]')
    assert pattern == '@source inline("content-[\\"hello\\"]");\n'


def test_daisyui_longest_prefix_detection():
    candidates = _parsed(
        "btn-primary",
        "mockup-browser-toolbar",
        "card-body",
        "hover-3d",
        "radial-progress",
        "text-rotate",
        "join",
        "stats",
        "tabs",
        "step",
    )
    assert compiler._daisyui_components(candidates) == {
        "button",
        "mockup",
        "card",
        "hover3d",
        "radialprogress",
        "textrotate",
        "join",
        "stat",
        "tab",
        "steps",
    }


def test_fragment_stylesheet_omits_preflight():
    stylesheet = compiler._build_stylesheet({"button"}, ["flex"], fragment=True)
    assert "@import 'tailwindcss/theme.css'" in stylesheet
    assert "@import 'tailwindcss/utilities.css'" in stylesheet
    assert "@import 'tailwindcss' source(none)" not in stylesheet
    assert "include: button;" in stylesheet
    assert "visibility.css" not in stylesheet  # contents, not filename
    assert ".daisie-visibility-target" in stylesheet


def test_extracts_class_and_data_attributes():
    html = """
    <html><body class="flex">
      <div class="grid" data-daisie-selected-class="btn-primary btn-active"></div>
    </body></html>
    """
    assert compiler._extract_class_names(html, fragment=False) == {
        "btn-active",
        "btn-primary",
        "flex",
        "grid",
    }


def test_extracts_template_children():
    html = (
        """<div class="outer"><template><span class="inside"></span></template></div>"""
    )
    assert compiler._extract_class_names(html, fragment=True) == {"inside", "outer"}


def test_inject_fills_every_placeholder():
    html = (
        '<head><style id="daisyui-jit-styles"></style>'
        '<style id="daisyui-jit-styles" nonce="x"></style></head>'
    )
    updated = compiler.inject_stylesheet(html, "/* css */")
    assert updated is not None
    assert updated.count("/* css */") == 2
    assert 'nonce="x"' in updated


def test_inject_prepends_fragment_style():
    updated = compiler.inject_stylesheet(
        '<div class="flex"></div>', "/* css */", fragment=True
    )
    assert (
        updated == '<style data-daisie-jit>/* css */</style>\n<div class="flex"></div>'
    )


def test_inject_returns_none_without_placeholder():
    assert compiler.inject_stylesheet("<div>no placeholder</div>", "/* css */") is None


def test_placeholder_html():
    assert compiler.placeholder_html() == '<style id="daisyui-jit-styles"></style>'


def test_cache_skips_compilation_on_repeat(monkeypatch):
    cache.clear()
    calls = []

    def fake_compile(stylesheet, session):
        calls.append(stylesheet)
        return "/* compiled */"

    monkeypatch.setattr(compiler, "_compile_stylesheet", fake_compile)
    session = object()

    assert compiler.compile_classnames(["flex", "p-4"], session) == "/* compiled */"
    assert compiler.compile_classnames(["p-4", "flex"], session) == "/* compiled */"
    assert len(calls) == 1
    cache.clear()


def test_full_and_fragment_cache_keys_differ(monkeypatch):
    cache.clear()
    calls = []

    def fake_compile(stylesheet, session):
        calls.append(stylesheet)
        return "/* compiled */"

    monkeypatch.setattr(compiler, "_compile_stylesheet", fake_compile)
    session = object()

    compiler.compile_classnames(["flex"], session)
    compiler.compile_classnames(["flex"], session, fragment=True)
    assert len(calls) == 2
    cache.clear()


@pytest.mark.parametrize("token", ["daisie-file-attachments", "daisyui-menu"])
def test_package_classes_are_not_sent_to_tailwind(token):
    candidate = ParsedCandidate(
        raw=token,
        variants=(),
        utility=token,
        base=token,
        value=None,
        modifier=None,
    )
    assert compiler._daisyui_components([candidate]) == set()
