import pytest

from wagtail_daisIE.tailwindcss.validators import CssValidationError, validate_css


@pytest.mark.parametrize(
    "css",
    [
        ".a { color: red; }",
        "@layer theme, base, components, utilities;\n@import 'tailwindcss/theme.css' layer(theme);",
        "@property --x { syntax: '*'; inherits: false; }",
        ".a { background: url('https://example.com/a;b'); }",
        "/* comment { */ .a { content: '}'; }",
    ],
)
def test_valid_css(css):
    assert validate_css(css) == css


@pytest.mark.parametrize(
    "css",
    [
        "",
        "   ",
        ".a { color: red;",
        ".a { color: red; }}",
        ".a { content: '<script>'; }",
        ".a { content: '</style>'; }",
        ".a { color: red; }\x00",
    ],
)
def test_invalid_css(css):
    with pytest.raises(CssValidationError):
        validate_css(css)


def test_size_limit():
    with pytest.raises(CssValidationError):
        validate_css(".a{}", max_bytes=1)
