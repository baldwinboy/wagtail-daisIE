# Notifications, bridges and campaigns

`wagtail_daisIE` can send DaisyUI email templates in response to local events
(bridges), and lets admins schedule campaigns to selected audiences. Email
templates themselves are documented in [emails.md](emails.md).

Overview of the admin menu:

* **Emails → Templates** — build and preview `EmailTemplate` snippets.
* **Notifications → Audiences** — lists of recipients.
* **Notifications → Campaigns** — scheduled one-off or recurring sends.
* **Notifications → Allauth emails** — see [allauth.md](allauth.md).

## Placeholders

Every email renders with a context so placeholders become real values:

| Source | Example |
|--------|---------|
| Built-ins | `{{ site.hostname }}`, `{{ now|date:"j F Y" }}`, `{{ recipient.email }}` |
| Bridge / campaign payload | `{{ payload.meeting_title }}`, `{{ payload.url }}` |
| Context models (configured) | `{{ user.first_name }}` |

The **help panel** on the Email template editor lists everything available,
including per-bridge and per-allauth variables, and links to Django's date
filter reference.

## Bridges

A bridge maps a business event to an email template. Configure it in settings:

```python
# settings.py
WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
    "booking_requested": {
        "label": "Booking requested",
        "template": "Booking requested",  # EmailTemplate.name (or template_key)
        "signal": "myapp.signals.booking_requested",
        "sender": "myapp.models.MeetingRequest",  # optional
        "context": "myapp.notifications.booking_context",  # optional
        "recipients": "myapp.notifications.booking_recipients",  # optional
        "placeholders": {"meeting_title": "Meeting title"},  # optional docs
    },
}
```

* **`signal`/`sender`** — a Django `Signal` (and optional sender). `wagtail_daisIE`
  connects a receiver at startup. Omit both when dispatching manually.
* **`context`** — a callable that receives the event `source` and returns a
  mapping exposed as `{{ payload.* }}`. When omitted, the payload is inferred
  from `source["payload"]` or `source["context"]`.
* **`recipients`** — a callable returning recipients (users, user ids, or email
  strings). When omitted, recipients are inferred from
  `payload["recipient_user_ids"]` / `payload["recipients"]`.
* **`placeholders`** — names/descriptions shown in the admin help panel.

A minimal bridge with a rich signal payload needs only `label`, `template`,
`signal` and `sender`.

### Signal source

For Django signals the `source` is a dict like:

```python
{"sender": ..., "instance": ..., "created": ..., **kwargs}
```

### Dispatching manually (custom event buses)

Projects with their own bus call `dispatch` directly:

```python
from wagtail_daisIE.notifications.bridges import dispatch

dispatch(
    "booking_requested",
    source={"payload": log_entry.payload, "instance": log_entry},
    event_ref=log_entry.event_ref,  # optional dedupe key
)
```

`event_ref` is remembered for `WAGTAIL_DAISIE_NOTIFICATION_DEDUPE_TIMEOUT`
seconds (default 3600) so the same event is not sent twice.

### Example: publish a blog post

```python
WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
    "blog_post_published": {
        "label": "Blog post published",
        "template": "Blog post published",
        "signal": "wagtail.signals.page_published",
        "sender": "blog.BlogPage",
        "context": "blog.notifications.blog_post_context",
        "recipients": "blog.notifications.newsletter_recipients",
    },
}
```

## Audiences

An **Audience** is a reusable list of recipients. Admins manage them under
**Notifications → Audiences**. There are two kinds:

* **Manual list** — add members, each an existing user **or** a bare email
  address. Newsletter signups add to manual audiences automatically.
* **From audience rules** — select a rule declared in
  `WAGTAIL_DAISIE_AUDIENCE_RULES`.

Audience rules are shared with block/page audience gating. For campaigns (which
have no request) a rule may also declare a `queryset` returning a User queryset:

```python
WAGTAIL_DAISIE_AUDIENCE_RULES = {
    "staff": {
        "label": "Staff members",
        "rule": "myapp.audience.is_staff",  # request -> bool
        "queryset": "myapp.audience.staff_users",  # () -> QuerySet[User]
    },
    "newsletter": {
        "label": "Newsletter subscribers",
        "rule": "myapp.audience.has_newsletter",
    },
}
```

`Audience.get_recipients()` returns users and/or email strings;
`Audience.get_emails()` returns unique email addresses.

## Campaigns

An **Email campaign** sends an `EmailTemplate` to an audience. Fields:

* **Template** and **Audience**.
* **Send mode** — `manual` or `scheduled`.
* **Scheduled at** and **Repeat** (`one-off`, `daily`, `weekly`, `monthly`).
* **Variables** — extra key/value pairs exposed as `{{ payload.<name> }}`.
* **Status** — `draft`, `scheduled`, `sending`, `sent`, `failed`, `cancelled`.

### Sending

Send due campaigns from cron (or a worker):

```bash
python manage.py send_campaigns
```

Options:

```bash
python manage.py send_campaigns --dry-run          # report only
python manage.py send_campaigns --campaign 3       # one campaign
python manage.py send_campaigns --force            # re-send
python manage.py send_campaigns --limit 5
```

Delivery is idempotent: a `CampaignRecipientLog` row exists for every
recipient, so re-running does not resend to addresses already sent (unless
`--force`). Recurring campaigns advance `scheduled_at` after a successful send.

### Celery

If Celery is installed, a task is available:

```python
from wagtail_daisIE.notifications.tasks import run_scheduled_campaigns

run_scheduled_campaigns.delay()
```

Schedule it with django-celery-beat or your preferred scheduler.

> Compliance (double opt-in, unsubscribe links) is intentionally left to the
> project. `AudienceMember.is_active` is the opt-out lever; set it to `False`
> to stop sending to an address.

## Newsletter signup

Two blocks post to the built-in subscribe endpoint:

* **Newsletter signup** (content block) — choose a manual audience.
* **Menu → Newsletter** — set **Mode** to *Daisie audience* and pick an
  audience, or keep *External URL*.

Include the subscribe URLs in your project:

```python
# urls.py
(path("newsletter/", include("wagtail_daisIE.notifications.urls")),)
```

The endpoint (`wagtail_daisIE_notifications:subscribe`) is rate-limited and
accepts `email`, `audience` and optional `name`. It responds with JSON to AJAX
requests and redirects otherwise. Projects that need consent/unsubscribe flows
should point the blocks at their own endpoint instead.
