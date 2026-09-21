# django-allauth integration

`wagtail_daisIE` can style your allauth account **pages** and **forms**, and
replace allauth's built-in **emails** with DaisyUI `EmailTemplate` snippets so
admins can edit them in Wagtail.

allauth is an optional dependency. Install the extra:

```bash
uv add "wagtail-daisIE[allauth]"
# or
pip install "wagtail-daisIE[allauth]"
```

Nothing in this page is required unless you use allauth; the templates and the
adapter mixin are opt-in.

## 1. Project setup

Add allauth to `INSTALLED_APPS`, its middleware, an authentication backend, and
its URLs.

```python
# settings.py
INSTALLED_APPS = [
    "wagtail_daisIE",  # keep before allauth so DaisyUI templates win
    # ... your apps, wagtail ...
    "django.contrib.sites",
    "allauth",
    "allauth.account",
]

SITE_ID = 1

MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
```

```python
# urls.py
urlpatterns = [
    path("accounts/", include("allauth.urls")),
    # ...
]
```

## 2. The account adapter bridge

Subclass `DefaultAccountAdapter` and mix in `DaisyUIAccountAdapterMixin`
**first**:

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from wagtail_daisIE.notifications.allauth import DaisyUIAccountAdapterMixin


class AccountAdapter(DaisyUIAccountAdapterMixin, DefaultAccountAdapter):
    # Every other override still works as usual.
    def is_open_for_signup(self, request):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
```

```python
# settings.py
ACCOUNT_ADAPTER = "myapp.adapters.AccountAdapter"
```

How it behaves:

* If the allauth `template_prefix` has an **active** `AllauthEmailOverride`
  with an email template, the email is rendered from that DaisyUI template and
  sent (text + HTML).
* Otherwise `render_mail` is delegated to `DefaultAccountAdapter`, so allauth's
  own templates are used.
* Only `render_mail` is overridden. Signup rules, redirects, verification, and
  any other adapter method you define are untouched.

Optionally set the envelope sender for bridged emails:

```python
WAGTAIL_DAISIE_NOTIFICATION_FROM_EMAIL = "hello@example.com"
```

## 3. Editing allauth emails in Wagtail

Allauth emails are normal `EmailTemplate` snippets, bound to an allauth event.

### The event catalogue

The list of allauth emails is **discovered at runtime** from the installed
allauth package, and each event's available variables are parsed from allauth's
own subject/message templates. This means the list is always complete for the
allauth version you have installed.

Open **Notifications → Allauth emails**. A row exists for every discovered
event (seeded after `migrate`). Each row has:

* **Allauth email** — the event prefix, e.g.
  `account/email/password_reset_key`.
* **Email template** — the DaisyUI `EmailTemplate` to use.
* **Active** — only active rows override allauth.

To override an event:

1. Create an `EmailTemplate` under **Emails → Templates** (see
   [emails.md](emails.md) for the builder and placeholders).
2. Open the matching **Allauth emails** row, choose the template, and tick
   **Active**.

### Variables

Allaath's context is exposed to the template under `{{ payload.* }}`, alongside
the built-ins `{{ site.* }}`, `{{ now }}` and `{{ recipient.* }}`. The help
panel on the **Email template** edit screen lists the variables available for
each allauth event.

Useful values by event:

| Event | Available under `payload` |
|-------|---------------------------|
| `account/email/email_confirmation_signup` | `user`, `code`, `activate_url`, `key`, `current_site`, `email` |
| `account/email/email_confirmation` | `user`, `code`, `activate_url`, `key`, `current_site`, `email` |
| `account/email/password_reset_key` | `user`, `password_reset_url`, `username`, `code`, `current_site` |
| `account/email/unknown_account` | `email`, `signup_url`, `current_site` |
| `account/email/account_already_exists` | `signup_url`, `password_reset_url` |
| `mfa/email/*` | `user`, `timestamp`, `ip`, `user_agent`, … |

Example subject: `Confirm your account` → `Hello {{ payload.user.first_name }}`.

Example body:

```html
<p>Hi {{ payload.user.first_name|default:"there" }},</p>
<p>Confirm your account using the code
   <strong>{{ payload.code }}</strong>.</p>
<p><a href="{{ payload.activate_url }}">Confirm now</a></p>
```

> Only `{{ ... }}` variable expressions are supported. Django template tags
> (`{% ... %}`) are shown literally and are reported by the help panel.
> See [emails.md](emails.md#placeholders) for details and date formatting.

### Using allauth's stock templates alongside

Rows that are inactive (or have no template) fall through to allauth's stock
email templates, so you can override only the emails you care about.

## 4. DaisyUI pages and forms

Set one flag to swap allauth's page chrome and form fields for DaisyUI markup:

```python
WAGTAIL_DAISIE_ALLAUTH_UI = True
```

When enabled, `wagtail_daisIE` registers its override templates ahead of
allauth's, restyling:

* **Layouts** — `allauth/layouts/base.html` provides a theme-aware page
  (`data-theme`, theme CSS), a navbar account menu, alert-styled messages, and a
  centered `card`. All allauth views (login, signup, password reset, email
  management, MFA, sessions) inherit it. allauth's block names are preserved so
  your own child templates keep working.
* **Forms** — `allauth/elements/fields.html`, `field.html`, `button.html` and
  `alert.html` are overridden so fields render as DaisyUI `input` / `textarea` /
  `select` / `checkbox` / `radio` with labels, help text and accessible errors
  (`aria-invalid`, `aria-describedby`, `role="alert"`).

Because this is done through the template engine's `DIRS`, it only applies when
the flag is on, and any project template with the same name takes precedence —
so you can override individual pages.

### Custom signup fields

Custom fields on your signup form (for example `name`, `date_of_birth`,
`accept_toc`) are rendered automatically: the field renderer iterates the actual
form fields and maps each widget to the right DaisyUI class. No per-field
configuration is required.

### Theming

The layouts use the project's **default `DaisyUITheme`**, so the account pages
match the rest of your site automatically. If you have no default theme, the
pages render with DaisyUI defaults.

## 5. Adding a custom adapter behaviour

The mixin only intercepts email rendering. Everything else is a normal allauth
adapter:

```python
class AccountAdapter(DaisyUIAccountAdapterMixin, DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.ACCOUNT_ALLOW_REGISTRATION

    def get_login_redirect_url(self, request):
        return "/members/"
```

## 6. Troubleshooting

* **Emails still look like allauth's defaults** — the override row is inactive,
  has no template, or the prefix does not match. Check **Notifications →
  Allauth emails**; the prefix must match exactly.
* **The account pages are not styled** — `WAGTAIL_DAISIE_ALLAUTH_UI` is not
  `True`, or the app registry did not include `wagtail_daisIE`. Ensure the app
  is installed before allauth.
* **`{{ payload.user }}` is empty** — not every event carries a user; check the
  help panel for the variables of that specific event.
* **`{% %}` tags appear in the email** — only `{{ ... }}` expressions are
  supported; convert them to variable lookups.
