"""Recover menu search blocks from pre-removal Wagtail revisions.

The menu-level ``show_search`` fields were removed in favour of the reusable
``search`` menu-item block. Revision history still contains the old values for
menus that were saved before the removal, so this command can restore the
equivalent ``search`` block without overwriting any other menu content.

The command is dry-run by default. Pass ``--apply`` to write changes.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q
from wagtail.models import Revision

from wagtail_daisIE.menus.models import DaisyUIMenu


SEARCH_BLOCK_TYPE = "search"


def _has_search_block(body) -> bool:
    return any(
        isinstance(item, dict) and item.get("type") == SEARCH_BLOCK_TYPE
        for item in (body.raw_data if body else [])
    )


def _search_block(*, url: str, parameter: str, placeholder: str) -> dict:
    return {
        "type": SEARCH_BLOCK_TYPE,
        "value": {
            "search_url": url or "/search/",
            "search_parameter": parameter or "query",
            "search_placeholder": placeholder or "Search",
            "method": "get",
            "input_color": "",
            "design": {},
            "audience": {"audience": []},
        },
    }


def _legacy_values(menu: DaisyUIMenu) -> dict | None:
    """Return the newest revision content that had search enabled."""
    content_type = ContentType.objects.get_for_model(
        DaisyUIMenu,
        for_concrete_model=False,
    )
    revisions = (
        Revision.objects.filter(
            Q(content_type=content_type) | Q(base_content_type=content_type),
            object_id=str(menu.pk),
        )
        .order_by("-created_at")
        .values_list("content", flat=True)
    )
    for content in revisions:
        if not isinstance(content, dict) or not content.get("show_search"):
            continue
        return {
            "url": content.get("search_url") or "/search/",
            "parameter": content.get("search_parameter") or "query",
            "placeholder": content.get("search_placeholder") or "Search",
        }
    return None


class Command(BaseCommand):
    help = (
        "Restore menu search blocks from revisions saved before the menu-level "
        "search fields were removed. Dry-run unless --apply is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write recovered search blocks. Without this, only report.",
        )
        parser.add_argument(
            "--menu",
            default="",
            help="Limit recovery to one menu name.",
        )

    def handle(self, *args, **options):
        menus = DaisyUIMenu.objects.all().order_by("name")
        if options["menu"]:
            menus = menus.filter(name=options["menu"])

        recovered = 0
        skipped = 0
        missing = 0

        for menu in menus:
            if _has_search_block(menu.body):
                skipped += 1
                continue

            legacy = _legacy_values(menu)
            if legacy is None:
                missing += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"No recoverable search revision for menu {menu.name!r}."
                    ),
                )
                continue

            self.stdout.write(
                f"Recover search block for menu {menu.name!r}: "
                f"{legacy['url']} ({legacy['parameter']!r})."
            )
            if options["apply"]:
                body = list(menu.body.raw_data or [])
                body.append(
                    _search_block(
                        url=legacy["url"],
                        parameter=legacy["parameter"],
                        placeholder=legacy["placeholder"],
                    ),
                )
                menu.body = body
                menu.save()
            recovered += 1

        summary = (
            f"Recovered {recovered}, skipped {skipped} (already has search), "
            f"unrecoverable {missing}."
        )
        if options["apply"]:
            self.stdout.write(self.style.SUCCESS(summary))
        else:
            self.stdout.write(self.style.WARNING(f"Dry run: {summary}"))
