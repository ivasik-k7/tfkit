# templates/theme_manager.py
from typing import Dict, TypedDict


class ThemeColors(TypedDict):
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    text_primary: str
    text_secondary: str
    border: str
    accent: str
    accent_secondary: str
    success: str
    warning: str
    danger: str
    info: str


class ThemeManager:
    """Manage color themes for templates."""

    THEMES: Dict[str, ThemeColors] = {
        "light": {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8f9fa",
            "bg_tertiary": "#e9ecef",
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "border": "#dee2e6",
            "accent": "#0d6efd",
            "accent_secondary": "#6610f2",
            "success": "#198754",
            "warning": "#ffc107",
            "danger": "#dc3545",
            "info": "#0dcaf0",
        },
        "dark": {
            "bg_primary": "#0a0e27",
            "bg_secondary": "#141b3d",
            "bg_tertiary": "#1a2347",
            "text_primary": "#e0e6f7",
            "text_secondary": "#a0a8c1",
            "border": "#2d3a5f",
            "accent": "#3b82f6",
            "accent_secondary": "#8b5cf6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4",
        },
        "cyber": {
            "bg_primary": "#0a0a0a",
            "bg_secondary": "#111111",
            "bg_tertiary": "#1a1a1a",
            "text_primary": "#00ff88",
            "text_secondary": "#00cc6a",
            "border": "#ff0088",
            "accent": "#00ffff",
            "accent_secondary": "#ff0088",
            "success": "#00ff88",
            "warning": "#ffff00",
            "danger": "#ff0044",
            "info": "#00ffff",
        },
        "nord": {
            "bg_primary": "#2e3440",
            "bg_secondary": "#3b4252",
            "bg_tertiary": "#434c5e",
            "text_primary": "#eceff4",
            "text_secondary": "#d8dee9",
            "border": "#4c566a",
            "accent": "#88c0d0",
            "accent_secondary": "#81a1c1",
            "success": "#a3be8c",
            "warning": "#ebcb8b",
            "danger": "#bf616a",
            "info": "#5e81ac",
        },
        "github-dark": {
            "bg_primary": "#0d1117",
            "bg_secondary": "#161b22",
            "bg_tertiary": "#21262d",
            "text_primary": "#f0f6fc",
            "text_secondary": "#8b949e",
            "border": "#30363d",
            "accent": "#58a6ff",
            "accent_secondary": "#bc8cff",
            "success": "#3fb950",
            "warning": "#d29922",
            "danger": "#f85149",
            "info": "#2f81f7",
        },
    }

    @classmethod
    def get_theme_colors(cls, theme: str) -> ThemeColors:
        """Get color scheme for specified theme."""
        return cls.THEMES.get(theme, cls.THEMES["light"])
