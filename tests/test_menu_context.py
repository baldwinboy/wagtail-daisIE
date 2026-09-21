import pytest

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import RequestFactory

from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.models import DaisyUIMenu


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
        "user": {"label": "User", "model": "auth.User", "source": "request.user"},
    }
    reset_context_models()
    yield
    reset_context_models()


def _render_menu(request):
    template = Template("{% load wagtail_daisIE_tags %}{% daisyui_menu 'Main' %}")
    return template.render(Context({"request": request}))


def test_menu_item_can_use_current_user():
    user = USER_MODEL.objects.create(username="ada")
    menu = DaisyUIMenu.objects.create(name="Main", layout="vertical")
    menu.body = [
        {
            "type": "text",
            "value": {
                "text": "Signed in as {{ user.username }}",
                "design": {},
                "audience": {},
            },
        }
    ]
    menu.save()

    request = RequestFactory().get("/")
    request.user = user

    html = _render_menu(request)
    assert "Signed in as ada" in html
