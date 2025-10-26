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
    purple: str


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
            "purple": "#6610f2",
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
            "purple": "#8b5cf6",
        },
        "cyber": {
            "bg_primary": "#000000",
            "bg_secondary": "#0d0d0d",
            "bg_tertiary": "#1a1a1a",
            "text_primary": "#00ffff",
            "text_secondary": "#00cccc",
            "border": "#00ffff",
            "accent": "#ff00ff",
            "accent_secondary": "#00ff00",
            "success": "#00ff00",
            "warning": "#ffff00",
            "danger": "#ff0000",
            "info": "#00ffff",
            "purple": "#ff00ff",
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
            "purple": "#b48ead",
        },
    }

    @classmethod
    def get_theme_colors(cls, theme: str) -> ThemeColors:
        """Get color scheme for specified theme."""
        return cls.THEMES.get(theme, cls.THEMES["light"])
