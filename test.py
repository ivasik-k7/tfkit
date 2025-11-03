import sys

sys.path.insert(0, "src")
from tfkit.templates.template_factory import TemplateFactory

factory = TemplateFactory()
print(f"Available templates: {factory.get_available_templates()}")
print(f"Classic template exists: {factory.template_exists('classic')}")
