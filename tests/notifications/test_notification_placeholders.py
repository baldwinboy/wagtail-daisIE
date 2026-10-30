from datetime import datetime

from wagtail_daisIE.dynamic.values import normalize_text_value
from wagtail_daisIE.notifications.placeholders import (
    extract_variables,
    get_placeholder_groups,
    render_expression,
    render_placeholders,
    validate_text,
)


class _Manager:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class TestRenderPlaceholders:
    def test_substitution_and_date_filter(self):
        assert (
            render_placeholders(
                "Hello {{ payload.name }}", {"payload": {"name": "Ada"}}
            )
            == "Hello Ada"
        )
        assert (
            render_placeholders(
                '{{ now|date:"j F Y" }}', {"now": datetime(2026, 11, 12, 9, 30)}
            )
            == "12 November 2026"
        )

    def test_escaping_modes(self):
        assert (
            render_placeholders(
                "{{ payload.name }}", {"payload": {"name": "<b>Ada</b>"}}
            )
            == "&lt;b&gt;Ada&lt;/b&gt;"
        )
        assert render_placeholders("a < b", {}) == "a &lt; b"
        assert (
            render_placeholders(
                "{{ payload.name }}",
                {"payload": {"name": "A&B"}},
                escape_literals=False,
                escape_values=False,
            )
            == "A&B"
        )

    def test_empty_managers_and_sequences_render_empty(self):
        assert (
            render_placeholders(
                "{{ payload.tags }}",
                {"payload": {"tags": _Manager([])}},
            )
            == ""
        )
        assert (
            render_placeholders(
                "{{ payload.tags }}",
                {"payload": {"tags": _Manager(["one", "two"])}},
            )
            == "one, two"
        )
        assert (
            render_placeholders("{{ payload.items }}", {"payload": {"items": []}}) == ""
        )

    def test_unknown_and_literal_tags(self):
        assert render_placeholders("x{{ payload.missing }}y", {"payload": {}}) == "xy"
        source = "{% if x %}hi{% endif %}"
        assert render_placeholders(source, {}) == source

    def test_rich_text_mode_preserves_html(self):
        assert (
            render_placeholders(
                "<p>Hi {{ payload.name }}</p>",
                {"payload": {"name": "Ada"}},
                escape_literals=False,
            )
            == "<p>Hi Ada</p>"
        )


class TestExpressionAndExtraction:
    def test_render_expression_and_extract_variables(self):
        assert render_expression("payload.title", {"payload": {"title": "Bread"}}) == (
            "Bread"
        )
        for source, context, expected in [
            ("payload.missing", {"payload": {}}, ""),
            ("payload.title", {"payload": {"title": None}}, ""),
            ("payload.items", {"payload": {"items": []}}, ""),
            (
                "payload.items",
                {"payload": {"items": ["one", "two"]}},
                "one, two",
            ),
            (
                "payload.tags",
                {"payload": {"tags": _Manager([])}},
                "",
            ),
            (
                "payload.tags",
                {"payload": {"tags": _Manager(["one", "two"])}},
                "one, two",
            ),
            (
                "payload.name",
                {"payload": {"name": "<b>Bread</b>"}},
                "&lt;b&gt;Bread&lt;/b&gt;",
            ),
            # A braced expression is accepted and stripped.
            ("{{ payload.title }}", {"payload": {"title": "Bread"}}, "Bread"),
        ]:
            assert render_expression(source, context) == expected

        assert (
            render_expression(
                'payload.date|date:"j F Y"',
                {"payload": {"date": datetime(2026, 11, 12, 9, 30)}},
            )
            == "12 November 2026"
        )
        assert (
            render_expression('payload.missing|default:"friend"', {"payload": {}})
            == "friend"
        )

        text = "{{ now|date:'Y' }} {{ payload.meeting.title }} {{ site.site_name }}"
        assert extract_variables(text) == ["now", "payload", "site"]


class TestValueNormalisation:
    def test_empty_and_non_empty_values(self):
        assert normalize_text_value(None) == ""
        assert normalize_text_value([]) == ""
        assert normalize_text_value(()) == ""
        assert normalize_text_value(set()) == ""
        assert normalize_text_value(_Manager([])) == ""
        assert normalize_text_value(_Manager(["one", "two"])) == "one, two"
        assert normalize_text_value(["one", "two"]) == "one, two"
        assert normalize_text_value("Ada") == "Ada"
        assert normalize_text_value(7) == "7"


class TestValidationAndHelp:
    def test_validate_and_help_groups(self):
        warnings = validate_text("{% if x %}")
        assert warnings and "tags" in warnings[0]
        warnings = validate_text("{# comment #}")
        assert warnings and "comments" in warnings[0]
        assert validate_text("Hello {{ payload.name }}") == []

        groups = get_placeholder_groups()
        assert groups
        tokens = [item["token"] for item in groups[0]["items"]]
        assert any("site" in token for token in tokens)
        assert any("now" in token for token in tokens)
        assert any("recipient" in token for token in tokens)
