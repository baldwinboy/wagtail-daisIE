from pathlib import Path

import pytest

from wagtail_daisIE.notifications.allauth_catalogue import (
    discover_emails,
    get_allauth_email_choices,
    reset_allauth_emails,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_allauth_emails()
    yield
    reset_allauth_emails()


def _make_fake_allauth(tmp_path):
    base = tmp_path / "templates"
    email_dir = base / "account" / "email"
    email_dir.mkdir(parents=True)
    (email_dir / "base_message.txt").write_text(
        "{% block content %}{% endblock %} from {{ current_site }}",
        encoding="utf-8",
    )
    (email_dir / "email_confirmation_signup_subject.txt").write_text(
        "Confirm your account", encoding="utf-8"
    )
    (email_dir / "email_confirmation_signup_message.txt").write_text(
        '{% extends "account/email/base_message.txt" %}'
        "{% block content %}{{ activate_url }} {{ user }}"
        "{% if code %}{{ code }}{% endif %}{% endblock %}",
        encoding="utf-8",
    )
    return base


class TestDiscovery:
    def test_discovers_prefixes_and_variables(self, tmp_path):
        base = _make_fake_allauth(tmp_path)
        emails = discover_emails(search_paths=[base])
        prefixes = [email.prefix for email in emails]
        assert "account/email/email_confirmation_signup" in prefixes
        # The base template itself is not an event.
        assert "account/email/base" not in prefixes

        entry = next(
            email
            for email in emails
            if email.prefix == "account/email/email_confirmation_signup"
        )
        assert entry.category == "account"
        for variable in ("activate_url", "user", "code", "current_site"):
            assert variable in entry.variables

    def test_curated_label_is_used(self, tmp_path):
        base = _make_fake_allauth(tmp_path)
        entry = discover_emails(search_paths=[base])[0]
        assert str(entry.label) == "Signup email confirmation"

    def test_missing_directories_is_empty(self, tmp_path):
        assert discover_emails(search_paths=[tmp_path / "nope"]) == []


class TestRealAllauth:
    def test_discovers_installed_allauth_templates(self):
        allauth = pytest.importorskip("allauth")
        base = Path(allauth.__file__).parent / "templates"
        emails = discover_emails(search_paths=[base])
        prefixes = {email.prefix for email in emails}
        assert "account/email/password_reset_key" in prefixes
        assert any(prefix.startswith("mfa/email/") for prefix in prefixes)

        reset = next(
            email
            for email in emails
            if email.prefix == "account/email/password_reset_key"
        )
        assert "password_reset_url" in reset.variables

    def test_choices_from_real_catalogue(self):
        pytest.importorskip("allauth")
        choices = get_allauth_email_choices()
        assert choices
        assert all(isinstance(prefix, str) for prefix, _label in choices)
