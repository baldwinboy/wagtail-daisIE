"""Check (or regenerate) the package's allauth account template overrides.

``manage.py check_allauth_templates`` reports any drift between the committed
overrides and the installed django-allauth templates (for example after an
allauth upgrade). ``--write`` regenerates the overrides instead.
"""

from django.core.management.base import BaseCommand

from ...allauth_ui.sync import sync


class Command(BaseCommand):
    help = "Check or regenerate the allauth account template overrides."

    def add_arguments(self, parser):
        parser.add_argument(
            "--write",
            action="store_true",
            help="Regenerate the overrides instead of only reporting drift.",
        )

    def handle(self, *args, **options):
        if options["write"]:
            sync(write=True)
            self.stdout.write(self.style.SUCCESS("Allauth overrides regenerated."))
            return

        mismatches = sync(write=False)
        if not mismatches:
            self.stdout.write(self.style.SUCCESS("Allauth overrides are up to date."))
            return
        for relpath, _expected, _actual in mismatches:
            self.stderr.write(f"Drift: account/{relpath}")
        self.stderr.write(
            self.style.ERROR(
                f"{len(mismatches)} override(s) differ from installed allauth. "
                "Run with --write to regenerate."
            )
        )
        raise SystemExit(1)
