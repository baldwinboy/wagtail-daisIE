"""Notification bridge callables for the demo.

Referenced from ``WAGTAIL_DAISIE_NOTIFICATION_BRIDGES``. The context values are
exposed to the email template as ``{{ payload.* }}``.
"""


def blog_post_context(source):
    page = source.get("instance")
    if page is None:
        return {}
    return {
        "title": getattr(page, "title", ""),
        "subtitle": getattr(page, "subtitle", ""),
        "url": getattr(page, "url", ""),
    }


def newsletter_recipients(source):
    from wagtail_daisIE.notifications.models import Audience

    audience = Audience.objects.filter(name="Newsletter").first()
    if audience is None:
        return []
    return audience.get_emails()
