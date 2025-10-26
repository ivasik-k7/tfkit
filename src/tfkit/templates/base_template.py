# templates/base_template.py
from abc import ABC, abstractmethod
from typing import Dict

from jinja2 import Template


class BaseTemplate(ABC):
    """Base class for all HTML templates."""

    @property
    @abstractmethod
    def template_string(self) -> str:
        """Return the Jinja2 template string."""
        pass

    @property
    def css_styles(self) -> Dict[str, str]:
        """Return CSS styles for the template."""
        return {}

    def create_template(self) -> Template:
        """Create and return a Jinja2 Template instance."""
        return Template(self.template_string)

    def render(self, **context) -> str:
        """Render template with given context."""
        template = self.create_template()
        return template.render(**context)
