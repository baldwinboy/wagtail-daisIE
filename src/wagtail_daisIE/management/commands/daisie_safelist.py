"""Generate the Tailwind safelist from the package's class choices.

The design system builds class strings at runtime (``block_css``), so Tailwind
cannot discover them by scanning templates. Every class an editor can choose is
declared in :mod:`wagtail_daisIE.choices`; this command turns those choices into
``@source inline(...)`` directives in ``tailwind/safelist.css``, which the
committed ``daisie.css`` is built from.
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from wagtail_daisIE import choices
from wagtail_daisIE.choices.responsive import (
    RESPONSIVE_BREAKPOINTS,
    RESPONSIVE_CLASSES,
)


#: Classes composed in Python or templates from values that are not choices.
RUNTIME_CLASSES = {
    # ``build_button_css`` / ``build_table_css`` literals.
    "btn",
    "table",
    "table-zebra",
    "table-pin-rows",
    "table-pin-cols",
    # ``dynamic.feeds.layout_class_map`` literals.
    "divide-base-300",
    "divide-y",
    "flex",
    "flex-row",
    "flex-nowrap",
    "flex-wrap",
    "grid",
    "overflow-x-auto",
    "snap-x",
    # ``templates/wagtail_daisIE/tags/messages.html``.
    "alert-error",
    "alert-info",
    "alert-success",
    "alert-warning",
    # Feed container hook used by the layout classes.
    "daisie-feed__item",
}

#: Numeric utilities generated from integer fields, not choice lists.
RANGE_DIRECTIVES = (
    # BorderBlock.border_width (max_value=999).
    "border-{2..999}",
    # TableBorderSpacingBlock (max_value=96).
    "border-spacing-{1..96}",
    "border-spacing-x-{1..96}",
    "border-spacing-y-{1..96}",
    # GridBlock.num_columns (min_value=1, max_value=6).
    "md:grid-cols-{1..6}",
)


def _class_tokens(value):
    """Yield individual class tokens from choices, mappings and sequences."""
    if isinstance(value, str):
        yield from (part for part in value.split() if part and part != "None")
    elif isinstance(value, dict):
        for item in value.values():
            yield from _class_tokens(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (list, tuple)) and item:
                yield from _class_tokens(item[0])
            else:
                yield from _class_tokens(item)


def _choice_tokens(name):
    """Yield the class tokens declared by the named export in ``choices``."""
    if not hasattr(choices, name):
        raise CommandError(f"choices.__all__ lists {name!r}, but it is not imported.")
    yield from _class_tokens(getattr(choices, name))


class Command(BaseCommand):
    help = "Generate tailwind/safelist.css from the package's class choices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=None,
            help="Output path (defaults to the package tailwind/safelist.css).",
        )
        parser.add_argument(
            "--responsive-output",
            default=None,
            help=(
                "Responsive output path (defaults to the package "
                "tailwind/responsive-safelist.css)."
            ),
        )

    def handle(self, *args, **options):
        from wagtail_daisIE.dynamic import feeds

        classes = set()
        for name in choices.__all__:
            classes.update(_choice_tokens(name))

        # Button states render with ``hover:``/``active:`` variants.
        button_values = set()
        for name in (
            "DAISYUI_BUTTON_COLOR_CHOICES",
            "DAISYUI_BUTTON_STYLE_CHOICES",
            "DAISYUI_BUTTON_SIZE_CHOICES",
            "DAISYUI_BUTTON_BEHAVIOR_CHOICES",
            "DAISYUI_BUTTON_MODIFIER_CHOICES",
        ):
            button_values.update(_choice_tokens(name))
        for value in button_values:
            classes.add(value)
            classes.add(f"hover:{value}")
            classes.add(f"active:{value}")

        # Typography colour/decoration supports hover/active states.
        for name in (
            "DAISYUI_TEXT_COLOR_CHOICES",
            "TEXT_DECORATION_CHOICES",
            "DECORATION_COLOR_CHOICES",
            "DECORATION_THICKNESS_CHOICES",
        ):
            for value in _choice_tokens(name):
                classes.add(value)
                classes.add(f"hover:{value}")
                classes.add(f"active:{value}")

        # Placeholder colours render through the ``::placeholder`` variant.
        for value in _choice_tokens("DAISYUI_TEXT_COLOR_CHOICES"):
            classes.add(f"placeholder:{value}")

        # ``build_border_css`` prefixes the stored border-style value.
        for value in _choice_tokens("BORDER_STYLE_CHOICES"):
            classes.add(f"border-{value}")

        # Runtime-built layout classes (feed containers and their gaps).
        classes.update(_class_tokens(feeds.GRID_COLUMNS))
        classes.update(_class_tokens(feeds.GAP_CHOICES))

        # Border width 1 renders as the bare ``border`` utility.
        classes.add("border")
        classes.update(RUNTIME_CLASSES)

        lines = [
            "/* Generated by `manage.py daisie_safelist`. Do not edit by hand. */",
        ]
        lines.extend(f'@source inline("{value}");' for value in sorted(classes))
        lines.extend(f'@source inline("{pattern}");' for pattern in RANGE_DIRECTIVES)

        responsive_lines = [
            "/* Generated by `manage.py daisie_safelist`. Do not edit by hand. */",
        ]
        prefixes = ",".join(f"{value}:" for value, _label in RESPONSIVE_BREAKPOINTS)
        responsive_lines.extend(
            f'@source inline("{{{prefixes}}}{value}");'
            for value in sorted(RESPONSIVE_CLASSES)
        )

        output = options["output"]
        path = (
            Path(output)
            if output
            else Path(__file__).resolve().parents[2] / "tailwind" / "safelist.css"
        )
        responsive_output = options["responsive_output"]
        responsive_path = (
            Path(responsive_output)
            if responsive_output
            else Path(__file__).resolve().parents[2]
            / "tailwind"
            / "responsive-safelist.css"
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        responsive_path.write_text("\n".join(responsive_lines) + "\n", encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {path} ({len(classes)} classes, "
                f"{len(RANGE_DIRECTIVES)} ranges) and {responsive_path} "
                f"({len(RESPONSIVE_CLASSES)} responsive classes)"
            )
        )
