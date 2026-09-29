import pytest

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

from wagtail_daisIE.allauth_emails.allauth import (
    DaisyUIAccountAdapterMixin,
    build_allauth_payload,
)
from wagtail_daisIE.allauth_emails.models import AllauthEmailOverride
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.models import EmailTemplate


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
        assert payload["code"] == "123" and payload["user"] == user


class TestMixin:
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
        assert "Code 123" in message.body and message.alternatives

    def test_fallbacks_and_defaults(self):
        assert (
            _Adapter().render_mail(
                "account/email/password_reset_key", "to@example.com", {}
            )
            == "base-rendered"
        )

        template = _template()
        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": template, "is_active": False},
        )
        assert (
            _Adapter().render_mail(
                "account/email/password_reset_key", "to@example.com", {"code": "1"}
            )
            == "base-rendered"
        )

        AllauthEmailOverride.objects.update_or_create(
            template_prefix="account/email/password_reset_key",
            defaults={"email_template": None, "is_active": True},
        )
        assert (
            _Adapter().render_mail(
                "account/email/password_reset_key", "to@example.com", {"code": "1"}
            )
            == "base-rendered"
        )

        pytest.importorskip("allauth")
        AllauthEmailOverride.objects.all().delete()
        assert AllauthEmailOverride.ensure_defaults() >= 1
        assert AllauthEmailOverride.ensure_defaults() == 0
