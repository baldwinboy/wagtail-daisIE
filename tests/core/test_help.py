from django.urls import reverse
from wagtail.admin.menu import help_menu

from wagtail_daisIE.help import _visible_sections


def _guide_pages():
    return [page for section in _visible_sections() for page in section["pages"]]


def test_guide_index_renders(admin_client):
    response = admin_client.get(reverse("wagtail_daisIE:guide"))
    assert response.status_code == 200
    assert b"DaisyUI Editor Guide" in response.content


def test_every_guide_page_renders(admin_client):
    pages = _guide_pages()
    assert pages
    for page in pages:
        response = admin_client.get(
            reverse("wagtail_daisIE:guide-page", args=[page["slug"]])
        )
        assert response.status_code == 200, page["slug"]
        assert b"<h1" in response.content, page["slug"]


def test_unknown_guide_page_is_404(admin_client):
    response = admin_client.get(
        reverse("wagtail_daisIE:guide-page", args=["not-a-page"])
    )
    assert response.status_code == 404


def test_block_reference_lists_a_block(admin_client):
    response = admin_client.get(
        reverse("wagtail_daisIE:guide-page", args=["block-reference"])
    )
    assert response.status_code == 200
    assert b"card" in response.content


def test_guide_is_in_the_help_menu():
    names = [item.name for item in help_menu.registered_menu_items]
    assert "daisyui-editor-guide" in names
