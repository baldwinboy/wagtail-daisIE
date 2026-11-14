import pytest

from wagtail_daisIE.tailwindcss._extractor import parse_candidate, parse_classnames


@pytest.mark.parametrize(
    "token",
    [
        "flex",
        "a",
        "@container",
        "items-center",
        "items--center",
        "px-2.5",
        "hover:flex",
        "hover:focus:flex",
        "[color:red]",
        "![color:red]",
        "[color:red]!",
        "[color:red]/20",
        "![color:red]/20",
        "[color:red]/20!",
        "bg-[#0088cc]",
        "bg-[#0088cc]/20",
        "bg-(--my-color)",
        "bg-(length:--x)",
        "bg-(--x,20%)",
        "!bg-red-500/20",
        "bg-red-500/20!",
        "[&>[data-slot=icon]:last-child]:right-2.5",
        "sm:[&>[data-slot=icon]:last-child]:right-2.5",
        "data-[state=pending]:flex",
        "group-hover/foo:flex",
        "group-hover/[.parent]:flex",
        "supports-(--x):flex",
        "@[36rem]:flex",
        "@-[36rem]:flex",
        "@md:flex",
        "2xl:flex",
        "*:flex",
        "**:flex",
        "-translate-x-full",
        "from-15%",
        "text-Title1_Strong",
        "w-1/2",
        "[:is(italic):is(underline)]:flex",
        "[CssClass('gap-y-4')]:flex",
    ],
)
def test_valid_candidates(token):
    candidate = parse_candidate(token)
    assert candidate is not None
    assert candidate.raw == token


@pytest.mark.parametrize(
    "token",
    [
        "!flex!",
        "bg-red-500!/20",
        "bg-red-500/20/20",
        "bg-[red]-[blue]",
        "bg-[red][blue]",
        "flex!block",
        "_blank",
        "hover:_blank",
        "[foo]/bar:flex",
        "bg-[${x}]",
        "[color:${x}]",
        "bg-(--x,${y})",
        "[]",
        "[color:red",
        "bg-(",
        "foo/",
        "foo/[]",
        "foo/()",
        "foo/(-)",
        "foo/(--)",
        "[]:flex",
        "group-hover/foo/bar:flex",
        "[:is(italic):is(underline)]",
        "[CssClass('gap-y-4')]",
    ],
)
def test_invalid_candidates(token):
    assert parse_candidate(token) is None


def test_variant_and_utility_parts():
    candidate = parse_candidate("lg:hover:bg-red-500/50!")
    assert candidate is not None
    assert candidate.variants == ("lg:", "hover:")
    assert candidate.utility == "bg-red-500"
    assert candidate.base == "bg-red"
    assert candidate.value == "500"
    assert candidate.modifier == "/50"
    assert candidate.important_after is True
    assert candidate.important_before is False


def test_leading_important_and_negative_utility():
    candidate = parse_candidate("!-mt-4")
    assert candidate is not None
    assert candidate.important_before is True
    assert candidate.base == "-mt"
    assert candidate.value == "4"


def test_arbitrary_property_has_no_value_split():
    candidate = parse_candidate("[color:red]")
    assert candidate is not None
    assert candidate.base == "[color:red]"
    assert candidate.value is None


def test_parse_classnames_splits_ascii_whitespace():
    parsed = list(parse_classnames(" flex\titems-center\nbg-red-500 "))
    assert [item.utility for item in parsed] == [
        "flex",
        "items-center",
        "bg-red-500",
    ]
