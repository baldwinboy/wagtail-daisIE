import pytest

from django.contrib.auth import get_user_model

from wagtail_daisIE.emails.models import EmailTemplate
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.bridges import (
    UnknownBridgeError,
    build_bridge_context,
    build_bridge_recipients,
    connect_signals,
    disconnect_signals,
    dispatch,
    make_receiver,
    normalize_recipients,
)
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
                        "value": {
                            "text": "Hello {{ payload.name }}",
                            "design": {},
                        },
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
    def test_parses_settings(self, settings):
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

    def test_placeholder_groups(self, settings):
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {
                "label": "Welcome",
                "template": "Welcome email",
                "placeholders": {"name": "Recipient name"},
            }
        }
        reset_bridges()
        groups = get_bridge_placeholder_groups()
        assert groups
        tokens = [item["token"] for item in groups[0]["items"]]
        assert "{{ payload.name }}" in tokens


class TestBuilders:
    def test_explicit_context_and_recipients(self):
        bridge = _bridge_with_builders(
            context=lambda source: {"name": "Ada"},
            recipients=lambda source: ["ada@example.com"],
        )
        context = build_bridge_context(bridge, {})
        recipients = build_bridge_recipients(bridge, {}, context)
        assert context == {"name": "Ada"}
        assert recipients == ["ada@example.com"]

    def test_context_inferred_from_payload(self):
        bridge = _bridge_with_builders()
        context = build_bridge_context(bridge, {"payload": {"name": "Ada"}})
        assert context == {"name": "Ada"}

    def test_recipients_inferred_from_payload(self):
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        bridge = _bridge_with_builders()
        recipients = build_bridge_recipients(
            bridge, {"payload": {"recipient_user_ids": [user.pk]}}, {}
        )
        assert recipients == [user]

    def test_normalize_recipients(self):
        assert normalize_recipients("a@b.com") == ["a@b.com"]
        assert normalize_recipients(3) == [3]
        assert normalize_recipients(None) == []
        assert normalize_recipients([1, 2]) == [1, 2]


class TestDispatch:
    def test_sends_for_inferred_payload(self, settings, mailoutbox):
        _template()
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Bridge email"}
        }
        reset_bridges()

        sent = dispatch(
            "welcome",
            source={"payload": {"name": "Ada", "recipient_user_ids": [user.pk]}},
        )

        assert sent == ["ada@example.com"]
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Hi Ada"
        assert "Hello Ada" in mailoutbox[0].body

    def test_event_ref_deduplicates(self, settings, mailoutbox):
        _template()
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Bridge email"}
        }
        reset_bridges()
        source = {"payload": {"name": "Ada", "recipient_user_ids": []}}
        source["payload"]["recipients"] = ["ada@example.com"]

        dispatch("welcome", source=source, event_ref="welcome.1")
        dispatch("welcome", source=source, event_ref="welcome.1")

        assert len(mailoutbox) == 1

    def test_unknown_bridge_raises(self):
        with pytest.raises(UnknownBridgeError):
            dispatch("missing")

    def test_missing_template_is_noop(self, settings):
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Does not exist"}
        }
        reset_bridges()
        assert dispatch("welcome", source={"payload": {}}) == []


class TestSignalWiring:
    def test_receiver_dispatches(self, settings, mailoutbox):
        _template()
        settings.WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
            "welcome": {"label": "Welcome", "template": "Bridge email"}
        }
        reset_bridges()
        bridge = get_bridges()["welcome"]
        bridge._resolved = True
        bridge._context = lambda source: {"name": "Ada"}
        bridge._recipients = lambda source: ["ada@example.com"]

        receiver = make_receiver(bridge)
        receiver(sender=None)

        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["ada@example.com"]

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
