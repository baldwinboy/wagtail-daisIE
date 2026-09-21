import pytest

from wagtail_daisIE.blocks.menu_items import MenuNewsletterBlock
from wagtail_daisIE.notifications.blocks import NewsletterSignupBlock
from wagtail_daisIE.notifications.models import Audience


pytestmark = pytest.mark.django_db


class TestNewsletterSignupBlock:
    def test_get_context_exposes_subscribe_target(self):
        audience = Audience.objects.create(name="Newsletter")
        context = NewsletterSignupBlock().get_context(
            {
                "target_audience": audience,
                "design": {},
                "audience": {},
            }
        )
        assert context["audience_id"] == audience.pk
        assert context["subscribe_url"] == "/notifications/subscribe/"


class TestMenuNewsletterBlock:
    def test_external_mode_uses_action(self):
        context = MenuNewsletterBlock().get_context(
            {
                "mode": "external",
                "action": "https://example.com/subscribe",
                "design": {},
                "audience": {},
            }
        )
        assert context["newsletter_action"] == "https://example.com/subscribe"
        assert context["audience_id"] is None

    def test_daisie_mode_uses_subscribe_url(self):
        audience = Audience.objects.create(name="Menu list")
        context = MenuNewsletterBlock().get_context(
            {
                "mode": "daisie",
                "target_audience": audience,
                "design": {},
                "audience": {},
            }
        )
        assert context["newsletter_action"] == "/notifications/subscribe/"
        assert context["audience_id"] == audience.pk
