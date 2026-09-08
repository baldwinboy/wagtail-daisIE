from wagtail.admin.panels import FieldPanel

from wagtail_daisIE.widgets import (
    DaisyUIColorWidget,
    DaisyUISizeWidget,
    DaisyUIThemeColorWidget,
)


class DaisyUISizePanel(FieldPanel):
    def get_form_options(self):
        opts = super().get_form_options()
        opts["widgets"] = {
            self.field_name: DaisyUISizeWidget(),
        }
        return opts


class DaisyUIColorPanel(FieldPanel):
    def get_form_options(self):
        opts = super().get_form_options()
        opts["widgets"] = {
            self.field_name: DaisyUIColorWidget(),
        }
        return opts


class DaisyUIThemeColorPanel(FieldPanel):
    def get_form_options(self):
        opts = super().get_form_options()
        opts["widgets"] = {
            self.field_name: DaisyUIThemeColorWidget(),
        }
        return opts


class LayerColorPanel(FieldPanel):
    """Colour picker for BackgroundLayer."""

    def get_form_options(self):
        opts = super().get_form_options()
        opts["widgets"] = {
            self.field_name: DaisyUIThemeColorWidget(),
        }
        return opts


class GradientStopColorPanel(FieldPanel):
    """Colour picker for GradientStop."""

    def get_form_options(self):
        opts = super().get_form_options()
        opts["widgets"] = {
            self.field_name: DaisyUIThemeColorWidget(),
        }
        return opts
