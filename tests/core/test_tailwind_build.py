from pathlib import Path


INPUT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "wagtail_daisIE"
    / "tailwind"
    / "input.css"
)


def test_minimal_input_is_exact():
    assert INPUT.read_text(encoding="utf-8").strip().splitlines() == [
        '@import "tailwindcss" source(none);',
        '@plugin "@tailwindcss/typography";',
        '@plugin "daisyui" { include: button, input, menu, megamenu, navbar, footer }',
    ]
