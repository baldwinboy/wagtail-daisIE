"""Build the committed minimal Tailwind base stylesheet."""

from __future__ import annotations

import subprocess

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Build the minimal committed Tailwind base stylesheet."

    def handle(self, *args, **options):
        package_root = Path(__file__).resolve().parents[2]
        input_path = package_root / "tailwind" / "input.css"
        output_path = (
            package_root / "static" / "wagtail_daisIE" / "css" / "daisie-base.css"
        )

        if not input_path.exists():
            raise CommandError(f"Missing Tailwind input: {input_path}")

        try:
            from django_tailwind_cli.config import ConfigurationError, get_config
            from django_tailwind_cli.management.commands._download import (
                ensure_cli_binary,
            )
        except ImportError as exc:
            raise CommandError(
                "django-tailwind-cli is required to build daisie-base.css."
            ) from exc

        if not getattr(settings, "TAILWIND_CLI_USE_DAISY_UI", False):
            raise CommandError(
                "Set TAILWIND_CLI_USE_DAISY_UI = True before building the base CSS."
            )

        try:
            ensure_cli_binary()
            config = get_config()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            command = [
                str(config.cli_path),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--minify",
            ]
            subprocess.run(  # noqa: S603 - command uses the configured CLI
                command,
                cwd=getattr(settings, "BASE_DIR", None),
                check=True,
                timeout=float(getattr(settings, "TAILWIND_CSS_TIMEOUT", 30)),
            )
        except (OSError, subprocess.SubprocessError, ConfigurationError) as exc:
            raise CommandError(f"Tailwind base build failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Wrote {output_path} from {input_path}"))
