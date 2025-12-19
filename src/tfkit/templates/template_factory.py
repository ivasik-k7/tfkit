import importlib.resources
from pathlib import Path
from typing import Dict

from jinja2 import BaseLoader, Environment, Template, TemplateNotFound


class TemplateFactory:
    """Factory for loading and rendering Jinja2 templates."""

    TEMPLATE_FILES: Dict[str, str] = {
        "classic": "classic-template.html.j2",
        "graph": "graph-template.html.j2",
        "dashboard": "dashboard-template.html.j2",
        "3d-graph": "3d-graph-template.html.j2",
    }

    def __init__(self):
        """
        Initialize the template factory.
        Uses importlib.resources for reliable template loading in all environments.
        """
        self.template_cache = {}

    def _load_template_content(self, template_type: str) -> str:
        """Load template content using importlib.resources."""
        filename = self.TEMPLATE_FILES.get(template_type)
        if not filename:
            available = ", ".join(self.get_available_templates())
            raise ValueError(
                f"Unknown template type: '{template_type}'. Available: {available}"
            )

        try:
            template_content = (
                importlib.resources.files("tfkit.templates")
                .joinpath(filename)
                .read_text(encoding="utf-8")
            )
        except (AttributeError, FileNotFoundError):
            try:
                template_content = importlib.resources.read_text(
                    "tfkit.templates", filename, encoding="utf-8"
                )
            except Exception as e:
                raise TemplateNotFound(  # noqa: B904
                    f"Failed to load template '{filename}': {e}"
                )

        return template_content

    def get_template(self, template_type: str) -> Template:
        """
        Get a compiled Jinja2 template by type.

        Args:
            template_type: Type of template to load ('classic', 'graph', or 'dashboard')

        Returns:
            Compiled Jinja2 Template object

        Raises:
            ValueError: If template_type is not recognized
            TemplateNotFound: If template file cannot be loaded
        """
        if template_type in self.template_cache:
            return self.template_cache[template_type]

        filename = self.TEMPLATE_FILES.get(template_type)
        if not filename:
            available = ", ".join(self.get_available_templates())
            raise ValueError(
                f"Unknown template type: '{template_type}'. Available: {available}"
            )

        template_content = self._load_template_content(template_type)

        template = Environment(loader=BaseLoader()).from_string(template_content)
        self.template_cache[template_type] = template
        return template

    def render(self, template_type: str, **context) -> str:
        """
        Load and render a template with the given context.

        Args:
            template_type: Type of template to render
            **context: Context variables for template rendering

        Returns:
            Rendered HTML string

        Example:
            factory = TemplateFactory()
            html = factory.render('classic',
                                 title='My Dashboard',
                                 graph_data=data,
                                 theme_colors=colors)
        """
        template = self.get_template(template_type)
        return template.render(**context)

    def render_to_file(self, template_type: str, output_path: Path, **context) -> None:
        """
        Render a template and save to file.

        Args:
            template_type: Type of template to render
            output_path: Path where the rendered HTML should be saved
            **context: Context variables for template rendering
        """
        html = self.render(template_type, **context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    @classmethod
    def get_available_templates(cls) -> list:
        """
        Get list of all available template types.

        Returns:
            List of template type names
        """
        return sorted(cls.TEMPLATE_FILES.keys())

    @classmethod
    def register_template(cls, name: str, filename: str) -> None:
        """
        Register a new template type.

        Args:
            name: Name identifier for the template
            filename: Jinja2 template filename (e.g., 'custom.html.j2')
        """
        cls.TEMPLATE_FILES[name] = filename

    @classmethod
    def unregister_template(cls, name: str) -> None:
        """
        Unregister a template type.

        Args:
            name: Name of template to unregister
        """
        cls.TEMPLATE_FILES.pop(name, None)

    def template_exists(self, template_type: str) -> bool:
        """
        Check if a template type exists and its file is accessible.

        Args:
            template_type: Type of template to check

        Returns:
            True if template exists and file is accessible
        """
        if template_type not in self.TEMPLATE_FILES:
            return False

        try:
            self._load_template_content(template_type)
            return True
        except (TemplateNotFound, ValueError):
            return False

    def list_template_files(self) -> Dict[str, str]:
        """
        Get a mapping of template types to their filenames.

        Returns:
            Dictionary mapping template names to filenames
        """
        return self.TEMPLATE_FILES.copy()
