from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tfkit.templates.template_factory import TemplateFactory
from tfkit.templates.theme_manager import ThemeManager

log = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Renders interactive HTML reports for Terraform visualizations using Jinja templates.
    Provides type-safe rendering with atomic writes, theme support, and JSON resilience.
    """

    def __init__(
        self,
        default_theme: str = "dark",
        default_layout: str = "classic",
        template_factory: Optional[TemplateFactory] = None,  # noqa: UP045
    ):
        self.default_theme = default_theme
        self.default_layout = default_layout
        self._factory = template_factory or TemplateFactory()

    def render(
        self,
        output_path: Optional[Path] = None,  # noqa: UP045
        *,
        layout: Optional[str] = None,  # noqa: UP045
        theme: Optional[str] = None,  # noqa: UP045
        **context: Any,
    ) -> Path:
        """
        Render template to HTML file with atomic write semantics.

        Args:
            output_path: Target file path for the rendered HTML
            layout: Template layout name (uses default if not specified)
            theme: Color theme name (uses default if not specified)
            **context: Template context variables including:
                - title: Report title
                - project_path: Terraform project path
                - tfkit_version: Tool version info
                - config_data: Configuration data dict
                - graph_data: Visualization graph data
                - Any additional template variables

        Returns:
            Path to the successfully rendered HTML file

        Raises:
            RuntimeError: If template rendering fails
        """
        layout = layout or self.default_layout
        theme = theme or self.default_theme
        output_path = output_path or Path("terraform_report.html")

        full_context = self._build_context(theme=theme, **context)

        temp_path = output_path.with_suffix(".tmp")
        try:
            self._factory.render_to_file(layout, temp_path, **full_context)
            temp_path.replace(output_path)
            log.info("TemplateRenderer → Report rendered: %s", output_path.resolve())
            return output_path.resolve()
        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"TemplateRenderer failed: {output_path}") from e

    def _build_context(self, theme: str, **context: Any) -> Dict[str, Any]:  # noqa: UP006
        """Build complete template context with defaults and safe serialization."""
        base_context = {
            "title": context.pop("title", "Terraform Project Visualization"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "generated_at": datetime.now().isoformat(),
            "tfkit_version": context.pop("tfkit_version", "Unknown"),
            "project_path": context.pop("project_path", "."),
            "theme_name": theme,
            "theme_colors": ThemeManager.get_theme_colors(theme),
        }

        for data_key in ["config_data", "graph_data"]:
            if data_key in context:
                base_context[data_key] = self._safe_json(context.pop(data_key))

        base_context.update(context)
        return base_context

    @staticmethod
    def _safe_json(obj: Any) -> str:
        """Safely serialize objects to JSON with fallback for non-serializable types."""

        def _default(o: Any) -> str:
            return f"<non-serializable: {type(o).__name__}>"

        try:
            return json.dumps(obj, default=_default, ensure_ascii=False, indent=None)
        except Exception as e:
            log.warning("JSON serialization fallback: %s", e)
            return json.dumps({"_error": "Serialization failed"}, default=_default)
