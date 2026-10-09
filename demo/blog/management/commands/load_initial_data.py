"""Load bakerydemo-equivalent content from ``demo/fixtures``.

Content (pages, posts, people, images) is read from
``demo/fixtures/content.json``; media is read from
``demo/fixtures/media/original_images``. DaisyUI themes, menus, error pages and
other configured snippets are seeded programmatically because themes and menus
use revisions and orderable models that are a poor fit for flat fixtures.
"""

from __future__ import annotations

import json
import re

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import wagtail

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from home.models import DemoPage, HomePage
from wagtail.images.models import Image
from wagtail.models import Collection, Site
from wagtail.rich_text import RichText
from wagtail.users.models import UserProfile

from blog.models import (
    BlogIndexPage,
    BlogPage,
    Bread,
    BreadDetailTemplate,
    BreadIndexPage,
    BreadSuggestionFormPage,
    Person,
)
from wagtail_daisIE.allauth_emails.models import AllauthEmailOverride
from wagtail_daisIE.errors.models import ErrorPage
from wagtail_daisIE.feeds.models import Feed
from wagtail_daisIE.menus.models import DaisyUIMenu
from wagtail_daisIE.models import (
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeColors,
    DaisyUIThemeEffects,
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
    DaisyUIThemeRadii,
    DaisyUIThemeSizes,
)
from wagtail_daisIE.notifications.models import (
    Audience,
    AudienceMember,
    EmailTemplate,
)


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures"
CONTENT_FILE = FIXTURES_DIR / "content.json"
IMAGES_DIR = FIXTURES_DIR / "media" / "original_images"

# Dark mode palette shipped with the demo. Values are 6-digit hex and are
# normalised to the alpha-aware ``#rrggbbff`` format used by the theme fields.
DARK_MODE_DEFAULT_COLORS: dict[str, str] = {
    "base_100": "#0F0A1A",
    "base_200": "#1A0A1F",
    "base_300": "#4a1942",
    "base_content": "#FDF2F8",
    "primary": "#0F0A1A",
    "primary_content": "#FDF2F8",
    "secondary": "#1A0A1F",
    "secondary_content": "#FBCFE8",
    "accent": "#7c3aed",
    "accent_content": "#e84a7a",
    "neutral": "#4a1942",
    "neutral_content": "#e84a7a",
    "info": "#fbcfe8",
    "info_content": "#e84a7a",
    "success": "#d1fae5",
    "success_content": "#10b981",
    "warning": "#fef3c7",
    "warning_content": "#f59e0b",
    "error": "#fee2e2",
    "error_content": "#ef4444",
}

GOOGLE_FONT_CDN = "https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@400;600;700&display=swap"

# Palette approximating the Wagtail Bakery demo (:root variables).
BAKERY_COLORS: dict[str, str] = {
    "primary": "#c55302",
    "primary_content": "#ffffff",
    "secondary": "#87744f",
    "secondary_content": "#ffffff",
    "accent": "#825600",
    "accent_content": "#f5f3e9",
    "neutral": "#333333",
    "neutral_content": "#f5f3e9",
    "base_100": "#ffffff",
    "base_200": "#f5f3e9",
    "base_300": "#e1dcd3",
    "base_content": "#333333",
    "info": "#00bafe",
    "info_content": "#042e49",
    "success": "#00d390",
    "success_content": "#004c39",
    "warning": "#fcb700",
    "warning_content": "#793205",
    "error": "#ff637d",
    "error_content": "#4d0218",
}


def _hexa(value: str) -> str:
    """Normalise a hex colour to the 8-digit ``#rrggbbff`` form."""
    value = value.strip()
    if len(value) == 7:
        return f"{value}ff"
    return value


def _load_content() -> dict[str, Any]:
    if not CONTENT_FILE.is_file():
        raise CommandError(f"Missing fixture file: {CONTENT_FILE}")
    return json.loads(CONTENT_FILE.read_text(encoding="utf-8"))


def _dimensions_from_path(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        w, h = get_image_dimensions(fh)
    if w and h:
        return w, h
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'viewBox="0\s+0\s+([\d.]+)\s+([\d.]+)"', text)
        if m:
            return int(float(m.group(1))), int(float(m.group(2)))
    raise CommandError(f"Could not read dimensions for {path}")


def _wagtail_image_from_spec(
    spec: dict[str, Any],
    *,
    collection_names: dict[int, str],
    cache: dict[str, Image],
    users_by_username: dict[str, AbstractUser],
    default_user: AbstractUser,
) -> Image:
    """Create a Wagtail image from an inlined fixture spec."""
    cache_key = spec["file"]
    if cache_key in cache:
        return cache[cache_key]

    path = IMAGES_DIR / Path(spec["file"]).name
    if not path.is_file():
        raise CommandError(f"Missing image file: {path}")

    width, height = _dimensions_from_path(path)
    file_size = path.stat().st_size
    with path.open("rb") as fh:
        data = fh.read()
    django_file = ContentFile(data, name=path.name)

    collection_name = collection_names.get(spec.get("collection"), "Root")
    root = Collection.get_first_root_node()
    collection = root.get_children().filter(name=collection_name).first()
    if collection is None:
        collection = root.add_child(name=collection_name)

    uploader = default_user
    for username in spec.get("uploaded_by_user") or []:
        if username in users_by_username:
            uploader = users_by_username[username]
            break

    img = Image(
        title=spec["title"],
        description=spec.get("description", ""),
        collection=collection,
        width=width,
        height=height,
        file_size=file_size,
        uploaded_by_user=uploader,
    )
    for key in (
        "focal_point_x",
        "focal_point_y",
        "focal_point_width",
        "focal_point_height",
    ):
        if spec.get(key) is not None:
            setattr(img, key, spec[key])

    img.file.save(path.name, django_file, save=False)
    img.save()

    Image.objects.filter(pk=img.pk).update(
        created_at=parse_datetime(spec["created_at"])
    )

    cache[cache_key] = img
    return img


def _blocks_to_stream(
    blocks: list[dict[str, Any]],
    *,
    load_image: Callable[[str], Image],
) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for block in blocks:
        btype = block["type"]
        value = block["value"]
        if btype in ("paragraph_block", "rich_text"):
            out.append(("rich_text", {"text": RichText(value)}))
        elif btype == "heading_block":
            out.append(("header", {"text": value.get("heading_text", "")}))
        elif btype == "image_block":
            out.append(
                (
                    "image",
                    {
                        "image": load_image(value["image"]),
                        "caption": value.get("caption", ""),
                        "attribution": value.get("attribution", ""),
                    },
                )
            )
        elif btype == "block_quote":
            out.append(
                (
                    "blockquote",
                    {
                        "text": value.get("text", ""),
                        "attribute_name": value.get("attribute_name", ""),
                    },
                )
            )
        elif btype == "embed_block":
            url = value if isinstance(value, str) else value.get("url", "")
            out.append(("embed", {"url": url}))
        else:
            raise CommandError(f"Unsupported block type {btype!r} in demo loader")
    return out


def _ensure_theme(
    name: str,
    *,
    default: bool = False,
    prefers_dark: bool = False,
    colors: dict[str, str] | None = None,
    with_fonts: bool = True,
    force: bool = False,
) -> DaisyUITheme:
    """Create (or refresh) a DaisyUI theme with all of its related options."""
    if force:
        DaisyUITheme.objects.filter(name=name).delete()

    theme, created = DaisyUITheme.objects.get_or_create(
        name=name,
        defaults={
            "default": default,
            "prefers_dark": prefers_dark,
            "color_scheme": "dark" if prefers_dark else "light",
        },
    )
    if created or force or not theme.colors.exists():
        DaisyUIThemeColors.objects.create(
            theme=theme, **{k: _hexa(v) for k, v in (colors or {}).items()}
        )
    if created or force or not theme.radii.exists():
        DaisyUIThemeRadii.objects.create(theme=theme)
    if created or force or not theme.sizes.exists():
        DaisyUIThemeSizes.objects.create(theme=theme)
    if created or force or not theme.effects.exists():
        DaisyUIThemeEffects.objects.create(theme=theme)
    if created or force or not theme.background.exists():
        DaisyUIThemeBackground.objects.create(theme=theme)

    if created or force or not theme.main_design:
        theme.main_design = _as_stream_data(
            [
                {
                    "type": "main",
                    "value": {
                        "layout": "column",
                        "size": {
                            "width": {"width": "w-full", "max_width": "max-w-6xl"}
                        },
                        "margin": {"left": "ml-auto", "right": "mr-auto"},
                        "padding": {
                            "top": "pt-8",
                            "right": "pr-4",
                            "bottom": "pb-8",
                            "left": "pl-4",
                        },
                    },
                }
            ]
        )
        theme.save()

    if with_fonts and (created or force or not theme.fonts.exists()):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        DaisyUIThemeFontFamily.objects.create(
            fonts=fonts,
            role="heading",
            font_family="Marcellus",
            generic_font_family="serif",
        )
        DaisyUIThemeFontFamily.objects.create(
            fonts=fonts,
            role="body",
            font_family="Inter",
            generic_font_family="sans-serif",
        )
        DaisyUIThemeFontCDN.objects.create(
            theme=theme, url=GOOGLE_FONT_CDN, label="Google Fonts"
        )
    return theme


def _as_stream_data(value):
    """Recursively convert ``{"type", "value"}`` dicts to ``(type, value)`` tuples.

    Wagtail's ``StreamBlock.to_python`` normalises the tuple form at every
    nesting level, but the dict form is left as raw data for nested streams,
    so chooser instances (pages, snippets) survive un-prepared and fail JSON
    serialisation on save. Tuples must be recursed into as well, since some
    callers (e.g. the navbar ``branding`` argument) hand us tuple form with
    raw dicts nested inside.
    """
    if isinstance(value, dict):
        if "type" in value and "value" in value:
            return (value["type"], _as_stream_data(value["value"]))
        return {key: _as_stream_data(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_as_stream_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_as_stream_data(item) for item in value)
    return value


def _ensure_menu(
    name: str,
    *,
    layout: str,
    body: list[dict[str, Any]],
    force: bool = False,
    **defaults: Any,
) -> DaisyUIMenu:
    """Create (or refresh) a demo menu snippet."""
    menu, created = DaisyUIMenu.objects.get_or_create(
        name=name, defaults={"layout": layout}
    )
    if created or force:
        menu.layout = layout
        for field, field_value in defaults.items():
            setattr(menu, field, _as_stream_data(field_value))
        menu.body = _as_stream_data(body)
        menu.save()
    return menu


def _ensure_newsletter_audience():
    audience, _ = Audience.objects.get_or_create(
        name="Newsletter",
        defaults={"description": "People who signed up for the demo newsletter."},
    )
    for email, name in (
        ("roberta@example.com", "Roberta"),
        ("olivia@example.com", "Olivia"),
    ):
        AudienceMember.objects.get_or_create(
            audience=audience, email=email, defaults={"name": name}
        )
    return audience


def _ensure_email_template(theme, name, subject, paragraphs, *, force=False):
    template = EmailTemplate.objects.filter(name=name).first()
    if template and not force:
        return template
    template, _ = EmailTemplate.objects.update_or_create(
        name=name,
        defaults={"subject": subject, "email_theme": theme},
    )
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {},
                "content": [
                    {
                        "type": "rich_text",
                        "value": {"text": paragraphs, "design": {}, "audience": {}},
                    }
                ],
            },
        }
    ]
    template.save()
    return template


def _ensure_allauth_overrides(confirm, reset):
    for prefix in (
        "account/email/email_confirmation_signup",
        "account/email/email_confirmation",
    ):
        AllauthEmailOverride.objects.update_or_create(
            template_prefix=prefix,
            defaults={"email_template": confirm, "is_active": True},
        )
    AllauthEmailOverride.objects.update_or_create(
        template_prefix="account/email/password_reset_key",
        defaults={"email_template": reset, "is_active": True},
    )


def _ensure_error_pages():
    specs = {
        403: (
            "Access denied",
            "<p>You do not have permission to view this page.</p>",
        ),
        404: (
            "Page not found",
            "<p>We could not find the page you were looking for.</p>",
        ),
        500: (
            "Something went wrong",
            "<p>An unexpected error occurred. Please try again later.</p>",
        ),
    }
    for code, (title, text) in specs.items():
        page, _ = ErrorPage.objects.update_or_create(
            status_code=code, defaults={"title": title, "is_active": True}
        )
        page.body = _as_stream_data([{"type": "rich_text", "value": {"text": text}}])
        page.save()


def _ensure_demo_page(
    home, title, slug, body, *, theme=None, audience=None, denied="403", force=False
):
    existing = DemoPage.objects.child_of(home).filter(slug=slug).first()
    if existing and not force:
        return existing
    if existing:
        existing.delete()
    page = DemoPage(title=title, slug=slug)
    if theme is not None:
        page.page_theme = theme
    home.add_child(instance=page)
    page.body = _as_stream_data(body)
    if audience:
        page.audience = [{"type": "audience", "value": {"audience": audience}}]
    page.audience_denied = denied
    page.save()
    page.save_revision().publish()
    return page


def _ensure_form_page(home, *, force=False):
    existing = (
        BreadSuggestionFormPage.objects.child_of(home)
        .filter(slug="suggest-a-bread")
        .first()
    )
    if existing and not force:
        return existing
    if existing:
        existing.delete()
    page = BreadSuggestionFormPage(title="Suggest a bread", slug="suggest-a-bread")
    home.add_child(instance=page)
    page.instance_model = "bread_suggestion"
    page.require_approval = True
    page.approval_field = "is_approved"
    page.submit_label = "Suggest a bread"
    page.submit_appearance = [("appearance", {"normal": {"color": "btn-primary"}})]
    page.success_body = [
        {
            "type": "rich_text",
            "value": {
                "text": (
                    "<p>Thanks for suggesting "
                    "{{ payload.submission.title }} — your suggestion is "
                    "awaiting review by an editor.</p>"
                )
            },
        }
    ]
    page.error_body = [
        {
            "type": "rich_text",
            "value": {"text": "<p>Please fix the errors below and submit again.</p>"},
        }
    ]
    page.save()
    page.form_fields.create(
        label="Title",
        field_type="singleline",
        required=True,
        sort_order=1,
        model_field="title",
    )
    page.form_fields.create(
        label="Description",
        field_type="multiline",
        required=False,
        sort_order=2,
        model_field="description",
    )
    page.form_fields.create(
        label="Attachment",
        field_type="file",
        required=False,
        sort_order=3,
    )
    # Interleave the fields with content blocks: a heading, the title field,
    # some rich text, then the description field.
    page.body = _as_stream_data(
        [
            {"type": "header", "value": {"text": "Suggest a bread"}},
            {"type": "form_field", "value": "title"},
            {
                "type": "rich_text",
                "value": {"text": "<p>Tell us what bread we should bake next.</p>"},
            },
            {"type": "form_field", "value": "description"},
        ]
    )
    page.save()
    page.save_revision().publish()
    return page


def _ensure_showcase(theme, home, *, force=False):
    confirm = _ensure_email_template(
        theme,
        "Account confirmation",
        "Confirm your account",
        "<p>Hello {{ recipient.email }}, please confirm your account.</p>"
        "<p>Your code is <strong>{{ payload.code }}</strong>.</p>",
        force=force,
    )
    reset = _ensure_email_template(
        theme,
        "Password reset",
        "Reset your password",
        "<p>Use this link to reset your password: "
        '<a href="{{ payload.password_reset_url }}">reset</a></p>',
        force=force,
    )
    _ensure_allauth_overrides(confirm, reset)
    _ensure_error_pages()

    _ensure_demo_page(
        home,
        "Context and components",
        "context-and-components",
        [
            {
                "type": "rich_text",
                "value": {
                    "text": (
                        "<p>Signed in as "
                        "<strong>{{ user.username|default:'anonymous' }}</strong>. "
                        "This page demonstrates context models, feedback blocks and "
                        "data-input blocks.</p>"
                    )
                },
            },
            {
                "type": "alert",
                "value": {
                    "content": "<p>This is a DaisyUI alert block.</p>",
                    "color": "alert-success",
                    "style": "",
                    "direction": "",
                    "design": {},
                    "audience": {},
                },
            },
            {
                "type": "progress",
                "value": {
                    "value": 60,
                    "maximum": 100,
                    "color": "progress-primary",
                    "label": "Progress",
                    "design": {},
                    "audience": {},
                },
            },
            {
                "type": "input",
                "value": {
                    "label": "Your name",
                    "input_type": "text",
                    "name": "demo_name",
                    "placeholder": "Ada",
                    "value": "",
                    "required": False,
                    "helper_text": "A DaisyUI input block.",
                    "error_text": "",
                    "color": "",
                    "size": "",
                    "design": {},
                    "audience": {},
                },
            },
        ],
        theme=theme,
        force=force,
    )

    _ensure_demo_page(
        home,
        "Members only",
        "members-only",
        [
            {
                "type": "rich_text",
                "value": {
                    "text": (
                        "<p>This page is limited to the "
                        "<em>Staff members</em> audience.</p>"
                    )
                },
            }
        ],
        theme=theme,
        audience=["staff"],
        denied="403",
        force=force,
    )

    _ensure_form_page(home, force=force)


def _action_value(
    action,
    *,
    text,
    target="",
    clickable=False,
    color="",
    size="",
    style="",
    confirm_text="",
    confirm_icon="",
    confirm_color="",
    confirm_style="",
    confirm_direction="",
):
    """Build an ``ActionBlock`` value (button subclass + optional confirmation)."""
    value = {
        "action": action,
        "target_expression": target,
        "button": {
            "text": text,
            "icon": "",
            "icon_after": True,
            "make_parent_clickable": clickable,
            "design": {
                "button_appearance": {
                    "normal": {"color": color, "size": size, "style": style}
                }
            },
            "audience": {},
        },
    }
    if confirm_text:
        value["confirmation"] = {
            "text": confirm_text,
            "icon": confirm_icon,
            "color": confirm_color,
            "style": confirm_style,
            "direction": confirm_direction,
        }
    return value


def _dynamic_image(expression):
    return {
        "type": "image",
        "value": {
            "image": None,
            "image_source": "dynamic",
            "image_expression": expression,
            "design": {},
            "audience": {},
        },
    }


def _breads_feed():
    return _ensure_feed(
        "Breads feed",
        "bread",
        order_by="name",
        page_size=6,
        empty_message="No breads yet.",
        item=[
            {
                "type": "card",
                "value": {
                    "content": [
                        _dynamic_image("{{ bread.image }}"),
                        {
                            "type": "header",
                            "value": {
                                "text": "{{ bread.name }}",
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "text",
                            "value": {
                                "text": "{{ bread.description }}",
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "action",
                            "value": _action_value(
                                "basket.add",
                                text="Add to basket",
                                target="{{ bread.pk }}",
                                color="btn-primary",
                                size="btn-sm",
                                confirm_text="Added to your basket",
                                confirm_icon="mdi:cart-plus",
                                confirm_color="alert-success",
                            ),
                        },
                    ],
                    "design": {},
                    "alignment": {},
                    "audience": {},
                },
            }
        ],
    )


def _ensure_bread_index_page(home, theme, *, force=False):
    existing = BreadIndexPage.objects.child_of(home).filter(slug="breads").first()
    if existing and not force:
        return existing
    if existing:
        existing.delete()
    page = BreadIndexPage(title="Breads", slug="breads")
    home.add_child(instance=page)
    page.page_theme = theme
    bread_feed = _breads_feed()
    page.body = _as_stream_data(
        [
            {
                "type": "feed",
                "value": {
                    "feed": bread_feed,
                    "design": {},
                    "audience": {},
                    "layout": {},
                },
            }
        ]
    )
    page.save()
    page.save_revision().publish()
    return page


def _ensure_bread_detail_template(home, index, theme, *, force=False):
    existing = (
        BreadDetailTemplate.objects.child_of(home).filter(detail_key="bread").first()
    )
    if existing and not force:
        existing.parent_page = index
        existing.save()
        return existing
    if existing:
        existing.delete()
    page = BreadDetailTemplate(title="Bread page design", detail_key="bread")
    home.add_child(instance=page)
    page.page_theme = theme
    page.parent_page = index
    page.context_bindings = _as_stream_data(
        [
            {
                "type": "binding",
                "value": {
                    "key": "bread",
                    "mode": "url",
                    "lookup_in": "path",
                    "lookup_field": "pk",
                    "lookup_pattern": r"[\w-]+",
                },
            }
        ]
    )
    page.save()
    page.save_revision().publish()
    return page


def _sync_bread_detail_pages():
    from wagtail_daisIE.detail_pages.bridges import sync_detail_page
    from wagtail_daisIE.detail_pages.registry import get_detail_page

    config = get_detail_page("bread")
    if config is None:
        return
    for bread in Bread.objects.all():
        sync_detail_page(config, bread)


def _ensure_breads(load_image):
    if Bread.objects.exists():
        return
    specs = [
        (
            "Seeded Harvest Loaf",
            "A nutty, seeded sourdough.",
            "seeded-harvest-loaf",
            "2026-02-03",
        ),
        (
            "Dark Rye Sourdough",
            "Dense, malty rye with a crisp crust.",
            "dark-rye-sourdough",
            "2026-02-05",
        ),
        (
            "Everyday White",
            "A soft, dependable white loaf.",
            "dark-rye-sourdough",
            "2026-02-09",
        ),
        (
            "Sliced Sandwich Loaf",
            "Even slices, perfect for lunch.",
            "seeded-harvest-loaf",
            "2026-02-12",
        ),
        (
            "Olive & Rosemary",
            "Fragrant herbs and briny olives.",
            "dark-rye-sourdough",
            "2026-02-16",
        ),
        (
            "Weekend Focaccia",
            "Dimpled, olive-oil-rich and crisp.",
            "seeded-harvest-loaf",
            "2026-02-21",
        ),
    ]
    for name, description, image_key, added_on in specs:
        try:
            image = load_image(image_key)
        except Exception:
            image = None
        Bread.objects.create(
            name=name,
            description=description,
            image=image,
            added_on=date.fromisoformat(added_on),
        )


def _ensure_feed(
    name,
    context_model,
    *,
    order_by="-pk",
    page_size=6,
    infinite=False,
    empty_message="Nothing to show yet.",
    item=None,
    filters=None,
    submit_appearance=None,
):
    feed, _ = Feed.objects.update_or_create(
        name=name,
        defaults={
            "context_model": context_model,
            "order_by": order_by,
            "page_size": page_size,
            "infinite": infinite,
            "empty_message": empty_message,
        },
    )
    feed.filters = [("filter", value) for value in (filters or [])]
    feed.submit_appearance = submit_appearance or []
    feed.item = item or []
    feed.save()
    return feed


def _ensure_data_pages(theme, home, *, force=False):
    basket_feed = _ensure_feed(
        "Basket feed",
        "basket",
        order_by="",
        page_size=20,
        empty_message="Your basket is empty.",
        item=[
            {
                "type": "card",
                "value": {
                    "content": [
                        {
                            "type": "header",
                            "value": {
                                "text": "{{ basket.name }}",
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "action",
                            "value": _action_value(
                                "basket.remove",
                                text="Remove",
                                target="{{ basket.pk }}",
                                color="btn-outline",
                                size="btn-sm",
                            ),
                        },
                    ],
                    "design": {},
                    "alignment": {},
                    "audience": {},
                },
            }
        ],
    )

    _ensure_demo_page(
        home,
        "Basket",
        "basket",
        [
            {
                "type": "rich_text",
                "value": {
                    "text": (
                        "<p>You have <strong>{{ basket_count }}</strong> bread(s) "
                        "in your basket.</p>"
                    )
                },
            },
            {
                "type": "feed",
                "value": {"feed": basket_feed, "design": {}, "audience": {}},
            },
            {
                "type": "action",
                "value": _action_value(
                    "basket.clear",
                    text="Clear basket",
                    color="btn-warning",
                    size="btn-sm",
                    confirm_text="Your basket is now empty",
                    confirm_icon="mdi:basket-off",
                    confirm_color="alert-warning",
                ),
            },
        ],
        theme=theme,
        force=force,
    )

    _ensure_demo_page(
        home,
        "Bread calendar",
        "bread-calendar",
        [
            {
                "type": "rich_text",
                "value": {"text": "<p>Pick a day to see which breads were added.</p>"},
            },
            {
                "type": "calendar",
                "value": {
                    "context_model": "bread",
                    "date_field": "added_on",
                    "event": [
                        {
                            "type": "header",
                            "value": {
                                "text": "{{ bread.name }}",
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "text",
                            "value": {
                                "text": "Added {{ bread.added_on }}",
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "action",
                            "value": _action_value(
                                "basket.add",
                                text="Add",
                                target="{{ bread.pk }}",
                                color="btn-primary",
                                size="btn-sm",
                            ),
                        },
                    ],
                    "limit": 200,
                    "empty_message": "No breads to show.",
                    "design": {},
                    "audience": {},
                },
            },
        ],
        theme=theme,
        force=force,
    )


def _home_body(data, blog_index, load_image):
    """Compose the home body: hero card, paragraph, then the blog feed."""
    spec = data["home"]
    hero = spec.get("hero") or {}

    hero_image = None
    if hero.get("image"):
        try:
            hero_image = load_image(hero["image"])
        except Exception:
            hero_image = None

    background = [
        (
            "layer",
            {
                "layer_type": "gradient",
                "gradient_shape": "linear",
                "gradient_angle": 0,
                "gradient_stops": [
                    {"bg_color": "#000000", "position": 0},
                    {"bg_color": "#00000000", "position": 100},
                ],
            },
        )
    ]
    if hero_image is not None:
        background.append(
            (
                "layer",
                {
                    "layer_type": "image",
                    "image": hero_image,
                    "position": "center",
                    "size": "cover",
                    "repeat": False,
                },
            )
        )

    content = [
        (
            "header",
            {
                "text": spec.get("title", "Home"),
                "design": {"typography": {"text_color": "text-primary-content"}},
                "audience": {},
            },
        )
    ]
    if hero.get("lead"):
        content.append(
            (
                "text",
                {
                    "text": hero["lead"],
                    "design": {"typography": {"text_color": "text-primary-content"}},
                    "audience": {},
                },
            )
        )
    if hero.get("cta_text"):
        content.append(
            (
                "button",
                {
                    "text": hero["cta_text"],
                    "icon": "",
                    "icon_after": True,
                    "make_parent_clickable": False,
                    "destination": [("link_page", blog_index)],
                    "open_in_new_tab": False,
                    "design": {},
                    "audience": {},
                },
            )
        )

    body = [
        (
            "hero",
            {
                "overlay": True,
                "full_width": True,
                "align": "left",
                "content": content,
                "design": {
                    "background": background,
                    "size": {"height": {"height": "h-96"}},
                },
                "alignment": {},
                "audience": {},
            },
        )
    ]
    body += _blocks_to_stream(spec["body"], load_image=load_image)

    section = spec.get("featured_section") or {}
    if section.get("title"):
        body.append(
            (
                "header",
                {"text": section["title"], "design": {}, "audience": {}},
            )
        )

    feed = Feed.objects.filter(name="Blog feed").first()
    if feed is not None:
        body.append(("feed", {"feed": feed, "design": {}, "audience": {}}))
    return body


class Command(BaseCommand):
    help = (
        "Create demo content from demo/fixtures/content.json: homepage, blog index, "
        "posts, author snippets, themes, menus, error pages, email templates, feeds, "
        "notification audiences and an admin user (idempotent)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate demo content even if it already exists.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        data = _load_content()

        collection_names = {int(k): v for k, v in data["collections"].items()}

        # Themes first.
        light_theme = _ensure_theme("light", default=True, force=force)
        _ensure_theme(
            "dark",
            prefers_dark=True,
            colors=DARK_MODE_DEFAULT_COLORS,
            force=force,
        )
        bakery_theme = _ensure_theme("bakery", colors=BAKERY_COLORS, force=force)
        self.stdout.write(self.style.SUCCESS("Ensured default light and dark themes."))

        # Seed the bridge template before posts are published so the
        # page_published bridge has somewhere to render to.
        _ensure_email_template(
            light_theme,
            "Blog post published",
            "New bread: {{ payload.title }}",
            "<h2>{{ payload.title }}</h2><p>{{ payload.subtitle }}</p>"
            '<p><a href="{{ payload.url }}">Read the post</a></p>',
            force=force,
        )

        site = Site.objects.get(is_default_site=True)
        home = HomePage.objects.live().first()
        if not home:
            raise CommandError("No live HomePage found. Run migrations first.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "first_name": "Admin",
                "last_name": "Example",
            },
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password("changeme")
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user 'admin' / 'changeme' "
                f"({'created' if created else 'updated, password reset'})."
            )
        )

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "theme": "light",
                "dismissibles": {
                    "help": True,
                    f"whats-new-in-wagtail-{wagtail.VERSION[0]}.{wagtail.VERSION[1]}": True,
                    "editor-guide": True,
                },
            },
        )

        users_by_username: dict[str, AbstractUser] = {user.username: user}
        image_cache: dict[str, Image] = {}

        def load_image(image_key: str) -> Image:
            spec = data["images"][image_key]
            return _wagtail_image_from_spec(
                spec,
                collection_names=collection_names,
                cache=image_cache,
                users_by_username=users_by_username,
                default_user=user,
            )

        existing_index = (
            BlogIndexPage.objects.child_of(home).filter(slug="blog").first()
        )
        if existing_index and not force:
            blog_index = existing_index
            self.stdout.write("Blog index already exists; skipping blog tree creation.")
            person_by_key: dict[str, Person] = {}
        else:
            if existing_index and force:
                existing_index.delete()
            index_spec = data["blog_index"]
            blog_index = BlogIndexPage(
                title=index_spec["title"],
                slug=index_spec["slug"],
                seo_title=index_spec.get("seo_title", ""),
                introduction=index_spec.get("introduction", ""),
                image=load_image(index_spec["image"]),
                show_in_menus=True,
            )
            home.add_child(instance=blog_index)
            blog_index.save_revision().publish()

            person_by_key: dict[str, Person] = {}
            for pdata in data["people"]:
                person = Person(
                    first_name=pdata["first_name"],
                    last_name=pdata["last_name"],
                    job_title=pdata["job_title"],
                    image=load_image(pdata["image"]),
                )
                person.save()
                person.save_revision().publish()
                person_by_key[pdata["key"]] = person

            for spec in data["posts"]:
                bp = BlogPage(
                    title=spec["title"],
                    slug=spec["slug"],
                    subtitle=spec.get("subtitle", ""),
                    introduction=spec.get("introduction", ""),
                    image=load_image(spec["image"]),
                    body=_as_stream_data(
                        [
                            (
                                "breadcrumbs",
                                {
                                    "items": [],
                                    "icon": None,
                                    "home_icon": None,
                                    "design": {},
                                    "audience": {},
                                },
                            ),
                            *_blocks_to_stream(spec["body"], load_image=load_image),
                        ]
                    ),
                    date_published=date.fromisoformat(spec["date_published"]),
                )
                blog_index.add_child(instance=bp)
                for author_key in spec["authors"]:
                    bp.blog_person_relationship.create(person=person_by_key[author_key])
                for tag_name in spec["tags"]:
                    bp.tags.add(tag_name)
                bp.save_revision().publish()

            blog_index.page_theme = bakery_theme
            blog_feed = _ensure_feed(
                "Blog feed",
                "blog_post",
                order_by="-date_published",
                page_size=6,
                empty_message="No posts yet.",
                filters=[
                    {
                        "key": "blog_post:tag",
                        "button_appearance": {
                            "normal": {"color": "btn-primary", "size": "btn-sm"}
                        },
                    },
                    {
                        "key": "blog_post:author",
                        "button_appearance": {
                            "normal": {"color": "btn-secondary", "size": "btn-sm"}
                        },
                    },
                    {
                        "key": "blog_post:published",
                        "input_design": {"typography": {"font_size": "text-sm"}},
                        "label_design": {
                            "typography": {"font_weight": "font-semibold"}
                        },
                    },
                ],
                submit_appearance=[
                    ("appearance", {"normal": {"color": "btn-primary"}})
                ],
                item=[
                    {
                        "type": "card",
                        "value": {
                            "content": [
                                _dynamic_image("{{ blog_post.image }}"),
                                {
                                    "type": "header",
                                    "value": {
                                        "text": "{{ blog_post.title }}",
                                        "design": {},
                                        "audience": {},
                                    },
                                },
                                {
                                    "type": "text",
                                    "value": {
                                        "text": "{{ blog_post.introduction }}",
                                        "design": {},
                                        "audience": {},
                                    },
                                },
                                {
                                    "type": "button",
                                    "value": {
                                        "text": "Read more",
                                        "icon": "",
                                        "icon_after": True,
                                        "make_parent_clickable": True,
                                        "destination": [
                                            {
                                                "type": "link_dynamic",
                                                "value": "{{ blog_post.url }}",
                                            }
                                        ],
                                        "open_in_new_tab": False,
                                        "design": {},
                                        "audience": {},
                                    },
                                },
                            ],
                            "design": {},
                            "alignment": {},
                            "audience": {},
                        },
                    },
                ],
            )
            blog_index.body = _as_stream_data(
                [
                    {
                        "type": "feed",
                        "value": {"feed": blog_feed, "design": {}, "audience": {}},
                    }
                ]
            )
            blog_index.save_revision().publish()

            self.stdout.write(self.style.SUCCESS("Created blog index and posts."))

        # Keep home and the blog tree on one theme so navigation is consistent
        # (and independent of whether the tree was just created).
        blog_index.page_theme = bakery_theme
        blog_index.save()
        for post in BlogPage.objects.descendant_of(blog_index):
            post.page_theme = bakery_theme
            post.save()

        home.page_theme = bakery_theme
        home.page_design = _as_stream_data(
            [("defaults", {"text": {"typography": {"font_family": "heading"}}})]
        )
        home.body = _as_stream_data(_home_body(data, blog_index, load_image))
        home.save_revision().publish()

        site.site_name = site.site_name or "Demo"
        site.save()

        # Demo navigation + footer.
        logo = load_image(data["home"]["image"])
        newsletter_audience = _ensure_newsletter_audience()

        _ensure_menu(
            "Main navigation",
            layout="navbar",
            force=force,
            menu_theme=bakery_theme,
            show_search=True,
            search_url="/search/",
            item_design=[
                (
                    "item",
                    {
                        "typography": {
                            "text_color": "text-base-content",
                        }
                    },
                )
            ],
            branding=[
                (
                    "branding",
                    {
                        "logo": {
                            "image": logo,
                            "alt": site.site_name,
                            "design": {"size": {"height": {"height": "h-10"}}},
                        },
                        "wordmark": {
                            "text": site.site_name,
                            "design": {
                                "typography": {
                                    "font_family": "heading",
                                    "font_size": "text-2xl",
                                    "line_height": "leading-tight",
                                    "font_weight": "font-normal",
                                    "text_color": "text-base-content",
                                }
                            },
                        },
                        "destination": [{"type": "link_page", "value": home}],
                        "open_in_new_tab": False,
                    },
                )
            ],
            body=[
                {
                    "type": "link",
                    "value": {
                        "text": "Blog",
                        "destination": [{"type": "link_page", "value": blog_index}],
                        "open_in_new_tab": False,
                    },
                },
            ],
        )
        _ensure_menu(
            "Footer",
            layout="footer",
            force=force,
            menu_theme=bakery_theme,
            item_design=[("item", {"typography": {"text_color": "text-base-content"}})],
            body=[
                {
                    "type": "link_list",
                    "value": {
                        "heading": {"text": "Explore"},
                        "content": [
                            {
                                "text": "Home",
                                "destination": [
                                    {"type": "link_page", "value": home}
                                ],
                                "open_in_new_tab": False,
                            },
                            {
                                "text": "Blog",
                                "destination": [
                                    {"type": "link_page", "value": blog_index}
                                ],
                                "open_in_new_tab": False,
                            },
                        ],
                    },
                },
                {
                    "type": "text",
                    "value": {"text": "Wagtail demo site"},
                },
                {
                    "type": "newsletter",
                    "value": {
                        "mode": "daisie",
                        "target_audience": newsletter_audience,
                        "method": "post",
                        "email_field": "email",
                        "placeholder": "Enter your email",
                        "button_label": "Subscribe",
                        "success_message": "Thanks! You are subscribed.",
                    },
                },
            ],
        )

        _ensure_showcase(light_theme, home, force=force)
        index = _ensure_bread_index_page(home, light_theme, force=force)
        _ensure_bread_detail_template(home, index, light_theme, force=force)
        _ensure_breads(load_image)
        _sync_bread_detail_pages()
        _ensure_data_pages(light_theme, home, force=force)

        self.stdout.write(
            self.style.SUCCESS(
                "Homepage updated with body content; themes and menus created."
            )
        )
