import pytest

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from wagtail.models import Page

from wagtail_daisIE.detail_pages.bridges import (
    connect_signals,
    disconnect_signals,
    find_detail_page,
    sync_detail_page,
)
from wagtail_daisIE.detail_pages.registry import (
    detail_page_for_instance,
    get_detail_page,
    get_detail_pages,
    reset_detail_pages,
)
from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.test.models import Widget, WidgetDetailPage, WidgetDetailTemplate


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _detail_pages(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
        "widget": {
            "label": "Widget",
            "model": "wagtail_daisIE_test.Widget",
            "source": "url",
            "lookup_field": "slug",
            "lookup_in": "path",
        }
    }
    settings.WAGTAIL_DAISIE_DETAIL_PAGES = {
        "widget": {
            "label": "Widget",
            "model": "wagtail_daisIE_test.Widget",
            "page_type": "wagtail_daisIE_test.WidgetDetailPage",
            "parent": "wagtail_daisIE_test.WidgetDetailTemplate",
            "lookup_field": "slug",
            "lookup_in": "path",
            "publish_field": "is_available",
            "title_source": "name",
            "slug_source": "slug",
        }
    }
    reset_context_models()
    reset_detail_pages()
    disconnect_signals()
    connect_signals()
    yield
    disconnect_signals()
    reset_detail_pages()
    reset_context_models()


def _make_template(**kwargs):
    root = Page.get_first_root_node()
    page = WidgetDetailTemplate(
        title="Widgets", slug="widgets", detail_key="widget", **kwargs
    )
    root.add_child(instance=page)
    return page


class TestRegistry:
    def test_resolves_config_and_model(self):
        config = get_detail_page("widget")
        assert config is not None
        assert config.model is Widget
        assert config.page_type is WidgetDetailPage
        assert detail_page_for_instance(Widget()) is config

    def test_missing_key_is_none(self):
        assert get_detail_page("nope") is None
        assert get_detail_pages()["widget"].label == "Widget"


class TestSync:
    def test_create_makes_live_page_when_published(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        assert page.live is True
        assert page.detail_key == "widget"
        assert page.get_parent().slug == "widgets"

    def test_create_makes_draft_when_not_published(self):
        _make_template()
        widget = Widget.objects.create(name="Rye", slug="rye", is_available=False)
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        assert page.live is False

    def test_update_refreshes_same_page(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        widget.name = "Sourdough v2"
        widget.save()
        page.refresh_from_db()
        assert page.title == "Sourdough v2"
        assert page.source_object_id == widget.pk
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 1

    def test_sync_is_idempotent(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        config = get_detail_page("widget")
        sync_detail_page(config, widget)
        sync_detail_page(config, widget)
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 1

    def test_find_detail_page(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        config = get_detail_page("widget")
        assert find_detail_page(config, widget) is not None

    def test_delete_removes_page_and_fixes_tree(self):
        template = _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        widget.delete()
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 0
        template.refresh_from_db()
        assert template.numchild == 0


class TestDesignInheritance:
    def test_design_source_uses_template(self):
        theme = DaisyUITheme.objects.create(name="brand", default=True)
        template = _make_template(page_theme=theme)
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        assert page.design_template_id == template.pk
        assert page.get_design_source() == template

    def test_opt_out_uses_own_design(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        page.use_template_design = False
        page.save()
        assert page.get_design_source() == page

    def test_context_binding_resolves_by_page_slug(self):
        template = _make_template()
        template.context_bindings = [
            {
                "type": "binding",
                "value": {
                    "key": "widget",
                    "mode": "url",
                    "lookup_in": "path",
                    "lookup_field": "slug",
                },
            }
        ]
        template.save()
        template.save_revision().publish()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        page.refresh_from_db()
        from django.test import RequestFactory

        request = RequestFactory().get(page.url)
        context = page.get_context(request)
        assert context["widget"] == widget


class TestSignals:
    def test_connect_and_disconnect_are_idempotent(self):
        assert connect_signals() >= 2
        disconnect_signals()
        disconnect_signals()

    def test_unique_constraint_on_concrete_subclass(self):
        _make_template()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)
        duplicate = WidgetDetailPage(
            title="Duplicate",
            slug="duplicate",
            detail_key="widget",
            source_content_type=page.source_content_type,
            source_object_id=widget.pk,
        )
        with pytest.raises((IntegrityError, ValidationError)):
            duplicate.full_clean()
