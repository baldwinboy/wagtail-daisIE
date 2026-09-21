import pytest

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template, engines
from django.template.loader import render_to_string

from wagtail_daisIE.allauth_ui import register_template_dir, template_dir


class SampleForm(forms.Form):
    name = forms.CharField(label="Name", help_text="Your name")
    bio = forms.CharField(widget=forms.Textarea, required=False)
    agree = forms.BooleanField(label="Agree", required=False)
    colour = forms.ChoiceField(choices=[("r", "Red")])
    tags = forms.MultipleChoiceField(
        choices=[("a", "A")], widget=forms.CheckboxSelectMultiple, required=False
    )
    score = forms.ChoiceField(choices=[("1", "1")], widget=forms.RadioSelect)
    upload = forms.FileField(required=False)


def _render_field(field):
    template = Template("{% load allauth_ui %}{% daisie_form_field field %}")
    return template.render(Context({"field": field}))


class TestRegisterTemplateDir:
    def test_prepends_and_is_idempotent(self):
        engine = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["/existing"],
        }
        assert register_template_dir([engine]) is True
        assert engine["DIRS"][0] == template_dir()
        assert engine["DIRS"][1] == "/existing"
        assert register_template_dir([engine]) is False
        assert engine["DIRS"].count(template_dir()) == 1

    def test_ignores_other_backends(self):
        engine = {"BACKEND": "django.template.backends.jinja2.Jinja2", "DIRS": []}
        assert register_template_dir([engine]) is False


class TestFormField:
    def test_widget_classes(self):
        form = SampleForm()
        assert "input w-full" in _render_field(form["name"])
        assert "textarea w-full" in _render_field(form["bio"])
        assert "checkbox" in _render_field(form["agree"])
        assert "select w-full" in _render_field(form["colour"])
        assert "radio" in _render_field(form["score"])
        assert "file-input w-full" in _render_field(form["upload"])

    def test_error_state_is_accessible(self):
        form = SampleForm(data={})
        assert form.is_valid() is False
        html = _render_field(form["name"])
        assert 'aria-invalid="true"' in html
        assert 'role="alert"' in html
        assert "This field is required" in html

    def test_checkbox_markup(self):
        form = SampleForm()
        html = _render_field(form["agree"])
        assert 'type="checkbox"' in html
        assert "label-text" in html


@pytest.fixture
def allauth_ui(settings):
    settings.WAGTAIL_DAISIE_ALLAUTH_UI = True
    engine = settings.TEMPLATES[0]
    original = list(engine.get("DIRS") or [])
    register_template_dir()
    engines._engines = {}
    yield
    engine["DIRS"] = original
    engines._engines = {}


@pytest.mark.django_db
class TestAllauthTemplates:
    def test_base_layout_uses_daisyui(self, allauth_ui, rf):
        from wagtail_daisIE.models import DaisyUITheme

        DaisyUITheme.objects.create(name="default", default=True)
        request = rf.get("/accounts/login/")
        request.user = AnonymousUser()
        html = render_to_string(
            "allauth/layouts/base.html",
            {"head_title": "Sign In", "request": request},
        )
        assert "data-theme" in html
        assert "navbar" in html
        assert "card" in html

    def test_fields_element_renders_daisyui_fields(self, allauth_ui):
        html = render_to_string(
            "allauth/elements/fields.html",
            {"attrs": {"form": SampleForm(), "unlabeled": False}},
        )
        assert "input w-full" in html
        assert "textarea w-full" in html
        assert "select w-full" in html
