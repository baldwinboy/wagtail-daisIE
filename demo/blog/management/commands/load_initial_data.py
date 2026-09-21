"""Load bakerydemo-equivalent content from ``demo/fixtures``.

Content (pages, posts, people, images) is read from
``demo/fixtures/content.json``; media is read from
``demo/fixtures/media/original_images``. DaisyUI themes and menus are seeded
programmatically because they use revisions and orderable models that are a
poor fit for flat fixtures.
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
    BreadSuggestionFormField,
    BreadSuggestionFormPage,
    Person,
)
from wagtail_daisIE.models import (
    AllauthEmailOverride,
    Audience,
    AudienceMember,
    DaisyUIMenu,
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeColors,
    DaisyUIThemeEffects,
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
    DaisyUIThemeRadii,
    DaisyUIThemeSizes,
    EmailTemplate,
    ErrorPage,
    Feed,
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

GOOGLE_FONT_CDN = (
    "https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@400;600;700&display=swap"
)


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

    Image.objects.filter(pk=img.pk).update(created_at=parse_datetime(spec["created_at"]))

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


def _stream_value(model, field_name, data):
    """Convert a list of ``{"type", "value"}`` dicts (or tuples) into a bound
    ``StreamValue`` so nested choosers are converted eagerly before saving."""
    if not isinstance(data, list):
        return data
    stream_block = model._meta.get_field(field_name).stream_block
    tuples = [
        (item["type"], item["value"]) if isinstance(item, dict) else item
        for item in data
    ]
    return stream_block.to_python(tuples)


def _ensure_menu(
    name: str,
    *,
    layout: str,
    body: list[dict[str, Any]],
    force: bool = False,
    **defaults: Any,
) -> DaisyUIMenu:
    """Create (or refresh) a demo menu snippet."""
    menu, created = DaisyUIMenu.objects.get_or_create(name=name, defaults={"layout": layout})
    if created or force:
        menu.layout = layout
        for field, field_value in defaults.items():
            setattr(menu, field, _stream_value(menu, field, field_value))
        menu.body = _stream_value(menu, "body", body)
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
        page.body = [{"type": "rich_text", "value": {"text": text}}]
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
    page.body = body
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
    page.field_map = [
        ("mapping", {"form_field": "title", "model_field": "title"}),
        ("mapping", {"form_field": "description", "model_field": "description"}),
    ]
    page.save()
    page.form_fields.create(
        label="Title", field_type="singleline", required=True, sort_order=1
    )
    page.form_fields.create(
        label="Description", field_type="multiline", required=False, sort_order=2
    )
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
        '<p>Use this link to reset your password: '
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


def _ensure_breads(load_image):
    if Bread.objects.exists():
        return
    specs = [
        ("Seeded Harvest Loaf", "A nutty, seeded sourdough.", "seeded-harvest-loaf", "2026-02-03"),
        ("Dark Rye Sourdough", "Dense, malty rye with a crisp crust.", "dark-rye-sourdough", "2026-02-05"),
        ("Everyday White", "A soft, dependable white loaf.", "dark-rye-sourdough", "2026-02-09"),
        ("Sliced Sandwich Loaf", "Even slices, perfect for lunch.", "seeded-harvest-loaf", "2026-02-12"),
        ("Olive & Rosemary", "Fragrant herbs and briny olives.", "dark-rye-sourdough", "2026-02-16"),
        ("Weekend Focaccia", "Dimpled, olive-oil-rich and crisp.", "seeded-harvest-loaf", "2026-02-21"),
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
    feed.filters = [("filter", {"key": key}) for key in (filters or [])]
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
                "type": "header",
                "value": {"text": "{{ basket.name }}", "design": {}, "audience": {}},
            },
            {
                "type": "action",
                "value": {
                    "action": "basket.remove",
                    "label": "Remove",
                    "button_class": "btn btn-sm btn-outline",
                    "target_expression": "basket.pk",
                    "confirm": "",
                    "design": {},
                    "audience": {},
                },
            },
        ],
    )
    breads_feed = _ensure_feed(
        "Breads feed",
        "bread",
        order_by="name",
        page_size=6,
        empty_message="No breads yet.",
        item=[
            {
                "type": "image",
                "value": {
                    "image": None,
                    "image_source": "dynamic",
                    "image_expression": "bread.image",
                    "design": {},
                    "audience": {},
                },
            },
            {
                "type": "header",
                "value": {"text": "{{ bread.name }}", "design": {}, "audience": {}},
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
                "value": {
                    "action": "basket.add",
                    "label": "Add to basket",
                    "button_class": "btn btn-primary btn-sm",
                    "target_expression": "bread.pk",
                    "confirm": "",
                    "design": {},
                    "audience": {},
                },
            },
        ],
    )

    _ensure_demo_page(
        home,
        "Breads and basket",
        "breads",
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
                "value": {"feed": basket_feed.pk, "design": {}, "audience": {}},
            },
            {
                "type": "action",
                "value": {
                    "action": "basket.clear",
                    "label": "Clear basket",
                    "button_class": "btn btn-warning btn-sm",
                    "target_expression": "",
                    "confirm": "Empty your basket?",
                    "design": {},
                    "audience": {},
                },
            },
            {
                "type": "feed",
                "value": {"feed": breads_feed.pk, "design": {}, "audience": {}},
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
                "value": {
                    "text": "<p>Pick a day to see which breads were added.</p>"
                },
            },
            {
                "type": "calendar",
                "value": {
                    "context_model": "bread",
                    "date_field": "added_on",
                    "event": [
                        {
                            "type": "header",
                            "value": {"text": "{{ bread.name }}", "design": {}, "audience": {}},
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
                            "value": {
                                "action": "basket.add",
                                "label": "Add",
                                "button_class": "btn btn-sm btn-primary",
                                "target_expression": "bread.pk",
                                "confirm": "",
                                "design": {},
                                "audience": {},
                            },
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


class Command(BaseCommand):
    help = (
        "Create demo content from demo/fixtures/content.json: homepage, blog index, "
        "posts, author snippets, themes, menus and an admin user (idempotent)."
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

        collection_names = {
            int(k): v for k, v in data["collections"].items()
        }

        # Themes first.
        light_theme = _ensure_theme("light", default=True, force=force)
        _ensure_theme(
            "dark",
            prefers_dark=True,
            colors=DARK_MODE_DEFAULT_COLORS,
            force=force,
        )
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

        existing_index = BlogIndexPage.objects.child_of(home).filter(slug="blog").first()
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
                    body=_blocks_to_stream(spec["body"], load_image=load_image),
                    date_published=date.fromisoformat(spec["date_published"]),
                )
                blog_index.add_child(instance=bp)
                for author_key in spec["authors"]:
                    bp.blog_person_relationship.create(person=person_by_key[author_key])
                for tag_name in spec["tags"]:
                    bp.tags.add(tag_name)
                bp.save_revision().publish()

            blog_index.page_theme = light_theme
            blog_feed = _ensure_feed(
                "Blog feed",
                "blog_post",
                order_by="-date_published",
                page_size=6,
                empty_message="No posts yet.",
                filters=["blog_post:tag", "blog_post:author"],
                item=[
                    {
                        "type": "image",
                        "value": {
                            "image": None,
                            "image_source": "dynamic",
                            "image_expression": "blog_post.image",
                            "design": {},
                            "audience": {},
                        },
                    },
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
                        "type": "link",
                        "value": {
                            "text": "Read more",
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
            )
            blog_index.body = [
                {
                    "type": "feed",
                    "value": {"feed": blog_feed.pk, "design": {}, "audience": {}},
                }
            ]
            blog_index.save_revision().publish()

            self.stdout.write(self.style.SUCCESS("Created blog index and posts."))

        home.page_theme = light_theme
        home.body = _stream_value(
            home, "body", _blocks_to_stream(data["home"]["body"], load_image=load_image)
        )
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
            menu_theme=light_theme,
            show_search=True,
            search_url="/search/",
            item_design=[
                ("item", {"typography": {"text_color": "text-base-content", "font_family": "body"}})
            ],
            branding=[
                (
                    "branding",
                    {
                        "logo": {"image": logo, "alt": site.site_name},
                        "wordmark": {"text": site.site_name},
                        "destination": [{"type": "link_page", "value": home.pk}],
                        "open_in_new_tab": False,
                    },
                )
            ],
            body=[
                {
                    "type": "link",
                    "value": {
                        "text": "Home",
                        "destination": [{"type": "link_page", "value": home.pk}],
                        "open_in_new_tab": False,
                    },
                },
                {
                    "type": "link",
                    "value": {
                        "text": "Blog",
                        "destination": [{"type": "link_page", "value": blog_index.pk}],
                        "open_in_new_tab": False,
                    },
                },
                {
                    "type": "text",
                    "value": {
                        "text": "Hi {{ user.username|default:'guest' }}",
                        "design": {},
                        "audience": {},
                    },
                },
            ],
        )
        _ensure_menu(
            "Footer",
            layout="footer",
            force=force,
            menu_theme=light_theme,
            item_design=[
                ("item", {"typography": {"text_color": "text-base-content"}})
            ],
            body=[
                {
                    "type": "link_list",
                    "value": {
                        "heading": {"text": "Explore"},
                        "content": [
                            {
                                "text": "Home",
                                "destination": [{"type": "link_page", "value": home.pk}],
                                "open_in_new_tab": False,
                            },
                            {
                                "text": "Blog",
                                "destination": [{"type": "link_page", "value": blog_index.pk}],
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
        _ensure_breads(load_image)
        _ensure_data_pages(light_theme, home, force=force)

        self.stdout.write(
            self.style.SUCCESS(
                "Homepage updated with body content; themes and menus created."
            )
        )
