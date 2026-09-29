# Imported so Django's model discovery (and ``makemigrations``) sees it.
from .background import (
    DaisyUIThemeBackground,
    DaisyUIThemeBackgroundLayer,
    DaisyUIThemeBackgroundLayerGradientStop,
)
from .box import DaisyUIThemeEffects, DaisyUIThemeRadii, DaisyUIThemeSizes
from .colors import DaisyUIThemeColors
from .fields import DaisyUIColorField, DaisyUIColorSchemeChoices, DaisyUISizeField
from .fonts import (
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFallback,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)
from .theme import DaisyUITheme


# Backwards-compatible aliases for the background layer models.
BackgroundLayer = DaisyUIThemeBackgroundLayer
GradientStop = DaisyUIThemeBackgroundLayerGradientStop


__all__ = [
    "BackgroundLayer",
    "DaisyUIColorField",
    "DaisyUIColorSchemeChoices",
    "DaisyUISizeField",
    "DaisyUITheme",
    "DaisyUIThemeBackground",
    "DaisyUIThemeBackgroundLayer",
    "DaisyUIThemeBackgroundLayerGradientStop",
    "DaisyUIThemeColors",
    "DaisyUIThemeEffects",
    "DaisyUIThemeFontCDN",
    "DaisyUIThemeFontFallback",
    "DaisyUIThemeFontFamily",
    "DaisyUIThemeFonts",
    "DaisyUIThemeRadii",
    "DaisyUIThemeSizes",
    "GradientStop",
]
