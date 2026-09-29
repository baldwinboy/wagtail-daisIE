import pytest

from django.test import RequestFactory
from wagtail.models import Page

from wagtail_daisIE.detail_pages.bridges import (
    connect_signals,
    disconnect_signals,
    find_detail_page,
)
from wagtail_daisIE.detail_pages.registry import (
    detail_page_for_instance,
    get_detail_page,
    reset_detail_pages,
)
from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.test.models import (
    Widget,
    WidgetDetailPage,
    WidgetDetailTemplate,
    WidgetIndexPage,
)


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
            "parent": "wagtail_daisIE_test.WidgetIndexPage",
            "template_page": "wagtail_daisIE_test.WidgetDetailTemplate",
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


def _make_index():
    root = Page.get_first_root_node()
    page = WidgetIndexPage(title="Widgets index", slug="widgets-index")
    root.add_child(instance=page)
    return page


def _make_template(index, **kwargs):
    root = Page.get_first_root_node()
    page = WidgetDetailTemplate(
        title="Widget design", detail_key="widget", parent_page=index, **kwargs
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


class TestSync:
    def test_create_live_or_draft_and_update(self):
        _make_template(_make_index())
        live = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=live.pk)
        assert page.live is True
        assert page.detail_key == "widget"
        assert page.get_parent().slug == "widgets-index"

        draft = Widget.objects.create(name="Rye", slug="rye", is_available=False)
        assert WidgetDetailPage.objects.get(source_object_id=draft.pk).live is False

        live.name = "Sourdough v2"
        live.save()
        page.refresh_from_db()
        assert page.title == "Sourdough v2"
        assert WidgetDetailPage.objects.filter(source_object_id=live.pk).count() == 1

    def test_find_detail_page_and_guards(self):
        _make_template(_make_index())
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        config = get_detail_page("widget")
        # Identity matters: callers update in place rather than duplicating.
        assert find_detail_page(config, widget) == WidgetDetailPage.objects.get(
            source_object_id=widget.pk
        )
        # A page cannot be bound before the record has a primary key.
        assert find_detail_page(config, None) is None
        assert find_detail_page(config, Widget(name="Unsaved")) is None

    def test_delete_removes_page_and_fixes_tree(self):
        index = _make_index()
        _make_template(index)
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        widget.delete()
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 0
        index.refresh_from_db()
        assert index.numchild == 0


class TestDesignInheritance:
    def test_design_source_opt_out_and_binding(self):
        theme = DaisyUITheme.objects.create(name="brand", default=True)
        template = _make_template(_make_index(), page_theme=theme)
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
        assert page.design_template_id == template.pk
        assert page.get_design_source() == template

        page.refresh_from_db()
        context = page.get_context(RequestFactory().get(page.url))
        assert context["widget"] == widget

        page.use_template_design = False
        page.save()
        assert page.get_design_source() == page


class TestSignals:
    def test_connect_and_disconnect_are_idempotent(self):
        assert connect_signals() >= 2
        disconnect_signals()
        disconnect_signals()
        Widget.objects.create(name="After", slug="after", is_available=True)
        assert WidgetDetailPage.objects.filter(slug="after").count() == 0

        connect_signals()
        widget = Widget.objects.create(name="Back", slug="back", is_available=True)
        connect_signals()
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 1
