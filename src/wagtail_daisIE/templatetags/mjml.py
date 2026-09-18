from django import template
from mjml.mjml import mjml2html


register = template.Library()


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
