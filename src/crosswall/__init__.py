"""crosswall - burn-in-safe Christian cross wallpapers."""

from crosswall.generator import STYLES, generate, luminance_ratio, oled_safe
from crosswall.presets import PRESETS, list_presets

__version__ = "0.1.0"
__all__ = [
    "PRESETS",
    "STYLES",
    "__version__",
    "generate",
    "list_presets",
    "luminance_ratio",
    "oled_safe",
]
