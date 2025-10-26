"""Advanced HTML visualization generator for Terraform projects."""

import json
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from tfkit.analyzer.models import TerraformProject
from tfkit.templates.template_factory import TemplateFactory
from tfkit.templates.theme_manager import ThemeManager
from tfkit.visualizer.graph_builder import TerraformGraphBuilder


class HTMLVisualizer:
    """Generate interactive HTML visualizations with multiple themes and layouts."""

    def __init__(self, theme: str = "dark", layout: str = "classic"):
        """
        Initialize visualizer.

        Args:
            theme: Visual theme ('light', 'dark', 'cyber', 'nord')
            layout: Layout type ('classic', 'graph', 'dashboard')
        """
        self.theme = theme
        self.layout = layout

    def generate_visualization(
        self,
        project: TerraformProject,
        output_path: Optional[Path] = None,
        **options,
    ) -> Path:
        """
        Generate HTML visualization for Terraform project.

        Args:
            project: Terraform project to visualize
            output_path: Output directory path
            **options: Additional options (title, include_graph, include_metrics, etc.)

        Returns:
            Path to generated HTML file
        """
        theme = options.get("theme", self.theme)
        layout = options.get("layout", self.layout)

        project_dict = json.loads(json.dumps(project.to_dict(), default=str))

        graph_data = TerraformGraphBuilder().build_graph(project_dict)

        sections = {
            "resources": list(project_dict["resources"].values()),
            "data_sources": list(project_dict["data_sources"].values()),
            "modules": list(project_dict["modules"].values()),
            "variables": list(project_dict["variables"].values()),
            "outputs": list(project_dict["outputs"].values()),
            "providers": list(project_dict["providers"].values()),
        }

        stats = {
            "resources": len(project_dict["resources"]),
            "data_sources": len(project_dict["data_sources"]),
            "modules": len(project_dict["modules"]),
            "variables": len(project_dict["variables"]),
            "outputs": len(project_dict["outputs"]),
            "providers": len(project_dict["providers"]),
            "total": sum(
                [
                    len(project_dict["resources"]),
                    len(project_dict["data_sources"]),
                    len(project_dict["modules"]),
                    len(project_dict["variables"]),
                    len(project_dict["outputs"]),
                    len(project_dict["providers"]),
                ]
            ),
        }

        template = TemplateFactory.create_template(layout)

        context = {
            "sections": sections,
            "stats": stats,
            "graph_data": json.dumps(graph_data),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "theme": theme,
            "theme_colors": ThemeManager.get_theme_colors(theme),
            "title": options.get("title", "Terraform Project Visualization"),
            "include_graph": options.get("include_graph", True),
            "include_metrics": options.get("include_metrics", True),
            "project_path": options.get("project_path", "."),
        }

        html_content = template.render(**context)

        output_file = self._get_output_file(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def _get_output_file(self, output_path: Optional[Path]) -> Path:
        """Determine output file path."""
        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            return output_path / "terraform_visualization.html"
        else:
            temp_dir = tempfile.mkdtemp()
            return Path(temp_dir) / "terraform_visualization.html"

    def open_in_browser(self, html_file: Path):
        """Open the generated HTML in default browser."""
        webbrowser.open(f"file://{html_file.resolve()}")
