import pytest

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

from wagtail_daisIE.emails.models import EmailTemplate
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.allauth import (
    DaisyUIAccountAdapterMixin,
    build_allauth_payload,
    get_active_override,
    render_allauth_message,
)
from wagtail_daisIE.notifications.models import AllauthEmailOverride


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


def _template(subject="Reset {{ payload.code }}"):
    theme, _created = DaisyUITheme.objects.get_or_create(
        name="allauth-theme", defaults={"default": True}
    )
    template = EmailTemplate.objects.create(name="Reset email", subject=subject)
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {},
                "content": [
                    {
                        "type": "text",
                        "value": {"text": "Code {{ payload.code }}", "design": {}},
                    }
                ],
            },
        }
    ]
    template.save()
    return template


class _BaseAdapter:
    def render_mail(self, template_prefix, email, context, headers=None):
        return "base-rendered"

    def get_from_email(self):
        return "from@example.com"

    def format_email_subject(self, subject):
        return f"[Site] {subject}"


class _Adapter(DaisyUIAccountAdapterMixin, _BaseAdapter):
    pass


class TestPayload:
    def test_excludes_request_and_keeps_values(self):
        user = USER_MODEL.objects.create(username="ada")
        payload = build_allauth_payload(
            {"request": object(), "user": user, "code": "123"}
        )
        assert "request" not in payload
        assert payload["code"] == "123"
        assert payload["user"] == user


class TestMixin:
    def test_unmapped_prefix_falls_back(self):
        message = _Adapter().render_mail(
            "account/email/password_reset_key", "to@example.com", {}
        )
        assert message == "base-rendered"

    def test_mapped_prefix_renders_daisie_template(self):
        template = _template()
        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": template, "is_active": True},
        )
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")

        message = _Adapter().render_mail(
            "account/email/password_reset_key",
            "to@example.com",
            {"user": user, "code": "123"},
        )

        assert isinstance(message, EmailMultiAlternatives)
        assert message.subject == "[Site] Reset 123"
        assert message.to == ["to@example.com"]
        assert message.from_email == "from@example.com"
        assert "Code 123" in message.body
        assert message.alternatives

    def test_inactive_override_falls_back(self):
        template = _template()
        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": template, "is_active": False},
        )
        message = _Adapter().render_mail(
            "account/email/password_reset_key", "to@example.com", {"code": "1"}
        )
        assert message == "base-rendered"

    def test_override_without_template_falls_back(self):
        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": None, "is_active": True},
        )
        message = _Adapter().render_mail(
            "account/email/password_reset_key", "to@example.com", {"code": "1"}
        )
        assert message == "base-rendered"


class TestHelpers:
    def test_get_active_override_requires_template(self):
        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": None, "is_active": True},
        )
        assert get_active_override("account/email/password_reset_key") is None

    def test_render_returns_none_when_unmapped(self):
        assert (
            render_allauth_message(
                _Adapter(),
                "account/email/unknown_account",
                "to@example.com",
                {},
            )
            is None
        )

    def test_ensure_defaults_creates_rows(self):
        pytest.importorskip("allauth")
        AllauthEmailOverride.objects.all().delete()
        created = AllauthEmailOverride.ensure_defaults()
        assert created >= 1
        # Calling it again is idempotent.
        assert AllauthEmailOverride.ensure_defaults() == 0
