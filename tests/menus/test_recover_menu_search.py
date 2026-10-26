import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from wagtail.models import Revision

from wagtail_daisIE.menus.models import DaisyUIMenu


pytestmark = pytest.mark.django_db


def _menu_with_legacy_revision(name="Recovery menu"):
    menu = DaisyUIMenu.objects.create(name=name)
    content_type = ContentType.objects.get_for_model(
        DaisyUIMenu,
        for_concrete_model=False,
    )
    Revision.objects.create(
        content_type=content_type,
        base_content_type=content_type,
        object_id=str(menu.pk),
        object_str=str(menu),
        content={
            "show_search": True,
            "search_url": "/find/",
            "search_parameter": "q",
            "search_placeholder": "Find",
        },
    )
    return menu


def test_recover_menu_search_is_dry_run_by_default(capsys):
    menu = _menu_with_legacy_revision()
    call_command("recover_menu_search_blocks", "--menu", "Recovery menu")
    menu.refresh_from_db()

    assert not menu.body.raw_data
    assert "Dry run" in capsys.readouterr().out


def test_recover_menu_search_appends_the_search_block():
    menu = _menu_with_legacy_revision()
    call_command(
        "recover_menu_search_blocks",
        "--apply",
        "--menu",
        "Recovery menu",
    )
    menu.refresh_from_db()

    assert len(menu.body.raw_data) == 1
    block = menu.body.raw_data[0]
    assert block["type"] == "search"
    assert block["value"]["search_url"] == "/find/"
    assert block["value"]["search_parameter"] == "q"
    assert block["value"]["search_placeholder"] == "Find"


def test_recover_menu_search_skips_menus_that_already_have_search():
    menu = _menu_with_legacy_revision()
    menu.body = [
        {
            "type": "search",
            "value": {
                "search_url": "/search/",
                "search_parameter": "query",
                "search_placeholder": "Search",
                "method": "get",
                "input_color": "",
                "design": {},
                "audience": {"audience": []},
            },
        },
    ]
    menu.save()

    call_command(
        "recover_menu_search_blocks",
        "--apply",
        "--menu",
        "Recovery menu",
    )
    menu.refresh_from_db()

    assert len(menu.body.raw_data) == 1
