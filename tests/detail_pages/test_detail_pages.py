import pytest

from django.test import RequestFactory
from wagtail.models import Page

from wagtail_daisIE.detail_pages.bridges import (
    connect_signals,
    disconnect_signals,
    find_detail_page,
)
from wagtail_daisIE.detail_pages.exceptions import DetailPageConfigurationError
from wagtail_daisIE.detail_pages.registry import (
    detail_page_for_instance,
    get_detail_page,
    reset_detail_pages,
)
from wagtail_daisIE.detail_pages.validation import validate_detail_pages
from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.test.models import (
    Widget,
    WidgetDetailPage,
    WidgetDetailTemplate,
    WidgetGeneratedPagesIndexPage,
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
            "generated_index": "wagtail_daisIE_test.WidgetGeneratedPagesIndexPage",
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


def _make_generated_index(index):
    page = WidgetGeneratedPagesIndexPage(
        title="Generated widgets", slug="generated-widgets"
    )
    index.add_child(instance=page)
    return page


def _make_template(**kwargs):
    root = Page.get_first_root_node()
    page = WidgetDetailTemplate(title="Widget design", detail_key="widget", **kwargs)
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def _structure():
    index = _make_index()
    generated = _make_generated_index(index)
    template = _make_template()
    return index, generated, template


class TestRegistry:
    def test_resolves_config_and_model(self):
        config = get_detail_page("widget")
        assert config is not None
        assert detail_page_for_instance(Widget()) is config


class TestSync:
    def test_create_live_and_update(self):
        _index, generated, _template = _structure()
        live = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=live.pk)
        assert page.live is True
        assert page.detail_key == "widget"
        assert page.get_parent().specific == generated

        live.name = "Sourdough v2"
        live.save()
        page.refresh_from_db()
        assert page.title == "Sourdough v2"
        assert WidgetDetailPage.objects.filter(source_object_id=live.pk).count() == 1

    def test_non_public_record_creates_no_page_and_deletes_existing(self):
        _structure()
        draft = Widget.objects.create(name="Rye", slug="rye", is_available=False)
        assert not WidgetDetailPage.objects.filter(source_object_id=draft.pk).exists()

        draft.is_available = True
        draft.save()
        assert WidgetDetailPage.objects.filter(source_object_id=draft.pk).exists()

        draft.is_available = False
        draft.save()
        assert not WidgetDetailPage.objects.filter(source_object_id=draft.pk).exists()

    def test_find_detail_page_and_guards(self):
        _structure()
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
        _index, generated, _template = _structure()
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        widget.delete()
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 0
        generated.refresh_from_db()
        assert generated.numchild == 0


class TestTemplateContext:
    def test_renders_template_bindings_and_page_has_no_design_fields(self):
        theme = DaisyUITheme.objects.create(name="brand", default=True)
        template = _make_template(page_theme=theme)
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
        _make_generated_index(_make_index())
        widget = Widget.objects.create(
            name="Sourdough", slug="sourdough", is_available=True
        )
        page = WidgetDetailPage.objects.get(source_object_id=widget.pk)

        assert not hasattr(page, "body")
        assert not hasattr(page, "design_template")
        assert not hasattr(page, "use_template_design")
        assert not hasattr(page, "page_design")

        context = page.get_context(RequestFactory().get(page.url))
        assert context["detail_template"] == template
        assert context["detail_template_body"] == template.body
        assert context["widget"] == widget
        assert context["daisyui_theme"] == theme

    def test_missing_template_raises(self):
        index = _make_index()
        _make_generated_index(index)
        with pytest.raises(DetailPageConfigurationError):
            Widget.objects.create(
                name="No template", slug="no-template", is_available=True
            )

    def test_duplicate_template_raises(self):
        _structure()
        root = Page.get_first_root_node()
        root.add_child(
            instance=WidgetDetailTemplate(title="Duplicate", detail_key="widget")
        )
        with pytest.raises(DetailPageConfigurationError):
            validate_detail_pages(records=True)


class TestSignals:
    def test_connect_and_disconnect_are_idempotent(self):
        assert connect_signals() >= 2
        disconnect_signals()
        disconnect_signals()
        Widget.objects.create(name="After", slug="after", is_available=True)
        assert WidgetDetailPage.objects.filter(slug="after").count() == 0

        connect_signals()
        _structure()
        widget = Widget.objects.create(name="Back", slug="back", is_available=True)
        connect_signals()
        assert WidgetDetailPage.objects.filter(source_object_id=widget.pk).count() == 1
