"""Render an :class:`~wagtail_daisIE.emails.models.EmailTemplate` to concrete
subject/HTML/plain-text for a recipient and placeholder payload.

This is the single place that turns a stored template plus a context into
something an email backend can send, so bridges, allauth and campaigns all
share identical substitution and compilation behaviour.
"""

from __future__ import annotations

import html as html_module
import re

from dataclasses import dataclass, field

from mjml.mjml import mjml2html

from .context import build_context
from .placeholders import render_placeholders


_STRIP_BLOCKS_RE = re.compile(r"(?is)<(script|style|head|title)\b[^>]*>.*?</\1>")
_BREAK_RE = re.compile(r"(?i)<br\s*/?>")
_PARAGRAPH_END_RE = re.compile(r"(?i)</p>")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


@dataclass
class RenderedEmail:
    """A ready-to-send representation of an email template."""

    subject: str = ""
    html: str = ""
    text: str = ""
    from_email: str = ""
    to: list[str] = field(default_factory=list)


def html_to_text(html):
    """Return a rough plain-text fallback for an HTML email."""
    if not html:
        return ""
    text = _STRIP_BLOCKS_RE.sub(" ", html)
    text = _BREAK_RE.sub("\n", text)
    text = _PARAGRAPH_END_RE.sub("\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_module.unescape(text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def render_email_template(
    template,
    *,
    payload=None,
    recipient=None,
    request=None,
    site=None,
    from_email=None,
):
    """Render ``template`` into a :class:`RenderedEmail`.

    ``template`` is an :class:`~wagtail_daisIE.emails.models.EmailTemplate`.
    """
    context = build_context(
        request=request,
        site=site,
        recipient=recipient,
        payload=payload,
    )
    mjml_source = template.get_mjml(context=context)
    html = mjml2html(mjml_source)
    subject = render_placeholders(
        template.subject,
        context,
        escape_literals=False,
        escape_values=False,
    )
    return RenderedEmail(
        subject=subject,
        html=html,
        text=html_to_text(html),
        from_email=from_email or "",
        to=[],
    )
