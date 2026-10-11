import pytest

from wagtail_daisIE.dynamic.forms import DynamicInstanceWidget
from wagtail_daisIE.dynamic.registry import reset_context_models


pytestmark = pytest.mark.django_db

CONFIG = {
    "owner": {"label": "Owner", "model": "auth.User", "source": "request.user"},
}


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = CONFIG
    reset_context_models()
    yield
    reset_context_models()


class TestDynamicInstanceWidget:
    def test_widget_context_exposes_object_id(self):
        context = DynamicInstanceWidget().get_context("binding-instance", 5, {})
        data = context["daisie_widget"]
        assert data["object_id"] == 5
        assert data["name"] == "binding-instance"
