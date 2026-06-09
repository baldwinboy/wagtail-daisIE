from wagtail.admin.panels import FieldPanel

from .widgets import DaisyUIColorWidget, DaisyUISizeWidget


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
