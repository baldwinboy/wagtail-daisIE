import pytest

from django.contrib.auth import get_user_model

from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.bridges import (
    UnknownBridgeError,
    build_bridge_context,
    build_bridge_recipients,
    connect_signals,
    disconnect_signals,
    dispatch,
    normalize_recipients,
)
from wagtail_daisIE.notifications.models import EmailTemplate
from wagtail_daisIE.notifications.registry import (
    Bridge,
    get_bridge_placeholder_groups,
    get_bridges,
    reset_bridges,
)


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


@pytest.fixture(autouse=True)
def _reset(settings):
    reset_bridges()
    yield
    disconnect_signals()
    reset_bridges()


def _template(name="Bridge email", subject="Hi {{ payload.name }}"):
    theme, _created = DaisyUITheme.objects.get_or_create(
        name="bridge-theme", defaults={"default": True}
    )
    template = EmailTemplate.objects.create(name=name, subject=subject)
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {},
                "content": [
                    {
                        "type": "text",
                        "value": {"text": "Hello {{ payload.name }}", "design": {}},
                    }
                ],
            },
        }
    ]
    template.save()
    return template


def _bridge_with_builders(**overrides):
    bridge = Bridge(key="custom", label="Custom", template="Bridge email")
    bridge._resolved = True
    bridge._context = overrides.get("context")
    bridge._recipients = overrides.get("recipients")
    return bridge


class TestRegistry:
    def test_parses_settings_and_placeholder_groups(self, settings):
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {
                "label": "Welcome",
                "template": "Welcome email",
                "placeholders": {"name": "Recipient name"},
            }
        }
        reset_bridges()
        bridge = get_bridges()["welcome"]
        assert bridge.template == "Welcome email"
        assert bridge.placeholders == {"name": "Recipient name"}
        tokens = [
            item["token"]
            for group in get_bridge_placeholder_groups()
            for item in group["items"]
        ]
        assert "{{ payload.name }}" in tokens


class TestBuilders:
    def test_builders_recipients_and_normalize(self):
        explicit = _bridge_with_builders(
            context=lambda source: {"name": "Explicit"},
            recipients=lambda source: ["explicit@example.com"],
        )
        context = build_bridge_context(explicit, {"payload": {"name": "Inferred"}})
        assert context == {"name": "Explicit"}
        assert build_bridge_recipients(explicit, {}, context) == [
            "explicit@example.com"
        ]

        inferred = _bridge_with_builders()
        assert build_bridge_context(inferred, {"payload": {"name": "Inferred"}}) == {
            "name": "Inferred"
        }
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        assert build_bridge_recipients(
            inferred, {"payload": {"recipient_user_ids": [user.pk]}}, {}
        ) == [user]

        assert normalize_recipients("a@b.com") == ["a@b.com"]
        assert normalize_recipients(3) == [3]
        assert normalize_recipients(None) == []
        assert normalize_recipients([1, 2]) == [1, 2]


class TestDispatch:
    def test_sends_and_deduplicates(self, settings, mailoutbox):
        _template()
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Bridge email"}
        }
        reset_bridges()
        source = {"payload": {"name": "Ada", "recipient_user_ids": [user.pk]}}

        assert dispatch("welcome", source=source) == ["ada@example.com"]
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Hi Ada"
        assert "Hello Ada" in mailoutbox[0].body

        source["payload"]["recipients"] = ["ada@example.com"]
        dispatch("welcome", source=source, event_ref="welcome.1")
        dispatch("welcome", source=source, event_ref="welcome.1")
        assert len(mailoutbox) == 2

    def test_unknown_bridge_and_missing_template(self, settings):
        with pytest.raises(UnknownBridgeError):
            dispatch("missing")
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Does not exist"}
        }
        reset_bridges()
        assert dispatch("welcome", source={"payload": {}}) == []


class TestSignalWiring:
    def test_connect_and_disconnect(self, settings, mailoutbox):
        _template(name="Auto email")
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "user_created": {
                "label": "User created",
                "template": "Auto email",
                "signal": "django.db.models.signals.post_save",
                "sender": "auth.User",
                "context": "wagtail_daisIE.test.notifications.title_context",
                "recipients": "wagtail_daisIE.test.notifications.fixed_recipients",
            }
        }
        reset_bridges()

        assert connect_signals() == 1
        USER_MODEL.objects.create(username="ada", email="ada@example.com")
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["bridge@example.com"]
        disconnect_signals()
