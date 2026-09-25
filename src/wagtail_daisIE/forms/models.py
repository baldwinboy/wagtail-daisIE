"""Form pages that can create a model instance from a submission."""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractForm
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.fields import StreamField

from ..base_blocks.button import ButtonAppearanceBlock
from ..base_blocks.css import build_design_css
from ..blocks.content import ContentBlock
from ..dynamic.registry import get_context_model, get_context_model_choices
from ..pages import StyledPageMixin
from .blocks import FormContentBlock, duplicate_field_names, placed_field_names
from .builder import DaisyUIFormBuilder
from .panels import FormModelFieldsHelpPanel


logger = logging.getLogger(__name__)


class DaisieFormPage(StyledPageMixin, AbstractForm):
    """A DaisyUI-styled form that links inputs to a configured model.

    Concrete subclasses must define a ``form_fields`` relation whose field model
    derives from :class:`wagtail_daisIE.forms.fields.DaisieFormField`.
    """

    form_builder = DaisyUIFormBuilder

    #: ``id`` of the single ``<form>`` element in the page template. Inputs
    #: rendered outside it (via the ``form_field`` body block) point back at it
    #: with the HTML ``form`` attribute.
    form_id = "daisie-form"

    body = StreamField(
        FormContentBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Body"),
        help_text=_(
            "Add content blocks and place the form's fields in any order. Fields "
            "that are not placed here are shown above the submit button."
        ),
    )

    instance_model = models.CharField(
        max_length=64,
        blank=True,
        choices=get_context_model_choices,
        verbose_name=_("Model to create"),
        help_text=_(
            "Optionally create an instance of a configured context model when "
            "the form is submitted."
        ),
    )
    require_approval = models.BooleanField(
        default=True,
        verbose_name=_("Require approval"),
        help_text=_(
            "Create the instance in an unapproved state so it can be reviewed."
        ),
    )
    approval_field = models.CharField(
        max_length=64,
        blank=True,
        default="is_approved",
        verbose_name=_("Approval field"),
        help_text=_("Boolean model field set to false when approval is required."),
    )
    submit_label = models.CharField(
        max_length=64,
        blank=True,
        default="Submit",
        verbose_name=_("Submit button label"),
    )
    success_body = StreamField(
        ContentBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Success body"),
        help_text=_("Shown after a successful submission (unless a redirect is set)."),
    )
    error_body = StreamField(
        ContentBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Error body"),
        help_text=_("Shown when a submission has validation errors."),
    )
    success_redirect_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Success redirect"),
        help_text=_("Redirect here after a successful submission instead of the body."),
    )
    submit_appearance = StreamField(
        [("appearance", ButtonAppearanceBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Submit button"),
    )

    class Meta:
        abstract = True

    content_panels = [
        *StyledPageMixin.content_panels,
        MultiFieldPanel(
            [
                FieldPanel("instance_model"),
                FieldPanel("require_approval"),
                FieldPanel("approval_field"),
            ],
            heading=_("Model instance"),
            classname="collapsed",
        ),
        FormModelFieldsHelpPanel(),
        MultiFieldPanel(
            [
                FieldPanel("submit_label"),
                FieldPanel("submit_appearance"),
                FieldPanel("success_body"),
                FieldPanel("error_body"),
                FieldPanel("success_redirect_page"),
            ],
            heading=_("Messages"),
            classname="collapsed",
        ),
        InlinePanel("form_fields", label=_("Form fields")),
        FormSubmissionsPanel(),
    ]

    def get_template(self, request, *args, **kwargs):
        return "wagtail_daisIE/forms/form_page.html"

    def get_landing_page_template(self, *args, **kwargs):
        return "wagtail_daisIE/forms/form_page_landing.html"

    def get_submit_css(self):
        value = self.submit_appearance[0].value if self.submit_appearance else None
        return build_design_css({"button_appearance": value}) or "btn"

    def get_placed_field_names(self):
        """Return the clean names of form fields placed in ``body``, in order."""
        return placed_field_names(self.body)

    def clean(self):
        super().clean()
        duplicates = duplicate_field_names(self.body)
        if duplicates:
            raise ValidationError(
                {
                    "body": _("These form fields are placed more than once: %(names)s")
                    % {"names": ", ".join(duplicates)}
                }
            )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        for field in form.fields.values():
            widget = getattr(field, "widget", None)
            if widget is None:
                continue
            for target in [widget, *getattr(widget, "widgets", ())]:
                attrs = getattr(target, "attrs", None)
                if attrs is not None:
                    attrs.setdefault("form", self.form_id)
        return form

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        context = self.get_context(request)
        context["form_submission"] = form_submission
        payload = dict(context.get("payload") or {})
        payload["submission"] = (
            form_submission.form_data if form_submission is not None else {}
        )
        context["payload"] = payload
        return TemplateResponse(
            request, self.get_landing_page_template(request), context
        )

    def get_model_field_map(self):
        """Return ``{clean_name: model_field}`` for the form's fields."""
        mapping = {}
        for field in self.get_form_fields():
            name = field.clean_name
            target = (getattr(field, "model_field", "") or "").strip() or name
            mapping[name] = target
        return mapping

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        self.create_instance_from_submission(form, submission)
        return submission

    def create_instance_from_submission(self, form, submission=None):
        """Create and save an instance of ``instance_model`` from ``form``."""
        if not self.instance_model:
            return None

        config = get_context_model(self.instance_model)
        model = config.model if config is not None else None
        if model is None:
            logger.warning(
                "Form page %s references unknown model %r",
                getattr(self, "pk", None),
                self.instance_model,
            )
            return None

        mapping = self.get_model_field_map()
        kwargs = {}
        for name, value in form.cleaned_data.items():
            target = mapping.get(name, name)
            try:
                model._meta.get_field(target)
            except Exception:
                logger.debug(
                    "Skipping unknown field %r on %s", target, model._meta.label
                )
                continue
            kwargs[target] = value

        if self.require_approval:
            approval_field = self.approval_field or "is_approved"
            try:
                model._meta.get_field(approval_field)
            except Exception:
                logger.warning(
                    "Approval field %r does not exist on %s",
                    approval_field,
                    model._meta.label,
                )
            else:
                kwargs[approval_field] = False

        try:
            instance = model(**kwargs)
            instance.save()
        except Exception:
            logger.exception("Failed to create %s from form submission", model)
            return None

        return instance

    def serve(self, request, *args, **kwargs):
        if not self.page_audience_allowed(request):
            return self.audience_denied_response(request)

        if request.method == "POST":
            form = self.get_form(
                request.POST, request.FILES, page=self, user=request.user
            )
            if form.is_valid():
                submission = self.process_form_submission(form)
                if self.success_redirect_page_id:
                    return redirect(self.success_redirect_page.url)
                return self.render_landing_page(request, submission, *args, **kwargs)

            context = self.get_context(request)
            context["form"] = form
            context["form_has_errors"] = True
            return TemplateResponse(request, self.get_template(request), context)

        return super().serve(request, *args, **kwargs)
