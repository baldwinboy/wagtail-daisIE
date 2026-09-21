# Imported so Django's model discovery (and ``makemigrations``) sees it.
# ``emails.models`` deliberately does not import this package at module level,
# so this does not create a cycle.
from ..dynamic.models import Feed
from ..emails.models import EmailTemplate
from ..errors.models import ErrorPage
from ..notifications.models import (
    AllauthEmailOverride,
    Audience,
    AudienceMember,
    CampaignRecipientLog,
    EmailCampaign,
)
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
from .icons import DaisyUIIconSource
from .menu import DaisyUIMenu
from .theme import DaisyUITheme


# Backwards-compatible aliases for the background layer models.
BackgroundLayer = DaisyUIThemeBackgroundLayer
GradientStop = DaisyUIThemeBackgroundLayerGradientStop


__all__ = [
    "AllauthEmailOverride",
    "Audience",
    "AudienceMember",
    "BackgroundLayer",
    "CampaignRecipientLog",
    "EmailCampaign",
    "EmailTemplate",
    "ErrorPage",
    "Feed",
    "DaisyUIColorField",
    "DaisyUIColorSchemeChoices",
    "DaisyUISizeField",
    "DaisyUIIconSource",
    "DaisyUIMenu",
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
