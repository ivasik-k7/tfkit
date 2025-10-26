# templates/template_factory.py
from typing import Dict, Type

from .base_template import BaseTemplate
from .classic_template import ClassicTemplate
from .dashboard_template import DashboardTemplate
from .graph_template import GraphTemplate


class TemplateFactory:
    """Factory for creating template instances."""

    TEMPLATE_REGISTRY: Dict[str, Type[BaseTemplate]] = {
        "classic": ClassicTemplate,
        "graph": GraphTemplate,
        "dashboard": DashboardTemplate,
    }

    @classmethod
    def create_template(cls, template_type: str) -> BaseTemplate:
        template_class = cls.TEMPLATE_REGISTRY.get(template_type)
        if not template_class:
            raise ValueError(f"Unknown template type: {template_type}")
        return template_class()

    @classmethod
    def get_available_templates(cls) -> list:
        return list(cls.TEMPLATE_REGISTRY.keys())
