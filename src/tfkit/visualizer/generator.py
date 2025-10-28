import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import _console

from tfkit.analyzer.project import TerraformProject
from tfkit.templates.template_factory import TemplateFactory
from tfkit.templates.theme_manager import ThemeManager
from tfkit.visualizer.graph_builder import GraphLayoutCalculator, TerraformGraphBuilder


class ReportGenerator:
    """
    Generates interactive HTML reports for Terraform projects,
    supporting multiple themes, layouts, and data inclusions.
    """

    def __init__(self, default_theme: str = "dark", default_layout: str = "classic"):
        """
        Initialize the report generator with default settings.

        Args:
            default_theme: Default visual theme ('light', 'dark', 'cyber', 'nord', etc.)
            default_layout: Default layout type ('classic', 'graph', 'dashboard', etc.)
        """
        self.default_theme = default_theme
        self.default_layout = default_layout
        self._graph_builder = TerraformGraphBuilder()

    def generate_analysis_report(
        self,
        project: TerraformProject,
        output_directory: Optional[Path] = None,
        **options,
    ) -> Path:
        """
        Generates a comprehensive HTML report for a Terraform project.

        Args:
            project: The analyzed Terraform project data to be reported.
            output_directory: Optional directory path to save the generated HTML file.
            **options: Optional overrides (e.g., 'theme', 'layout', 'report_title').

        Returns:
            Path to the generated HTML file.
        """
        # --- 1. Configuration Setup ---
        report_theme = options.get("theme", self.default_theme)
        report_layout = options.get("layout", self.default_layout)

        # --- 2. Data Transformation ---
        graph_data = self._graph_builder.build_graph(project)

        graph_file = "graph_data.json"
        with open(graph_file, "w") as file:
            json.dump(graph_data, file, indent=2, default=str)

        calculator = GraphLayoutCalculator()
        positions = calculator.calculate_force_layout(
            self._graph_builder.nodes,
            self._graph_builder.edges,
            width=1600,
            height=600,
        )

        # Add positions to nodes
        for node_dict in graph_data["nodes"]:
            node_id = node_dict["id"]
            if node_id in positions:
                node_dict["x"] = positions[node_id]["x"]
                node_dict["y"] = positions[node_id]["y"]

        # --- 3. Context & Rendering Setup ---
        template = TemplateFactory.create_template(report_layout)

        try:
            from tfkit import __version__
        except ImportError:
            __version__ = "Unknown"

        report_context = {
            "title": options.get("title", "Terraform Project Visualization"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tfkit_version": __version__,
            "project_path": options.get(
                "project_path",
                str(project.source_path) if hasattr(project, "source_path") else ".",
            ),
            "graph_data": json.dumps(graph_data),
            "theme_name": report_theme,
            "theme_colors": ThemeManager.get_theme_colors(report_theme),
        }

        html_content = template.render(**report_context)

        output_file_path = self._determine_output_file(output_directory)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file_path

    def _determine_output_file(self, output_directory: Optional[Path]) -> Path:
        """Determines and creates the output file path for the visualization report."""
        if output_directory:
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / "terraform_analysis_report.html"
        else:
            temp_dir = tempfile.mkdtemp()
            return Path(temp_dir) / "terraform_analysis_report_temp.html"

    def open_in_browser(self, html_file_path: Path):
        """Simple webbrowser approach that immediately returns."""
        try:
            if not html_file_path.exists():
                raise FileNotFoundError(f"HTML file not found: {html_file_path}")

            absolute_path = html_file_path.resolve()

            print("📊 Opening Terraform Graph...")
            print(f"📍 File: {absolute_path}")

            import webbrowser

            webbrowser.open(f"file://{absolute_path}")

            print("✅ Browser launched successfully")
            print("💡 The browser may show warnings - this is normal for local files")
            print(f"🔗 If needed, open manually: {absolute_path}")

            return True

        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print("📋 Manual opening required:")
            print(f"   {html_file_path.resolve()}")
            return False
