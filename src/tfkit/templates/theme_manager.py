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
        # --- Original Themes ---
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
        # --- First set of added themes ---
        "monokai": {
            "bg_primary": "#272822",
            "bg_secondary": "#383a36",
            "bg_tertiary": "#494a47",
            "text_primary": "#f8f8f2",
            "text_secondary": "#75715e",
            "border": "#66d9ef",
            "accent": "#f92672",
            "accent_secondary": "#ae81ff",
            "success": "#a6e22e",
            "warning": "#e6db74",
            "danger": "#f92672",
            "info": "#66d9ef",
        },
        "solarized-light": {
            "bg_primary": "#fdf6e3",
            "bg_secondary": "#eee8d5",
            "bg_tertiary": "#e5e3cb",
            "text_primary": "#586e75",
            "text_secondary": "#657b83",
            "border": "#93a1a1",
            "accent": "#268bd2",
            "accent_secondary": "#d33682",
            "success": "#859900",
            "warning": "#cb4b16",
            "danger": "#dc322f",
            "info": "#2aa198",
        },
        "dracula": {
            "bg_primary": "#282a36",
            "bg_secondary": "#383c4f",
            "bg_tertiary": "#44475a",
            "text_primary": "#f8f8f2",
            "text_secondary": "#6272a4",
            "border": "#44475a",
            "accent": "#bd93f9",
            "accent_secondary": "#ff79c6",
            "success": "#50fa7b",
            "warning": "#f1fa8c",
            "danger": "#ff5555",
            "info": "#8be9fd",
        },
        # --- Second set of added themes ---
        "atom-one-dark": {
            "bg_primary": "#282c34",
            "bg_secondary": "#3a404b",
            "bg_tertiary": "#4f5666",
            "text_primary": "#abb2bf",
            "text_secondary": "#5c6370",
            "border": "#3f4451",
            "accent": "#61afef",
            "accent_secondary": "#c678dd",
            "success": "#98c379",
            "warning": "#e5c07b",
            "danger": "#e06c75",
            "info": "#56b6c2",
        },
        "gruvbox-dark": {
            "bg_primary": "#282828",
            "bg_secondary": "#3c3836",
            "bg_tertiary": "#504945",
            "text_primary": "#ebdbb2",
            "text_secondary": "#a89984",
            "border": "#665c54",
            "accent": "#458588",
            "accent_secondary": "#b16286",
            "success": "#b8bb26",
            "warning": "#fabd2f",
            "danger": "#fb4934",
            "info": "#83a598",
        },
        "night-owl": {
            "bg_primary": "#011627",
            "bg_secondary": "#0a2133",
            "bg_tertiary": "#102a43",
            "text_primary": "#d6deeb",
            "text_secondary": "#88a2b5",
            "border": "#5f7e97",
            "accent": "#82aaff",
            "accent_secondary": "#c792ea",
            "success": "#22da6e",
            "warning": "#ffc837",
            "danger": "#ef5350",
            "info": "#00d0ff",
        },
    }

    @classmethod
    def get_theme_colors(cls, theme: str) -> ThemeColors:
        """Get color scheme for specified theme."""
        return cls.THEMES.get(theme, cls.THEMES["light"])
