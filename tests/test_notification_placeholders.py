from datetime import datetime

from wagtail_daisIE.notifications.placeholders import (
    extract_variables,
    render_expression,
    render_placeholders,
    validate_text,
)


class TestRenderPlaceholders:
    def test_simple_substitution(self):
        result = render_placeholders(
            "Hello {{ payload.name }}", {"payload": {"name": "Ada"}}
        )
        assert result == "Hello Ada"

    def test_django_date_filter_is_applied(self):
        context = {"now": datetime(2026, 11, 12, 9, 30)}
        result = render_placeholders('{{ now|date:"j F Y" }}', context)
        assert result == "12 November 2026"

    def test_values_are_escaped(self):
        result = render_placeholders(
            "{{ payload.name }}", {"payload": {"name": "<b>Ada</b>"}}
        )
        assert result == "&lt;b&gt;Ada&lt;/b&gt;"

    def test_escape_values_can_be_disabled(self):
        result = render_placeholders(
            "{{ payload.name }}",
            {"payload": {"name": "A&B"}},
            escape_literals=False,
            escape_values=False,
        )
        assert result == "A&B"

    def test_literals_are_escaped_by_default(self):
        assert render_placeholders("a < b", {}) == "a &lt; b"

    def test_literals_can_be_preserved(self):
        assert render_placeholders("a < b", {}, escape_literals=False) == "a < b"

    def test_unknown_variable_is_empty(self):
        assert render_placeholders("x{{ payload.missing }}y", {"payload": {}}) == "xy"

    def test_no_tokens_returns_text(self):
        assert render_placeholders("just text", {}) == "just text"

    def test_none_returns_empty_string(self):
        assert render_placeholders(None, {}) == ""

    def test_template_tags_are_left_literal(self):
        source = "{% if x %}hi{% endif %}"
        assert render_placeholders(source, {}) == source

    def test_unmatched_braces_do_not_raise(self):
        assert "{{" in render_placeholders("open {{ only", {})

    def test_rich_text_mode_preserves_html(self):
        result = render_placeholders(
            "<p>Hi {{ payload.name }}</p>",
            {"payload": {"name": "Ada"}},
            escape_literals=False,
        )
        assert result == "<p>Hi Ada</p>"


class TestRenderExpression:
    def test_renders_single_expression(self):
        assert render_expression("payload.title", {"payload": {"title": "Bread"}}) == (
            "Bread"
        )

    def test_empty_expression(self):
        assert render_expression("", {}) == ""


class TestExtractVariables:
    def test_extracts_roots(self):
        text = "{{ now|date:'Y' }} {{ payload.meeting.title }} {{ site.site_name }}"
        assert extract_variables(text) == ["now", "payload", "site"]

    def test_ignores_non_tokens(self):
        assert extract_variables("no tokens") == []


class TestValidateText:
    def test_reports_template_tags(self):
        warnings = validate_text("{% if x %}")
        assert warnings and "tags" in warnings[0]

    def test_reports_comments(self):
        assert validate_text("{# comment #}")

    def test_clean_text_has_no_warnings(self):
        assert validate_text("Hello {{ payload.name }}") == []


class TestHelpGroups:
    def test_builtin_group_is_available(self):
        from wagtail_daisIE.notifications.placeholders import get_placeholder_groups

        groups = get_placeholder_groups()
        assert groups
        tokens = [item["token"] for item in groups[0]["items"]]
        assert any("site" in token for token in tokens)
        assert any("now" in token for token in tokens)
        assert any("recipient" in token for token in tokens)

    def test_help_template_renders(self):
        from django.template.loader import render_to_string

        from wagtail_daisIE.notifications.placeholders import get_placeholder_groups

        html = render_to_string(
            "wagtail_daisIE/admin/email_placeholders_help.html",
            {"placeholder_groups": get_placeholder_groups()},
        )
        assert "Placeholders" in html
        assert "Date filter reference" in html
