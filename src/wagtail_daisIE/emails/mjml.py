"""MJML component model used by the email builder.

The tables below are transcribed from the official MJML documentation
(https://documentation.mjml.io) and drive three things:

* which components may be nested where (``MJML_PARENTS`` / ``MJML_CHILDREN``),
* which components are "ending tags" (text/HTML only, no MJML children), and
* which attributes a component accepts, so design declarations are only ever
  emitted as attributes the target component understands (``attr_map_for``).

Everything is plain data; importing this module never touches the database.
"""

#: Components that contain text/HTML only and must not contain MJML children.
ENDING_TAGS = frozenset(
    {
        "mj-accordion-text",
        "mj-accordion-title",
        "mj-button",
        "mj-carousel-image",
        "mj-navbar-link",
        "mj-raw",
        "mj-social-element",
        "mj-table",
        "mj-text",
    }
)

#: Document/head components.
HEAD_TAGS = frozenset(
    {
        "mjml",
        "mj-head",
        "mj-body",
        "mj-include",
        "mj-attributes",
        "mj-class",
        "mj-all",
        "mj-breakpoint",
        "mj-font",
        "mj-html-attributes",
        "mj-selector",
        "mj-html-attribute",
        "mj-preview",
        "mj-style",
        "mj-title",
    }
)

#: Components that may be a direct child of ``mj-body``.
BODY_LEVEL = frozenset({"mj-section", "mj-wrapper", "mj-hero", "mj-raw"})

#: Components that may be a direct child of ``mj-section``.
SECTION_LEVEL = frozenset({"mj-column", "mj-group", "mj-raw"})

#: Components that may be a direct child of ``mj-column``.
COLUMN_LEVEL = frozenset(
    {
        "mj-accordion",
        "mj-button",
        "mj-carousel",
        "mj-divider",
        "mj-image",
        "mj-navbar",
        "mj-raw",
        "mj-social",
        "mj-spacer",
        "mj-table",
        "mj-text",
    }
)

#: Every component -> the components it may contain (empty = ending/self-closing).
MJML_CHILDREN = {
    "mjml": frozenset({"mj-head", "mj-body", "mj-raw"}),
    "mj-head": frozenset(
        {
            "mj-attributes",
            "mj-breakpoint",
            "mj-font",
            "mj-html-attributes",
            "mj-preview",
            "mj-style",
            "mj-title",
            "mj-raw",
        }
    ),
    "mj-body": frozenset(
        {"mj-section", "mj-wrapper", "mj-hero", "mj-raw", "mj-include"}
    ),
    "mj-attributes": frozenset({"mj-class", "mj-all"}),
    "mj-class": frozenset(),
    "mj-all": frozenset(),
    "mj-breakpoint": frozenset(),
    "mj-font": frozenset(),
    "mj-html-attributes": frozenset({"mj-selector"}),
    "mj-selector": frozenset({"mj-html-attribute"}),
    "mj-html-attribute": frozenset(),
    "mj-preview": frozenset(),
    "mj-style": frozenset(),
    "mj-title": frozenset(),
    "mj-include": frozenset(),
    "mj-wrapper": frozenset({"mj-section", "mj-hero"}),
    "mj-section": frozenset({"mj-column", "mj-group", "mj-raw"}),
    "mj-group": frozenset({"mj-column"}),
    "mj-column": COLUMN_LEVEL,
    "mj-hero": COLUMN_LEVEL,
    "mj-accordion": frozenset({"mj-accordion-element"}),
    "mj-accordion-element": frozenset({"mj-accordion-title", "mj-accordion-text"}),
    "mj-carousel": frozenset({"mj-carousel-image"}),
    "mj-navbar": frozenset({"mj-navbar-link"}),
    "mj-social": frozenset({"mj-social-element"}),
    "mj-button": frozenset(),
    "mj-divider": frozenset(),
    "mj-image": frozenset(),
    "mj-spacer": frozenset(),
    "mj-text": frozenset(),
    "mj-table": frozenset(),
    "mj-raw": frozenset(),
    "mj-accordion-title": frozenset(),
    "mj-accordion-text": frozenset(),
    "mj-carousel-image": frozenset(),
    "mj-navbar-link": frozenset(),
    "mj-social-element": frozenset(),
}

#: Every component -> the components it may be placed in.
MJML_PARENTS = {
    "mjml": frozenset(),
    "mj-head": frozenset({"mjml"}),
    "mj-body": frozenset({"mjml"}),
    "mj-attributes": frozenset({"mj-head"}),
    "mj-class": frozenset({"mj-attributes"}),
    "mj-all": frozenset({"mj-attributes"}),
    "mj-breakpoint": frozenset({"mj-head"}),
    "mj-font": frozenset({"mj-head"}),
    "mj-html-attributes": frozenset({"mj-head"}),
    "mj-selector": frozenset({"mj-html-attributes"}),
    "mj-html-attribute": frozenset({"mj-selector"}),
    "mj-preview": frozenset({"mj-head"}),
    "mj-style": frozenset({"mj-head"}),
    "mj-title": frozenset({"mj-head"}),
    "mj-include": frozenset({"mjml", "mj-head", "mj-body"}),
    "mj-wrapper": frozenset({"mj-body"}),
    "mj-section": frozenset({"mj-body", "mj-wrapper"}),
    "mj-group": frozenset({"mj-section"}),
    "mj-column": frozenset({"mj-section", "mj-group"}),
    "mj-hero": frozenset({"mj-body", "mj-wrapper"}),
    "mj-accordion": frozenset({"mj-column"}),
    "mj-accordion-element": frozenset({"mj-accordion"}),
    "mj-accordion-title": frozenset({"mj-accordion-element"}),
    "mj-accordion-text": frozenset({"mj-accordion-element"}),
    "mj-carousel": frozenset({"mj-column"}),
    "mj-carousel-image": frozenset({"mj-carousel"}),
    "mj-navbar": frozenset({"mj-column"}),
    "mj-navbar-link": frozenset({"mj-navbar"}),
    "mj-social": frozenset({"mj-column"}),
    "mj-social-element": frozenset({"mj-social"}),
    "mj-button": frozenset({"mj-column", "mj-hero"}),
    "mj-text": frozenset({"mj-column", "mj-hero"}),
    "mj-image": frozenset({"mj-column"}),
    "mj-divider": frozenset({"mj-column"}),
    "mj-spacer": frozenset({"mj-column"}),
    "mj-table": frozenset({"mj-column"}),
    "mj-raw": frozenset(
        {"mjml", "mj-head", "mj-body", "mj-section", "mj-column", "mj-hero"}
    ),
}

# An ``mj-hero`` behaves like a section with a single column, so it accepts the
# same leaf components directly.
for _tag, _parents in list(MJML_PARENTS.items()):
    if "mj-column" in _parents:
        MJML_PARENTS[_tag] = _parents | {"mj-hero"}

#: Every component -> the attributes it accepts (documented set).
MJML_ATTRS = {
    "mjml": frozenset({"owa", "lang", "dir"}),
    "mj-head": frozenset(),
    "mj-body": frozenset({"background-color", "css-class", "id", "width"}),
    "mj-include": frozenset({"path", "type", "css-inline"}),
    "mj-attributes": frozenset(),
    "mj-class": frozenset(),
    "mj-all": frozenset(),
    "mj-html-attributes": frozenset(),
    "mj-breakpoint": frozenset({"width"}),
    "mj-font": frozenset({"href", "name"}),
    "mj-preview": frozenset(),
    "mj-style": frozenset({"inline"}),
    "mj-title": frozenset(),
    "mj-selector": frozenset({"path"}),
    "mj-html-attribute": frozenset({"name"}),
    "mj-wrapper": frozenset(
        {
            "background-color",
            "background-position",
            "background-position-x",
            "background-position-y",
            "background-repeat",
            "background-size",
            "background-url",
            "border",
            "border-bottom",
            "border-left",
            "border-radius",
            "border-right",
            "border-top",
            "css-class",
            "full-width",
            "gap",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "text-align",
        }
    ),
    "mj-section": frozenset(
        {
            "background-color",
            "background-position",
            "background-position-x",
            "background-position-y",
            "background-repeat",
            "background-size",
            "background-url",
            "border",
            "border-bottom",
            "border-left",
            "border-radius",
            "border-right",
            "border-top",
            "css-class",
            "direction",
            "full-width",
            "gutter",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "text-align",
        }
    ),
    "mj-column": frozenset(
        {
            "background-color",
            "border",
            "border-bottom",
            "border-left",
            "border-radius",
            "border-right",
            "border-top",
            "css-class",
            "direction",
            "inner-background-color",
            "inner-border",
            "inner-border-bottom",
            "inner-border-left",
            "inner-border-radius",
            "inner-border-right",
            "inner-border-top",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "vertical-align",
            "width",
        }
    ),
    "mj-group": frozenset(
        {"background-color", "css-class", "direction", "vertical-align", "width"}
    ),
    "mj-hero": frozenset(
        {
            "background-color",
            "background-height",
            "background-position",
            "background-url",
            "background-width",
            "border-radius",
            "css-class",
            "height",
            "inner-background-color",
            "inner-padding",
            "inner-padding-bottom",
            "inner-padding-left",
            "inner-padding-right",
            "inner-padding-top",
            "mode",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "vertical-align",
        }
    ),
    "mj-accordion": frozenset(
        {
            "border",
            "container-background-color",
            "css-class",
            "font-family",
            "icon-align",
            "icon-height",
            "icon-position",
            "icon-unwrapped-alt",
            "icon-unwrapped-url",
            "icon-width",
            "icon-wrapped-alt",
            "icon-wrapped-url",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
        }
    ),
    "mj-accordion-element": frozenset(
        {
            "background-color",
            "border",
            "css-class",
            "font-family",
            "icon-align",
            "icon-height",
            "icon-position",
            "icon-unwrapped-alt",
            "icon-unwrapped-url",
            "icon-width",
            "icon-wrapped-alt",
            "icon-wrapped-url",
        }
    ),
    "mj-accordion-title": frozenset(
        {
            "background-color",
            "color",
            "css-class",
            "font-family",
            "font-size",
            "font-weight",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
        }
    ),
    "mj-accordion-text": frozenset(
        {
            "background-color",
            "color",
            "css-class",
            "font-family",
            "font-size",
            "font-weight",
            "letter-spacing",
            "line-height",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
        }
    ),
    "mj-button": frozenset(
        {
            "align",
            "background-color",
            "border",
            "border-bottom",
            "border-left",
            "border-radius",
            "border-right",
            "border-top",
            "color",
            "container-background-color",
            "css-class",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "height",
            "href",
            "inner-padding",
            "letter-spacing",
            "line-height",
            "name",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "rel",
            "target",
            "text-align",
            "text-decoration",
            "text-transform",
            "title",
            "vertical-align",
            "width",
        }
    ),
    "mj-carousel": frozenset(
        {
            "align",
            "border-radius",
            "container-background-color",
            "css-class",
            "icon-width",
            "left-icon",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "right-icon",
            "tb-border",
            "tb-border-radius",
            "tb-hover-border-color",
            "tb-selected-border-color",
            "tb-width",
            "thumbnails",
        }
    ),
    "mj-carousel-image": frozenset(
        {
            "alt",
            "border-radius",
            "css-class",
            "href",
            "rel",
            "src",
            "target",
            "tb-border",
            "tb-border-radius",
            "thumbnails-src",
            "title",
        }
    ),
    "mj-divider": frozenset(
        {
            "align",
            "border-color",
            "border-style",
            "border-width",
            "container-background-color",
            "css-class",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "width",
        }
    ),
    "mj-image": frozenset(
        {
            "align",
            "alt",
            "border",
            "border-bottom",
            "border-left",
            "border-radius",
            "border-right",
            "border-top",
            "container-background-color",
            "css-class",
            "fluid-on-mobile",
            "font-size",
            "height",
            "href",
            "max-height",
            "name",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "rel",
            "sizes",
            "src",
            "srcset",
            "target",
            "title",
            "usemap",
            "width",
        }
    ),
    "mj-navbar": frozenset(
        {
            "align",
            "base-url",
            "css-class",
            "hamburger",
            "ico-align",
            "ico-close",
            "ico-color",
            "ico-font-family",
            "ico-font-size",
            "ico-line-height",
            "ico-open",
            "ico-padding",
            "ico-padding-bottom",
            "ico-padding-left",
            "ico-padding-right",
            "ico-padding-top",
            "ico-text-decoration",
            "ico-text-transform",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
        }
    ),
    "mj-navbar-link": frozenset(
        {
            "color",
            "css-class",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "href",
            "letter-spacing",
            "line-height",
            "name",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "rel",
            "target",
            "text-decoration",
            "text-transform",
        }
    ),
    "mj-raw": frozenset({"position"}),
    "mj-social": frozenset(
        {
            "align",
            "border",
            "border-radius",
            "color",
            "css-class",
            "container-background-color",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "icon-height",
            "icon-padding",
            "icon-size",
            "inner-padding",
            "line-height",
            "mode",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "text-padding",
            "text-decoration",
        }
    ),
    "mj-social-element": frozenset(
        {
            "align",
            "alt",
            "background-color",
            "border",
            "border-radius",
            "color",
            "css-class",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "href",
            "icon-height",
            "icon-padding",
            "icon-position",
            "icon-size",
            "line-height",
            "name",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "rel",
            "sizes",
            "src",
            "srcset",
            "target",
            "text-decoration",
            "text-padding",
            "title",
            "vertical-align",
        }
    ),
    "mj-spacer": frozenset(
        {
            "container-background-color",
            "css-class",
            "height",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
        }
    ),
    "mj-table": frozenset(
        {
            "align",
            "border",
            "cellpadding",
            "cellspacing",
            "color",
            "container-background-color",
            "css-class",
            "font-family",
            "font-size",
            "line-height",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "role",
            "table-layout",
            "width",
        }
    ),
    "mj-text": frozenset(
        {
            "align",
            "color",
            "container-background-color",
            "css-class",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "height",
            "letter-spacing",
            "line-height",
            "padding",
            "padding-bottom",
            "padding-left",
            "padding-right",
            "padding-top",
            "text-decoration",
            "text-transform",
        }
    ),
}

#: Design category -> the component that category's ``mj-class`` is valid on.
CATEGORY_TAGS = {
    "container": "mj-section",
    "text": "mj-text",
    "button": "mj-button",
    "media": "mj-image",
}

#: CSS declaration -> MJML attribute, for attributes whose names map 1:1.
_DIRECT_ATTRS = frozenset(
    {
        "padding",
        "padding-top",
        "padding-right",
        "padding-bottom",
        "padding-left",
        "border",
        "border-top",
        "border-right",
        "border-bottom",
        "border-left",
        "border-radius",
        "background-color",
        "font-family",
        "font-size",
        "font-weight",
        "font-style",
        "line-height",
        "letter-spacing",
        "color",
        "width",
        "height",
        "max-height",
        "vertical-align",
        "direction",
        "text-align",
        "text-decoration",
        "text-transform",
        "table-layout",
    }
)


def attr_map_for(tag):
    """Return the ``{css_property: mjml_attribute}`` mapping valid for ``tag``.

    Names that already exist on the component map directly. Otherwise the
    background colour falls back to the component's container/ inner colour,
    and ``text-align`` falls back to ``align``. The button's visual padding maps
    to ``inner-padding``.
    """
    attrs = MJML_ATTRS.get(tag, frozenset())
    mapping = {prop: prop for prop in _DIRECT_ATTRS if prop in attrs}
    if "background-color" not in attrs:
        if "container-background-color" in attrs:
            mapping["background-color"] = "container-background-color"
        elif "inner-background-color" in attrs:
            mapping["background-color"] = "inner-background-color"
    if "text-align" not in attrs and "align" in attrs:
        mapping["text-align"] = "align"
    if "padding" not in attrs and "inner-padding" in attrs:
        mapping["padding"] = "inner-padding"
    if tag == "mj-button" and "padding" in mapping:
        mapping["padding"] = "inner-padding"
    return mapping


#: Pre-computed per-component attribute maps.
ATTR_MAPS = {tag: attr_map_for(tag) for tag in MJML_ATTRS}


def can_contain(parent, child):
    """Return whether ``child`` is a valid MJML child of ``parent``."""
    return child in MJML_CHILDREN.get(parent, frozenset())


def is_ending(tag):
    """Return whether ``tag`` is an MJML ending tag (text/HTML only)."""
    return tag in ENDING_TAGS
