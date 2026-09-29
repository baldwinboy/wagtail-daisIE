import pytest

from wagtail_daisIE.notifications.blocks import (
    MenuNewsletterBlock,
    NewsletterSignupBlock,
)
from wagtail_daisIE.notifications.models import Audience


pytestmark = pytest.mark.django_db


class TestNewsletterBlocks:
    def test_daisie_and_external_modes(self):
        """Both blocks wrap the same subscribe URL, under different keys."""
        audience = Audience.objects.create(name="Newsletter")
        for block_class, value, action_key in [
            (NewsletterSignupBlock, {"target_audience": "audience"}, "subscribe_url"),
            (
                MenuNewsletterBlock,
                {"mode": "daisie", "target_audience": "audience"},
                "newsletter_action",
            ),
        ]:
            context = block_class().get_context(
                {**value, "target_audience": audience, "design": {}, "audience": {}}
            )
            assert context["audience_id"] == audience.pk
            assert context[action_key] == "/notifications/subscribe/"

        context = MenuNewsletterBlock().get_context(
            {
                "mode": "external",
                "action": "https://example.com/subscribe",
                "target_audience": audience,
                "design": {},
                "audience": {},
            }
        )
        assert context["newsletter_action"] == "https://example.com/subscribe"
        # In external mode the chooser is irrelevant and must be cleared.
        assert context["audience_id"] is None
