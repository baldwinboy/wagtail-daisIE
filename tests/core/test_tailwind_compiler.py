import pytest

from wagtail_daisIE.tailwindcss import compiler
from wagtail_daisIE.tailwindcss._extractor import parse_candidate


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


def test_no_classes_produce_no_stylesheet():
    assert compiler.build_input_stylesheet([]) == ""
    assert compiler.build_input_stylesheet(["daisie-file-attachments"]) == ""


def test_extracts_class_and_data_attributes():
    html = """
    <html><body class="flex">
      <div class="grid" data-daisie-selected-class="btn-primary btn-active"></div>
    </body></html>
    """
    assert compiler.extract_class_names(html, fragment=False) == {
        "btn-active",
        "btn-primary",
        "flex",
        "grid",
    }


def test_extracts_template_children():
    html = (
        """<div class="outer"><template><span class="inside"></span></template></div>"""
    )
    assert compiler.extract_class_names(html, fragment=True) == {"inside", "outer"}
