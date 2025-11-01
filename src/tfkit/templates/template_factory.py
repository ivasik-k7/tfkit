from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


class TemplateFactory:
    """Factory for loading and rendering Jinja2 templates."""

    TEMPLATE_FILES: Dict[str, str] = {
        "classic": "classic-template.html.j2",
        "graph": "graph-template.html.j2",
        "dashboard": "dashboard-template.html.j2",
    }

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template factory with Jinja2 environment.

        Args:
            template_dir: Directory containing template files.
                         Defaults to the directory of this file.
        """
        self.template_dir = template_dir or Path(__file__).parent
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_template(self, template_type: str) -> Template:
        """
        Get a compiled Jinja2 template by type.

        Args:
            template_type: Type of template to load ('classic', 'graph', or 'dashboard')

        Returns:
            Compiled Jinja2 Template object

        Raises:
            ValueError: If template_type is not recognized
            TemplateNotFound: If .j2 file doesn't exist
        """
        filename = self.TEMPLATE_FILES.get(template_type)
        if not filename:
            available = ", ".join(self.get_available_templates())
            raise ValueError(
                f"Unknown template type: '{template_type}'. "
                f"Available templates: {available}"
            )

        try:
            return self.jinja_env.get_template(filename)
        except TemplateNotFound:
            raise TemplateNotFound(  # noqa: B904
                f"Template file not found: {filename} in {self.template_dir}"
            )

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

        filename = self.TEMPLATE_FILES[template_type]
        template_path = self.template_dir / filename
        return template_path.exists()

    def list_template_files(self) -> Dict[str, Path]:
        """
        Get a mapping of template types to their file paths.

        Returns:
            Dictionary mapping template names to Path objects
        """
        return {
            name: self.template_dir / filename
            for name, filename in self.TEMPLATE_FILES.items()
        }
