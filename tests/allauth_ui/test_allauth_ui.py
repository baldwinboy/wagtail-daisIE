import pytest

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template, engines
from django.template.loader import render_to_string

from wagtail_daisIE.allauth_ui import (
    CONTEXT_PROCESSORS,
    register_template_dir,
    template_dir,
)


class SampleForm(forms.Form):
    name = forms.CharField(label="Name", help_text="Your name")
    bio = forms.CharField(widget=forms.Textarea, required=False)
    agree = forms.BooleanField(label="Agree", required=False)
    colour = forms.ChoiceField(choices=[("r", "Red")])
    score = forms.ChoiceField(choices=[("1", "1")], widget=forms.RadioSelect)
    upload = forms.FileField(required=False)


def _render_field(field):
    template = Template("{% load allauth_ui %}{% daisie_form_field field %}")
    return template.render(Context({"field": field}))


class TestRegisterTemplateDir:
    def test_prepends_and_injects_processors(self):
        engine = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["/existing"],
        }
        assert register_template_dir([engine]) is True
        assert engine["DIRS"][0] == template_dir()
        assert engine["DIRS"][1] == "/existing"
        # Order matters: our processors must run first, and re-registering
        # must not duplicate anything.
        assert engine["OPTIONS"]["context_processors"][
            : len(CONTEXT_PROCESSORS)
        ] == list(CONTEXT_PROCESSORS)
        assert register_template_dir([engine]) is False
        assert engine["DIRS"].count(template_dir()) == 1
        assert engine["OPTIONS"]["context_processors"].count(CONTEXT_PROCESSORS[0]) == 1

    def test_registration_is_gated_on_the_opt_in_setting(self, settings):
        import wagtail_daisIE.allauth_ui

        from wagtail_daisIE.allauth_ui.apps import AllauthUIAppConfig

        def _ready():
            AllauthUIAppConfig(
                "wagtail_daisIE.allauth_ui", wagtail_daisIE.allauth_ui
            ).ready()

        def _dirs():
            return [
                e["DIRS"]
                for e in settings.TEMPLATES
                if e["BACKEND"].endswith("DjangoTemplates")
            ][0]

        settings.TEMPLATES = [dict(t) for t in settings.TEMPLATES]
        settings.TEMPLATES[0]["DIRS"] = ["/existing"]

        settings.WAGTAIL_DAISIE_ALLAUTH_UI = False
        _ready()
        assert _dirs() == ["/existing"]

        settings.WAGTAIL_DAISIE_ALLAUTH_UI = True
        _ready()
        assert template_dir() in _dirs()


class TestFormField:
    def test_widget_classes_and_errors(self):
        form = SampleForm()
        assert "input w-full" in _render_field(form["name"])
        assert "textarea w-full" in _render_field(form["bio"])
        assert "checkbox" in _render_field(form["agree"])
        assert "select w-full" in _render_field(form["colour"])
        assert "radio" in _render_field(form["score"])
        assert "file-input w-full" in _render_field(form["upload"])

        invalid = SampleForm(data={})
        assert invalid.is_valid() is False
        html = _render_field(invalid["name"])
        assert 'aria-invalid="true"' in html
        assert 'role="alert"' in html
        assert "This field is required" in html


@pytest.fixture
def allauth_ui(settings):
    settings.WAGTAIL_DAISIE_ALLAUTH_UI = True
    engine = settings.TEMPLATES[0]
    original = list(engine.get("DIRS") or [])
    original_processors = list(
        engine.get("OPTIONS", {}).get("context_processors") or []
    )
    register_template_dir()
    engines._engines = {}
    yield
    engine["DIRS"] = original
    engine.setdefault("OPTIONS", {})["context_processors"] = original_processors
    engines._engines = {}


@pytest.mark.django_db
class TestAllauthTemplates:
    def test_base_layout_and_configured_parent(self, allauth_ui, rf, settings):
        from wagtail_daisIE.models import DaisyUITheme

        DaisyUITheme.objects.create(name="default", default=True)
        request = rf.get("/accounts/login/")
        request.user = AnonymousUser()
        html = render_to_string("test_allauth_child.html", request=request)
        assert "data-theme" in html and "template-allauth" in html
        assert "Sign In" in html and "Sign in form" in html

        settings.WAGTAIL_DAISIE_ALLAUTH_BASE_TEMPLATE = "test_project_base.html"
        html = render_to_string("test_allauth_child.html", request=request)
        assert "PROJECT-CHROME" in html
        assert "Sign In" in html and "Sign in form" in html

    def test_theme_processor_and_fields_element(self, allauth_ui, rf):
        from wagtail_daisIE.allauth_ui import context_processors
        from wagtail_daisIE.models import DaisyUITheme

        DaisyUITheme.objects.create(name="default", default=True)
        request = rf.get("/accounts/login/")
        request.resolver_match = type(
            "Match",
            (),
            {
                "view_name": "allauth.account.views.login",
                "func": type("F", (), {"__module__": "allauth.account.views"}),
            },
        )()
        assert context_processors.allauth_theme(request)["daisyui_theme"] is not None
        request.resolver_match = type(
            "Match",
            (),
            {
                "view_name": "home.views.home",
                "func": type("F", (), {"__module__": "home.views"}),
            },
        )()
        assert context_processors.allauth_theme(request) == {}

        html = render_to_string(
            "allauth/elements/fields.html",
            {"attrs": {"form": SampleForm(), "unlabeled": False}},
        )
        assert "input w-full" in html
        assert "textarea w-full" in html
        assert "select w-full" in html
