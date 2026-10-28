from wagtail.admin.telepath import Adapter, register

from wagtail_daisIE.widgets import DaisyUISwatchWidget


class DaisyUISwatchWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.SwatchSelect"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]

    def get_media(self, widget):
        # Base Adapter.get_media() only returns the adapter's own Media; the
        # widget's Media (swatch_controller.js) must be added explicitly, as
        # Wagtail's WidgetAdapter does for the built-in widgets.
        return super().get_media(widget) + widget.media


register(DaisyUISwatchWidgetAdapter(), DaisyUISwatchWidget)
