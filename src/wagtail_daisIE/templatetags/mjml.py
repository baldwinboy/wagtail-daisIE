from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from mjml.mjml import mjml2html


register = template.Library()


@register.simple_tag
def mj_attrs(attributes=None, css_class="", mj_class=""):
    """Render MJML component attributes.

    Usage::

        <mj-text {% mj_attrs email_attributes css_class=email_css_class mj_class=email_mj_class %}>

    ``css-class`` is emitted first so ``mj-style`` rules can target the
    component, then the design-derived attributes.
    """
    parts = []
    if mj_class:
        parts.append(("mj-class", mj_class))
    if css_class:
        parts.append(("css-class", css_class))
    if attributes:
        parts.extend(attributes.items())
    return mark_safe(" ".join(f'{escape(k)}="{escape(v)}"' for k, v in parts))  # noqa: S308


class MJMLRenderNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context) -> str:
        mjml_source = self.nodelist.render(context)
        return mjml_render(mjml_source)


@register.tag
def mjml(parser, token) -> MJMLRenderNode:
    """
    Compile MJML template after render django template.

    Usage:
        {% mjml %}
            .. MJML template code ..
        {% endmjml %}
    """
    nodelist = parser.parse(("endmjml",))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) != 1:
        raise template.TemplateSyntaxError(
            f"'{tokens[0]!r}' tag doesn't receive any arguments."
        )
    return MJMLRenderNode(nodelist)


def mjml_render(mjml_source: str) -> str:
    return mjml2html(mjml_source)
