"""Advanced HTML visualization generator for Terraform projects."""

import json
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from jinja2 import Template

from tfkit.analyzer.models import TerraformProject


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
        self, project: TerraformProject, output_path: Optional[Path] = None, **options
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

        graph_data = self._build_graph_data(project_dict)

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

        if layout == "graph":
            template = self._get_graph_template()
        elif layout == "dashboard":
            template = self._get_dashboard_template()
        else:
            template = self._get_classic_template()

        html_content = template.render(
            sections=sections,
            stats=stats,
            graph_data=json.dumps(graph_data),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            theme=theme,
            theme_colors=self._get_theme_colors(theme),
            title=options.get("title", "Terraform Project Visualization"),
            include_graph=options.get("include_graph", True),
            include_metrics=options.get("include_metrics", True),
            project_path=options.get("project_path", "."),
        )

        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / "terraform_visualization.html"
        else:
            temp_dir = tempfile.mkdtemp()
            output_file = Path(temp_dir) / "terraform_visualization.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def open_in_browser(self, html_file: Path):
        """Open the generated HTML in default browser."""
        webbrowser.open(f"file://{html_file.resolve()}")

    def _build_graph_data(self, project_dict: Dict) -> Dict:
        nodes = []
        edges = []
        node_id = 0
        node_map = {}

        def add_node(label, node_type, subtype, details=None):
            nonlocal node_id
            node_data = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "subtype": subtype,
                "details": details or {},
                "dependencies_out": 0,
                "dependencies_in": 0,
            }
            nodes.append(node_data)
            node_map[label] = node_id
            node_id += 1
            return node_data

        for res_name, res_data in project_dict.get("resources", {}).items():
            res_type = res_data.get("type", "unknown")
            subtype = res_type.name if hasattr(res_type, "name") else str(res_type)
            add_node(res_name, "resource", subtype, res_data)

        for mod_name, mod_data in project_dict.get("modules", {}).items():
            add_node(mod_name, "module", "module", mod_data)

        for var_name, var_data in project_dict.get("variables", {}).items():
            add_node(var_name, "variable", "variable", var_data)

        for out_name, out_data in project_dict.get("outputs", {}).items():
            add_node(out_name, "output", "output", out_data)

        for data_name, data_data in project_dict.get("data_sources", {}).items():
            data_type = data_data.get("type", "unknown")
            subtype = data_type.name if hasattr(data_type, "name") else str(data_type)
            add_node(data_name, "data", subtype, data_data)

        for provider_name, provider_data in project_dict.get("providers", {}).items():
            add_node(provider_name, "provider", "provider", provider_data)

        def add_edge(source_name, target_name, edge_type, strength=1.0):
            if source_name in node_map and target_name in node_map:
                source_id = node_map[source_name]
                target_id = node_map[target_name]

                edges.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "type": edge_type,
                        "strength": strength,
                    }
                )

                nodes[source_id]["dependencies_out"] += 1
                nodes[target_id]["dependencies_in"] += 1
                return True
            return False

        for res_name, res_data in project_dict.get("resources", {}).items():
            if "dependencies" in res_data and isinstance(
                res_data["dependencies"], list
            ):
                for dep in res_data["dependencies"]:
                    add_edge(res_name, dep, "dependency", 1.0)

        for mod_name, mod_data in project_dict.get("modules", {}).items():
            if "dependencies" in mod_data and isinstance(
                mod_data["dependencies"], list
            ):
                for dep in mod_data["dependencies"]:
                    add_edge(mod_name, dep, "dependency", 0.8)

            if "source" in mod_data:
                add_edge(mod_name, mod_data["source"], "source", 0.6)

        for var_name, var_data in project_dict.get("variables", {}).items():
            if "references" in var_data and isinstance(var_data["references"], list):
                for ref in var_data["references"]:
                    add_edge(var_name, ref, "reference", 0.7)

        for out_name, out_data in project_dict.get("outputs", {}).items():
            if "references" in out_data and isinstance(out_data["references"], list):
                for ref in out_data["references"]:
                    add_edge(out_name, ref, "reference", 0.7)

        for data_name, data_data in project_dict.get("data_sources", {}).items():
            if "dependencies" in data_data and isinstance(
                data_data["dependencies"], list
            ):
                for dep in data_data["dependencies"]:
                    add_edge(data_name, dep, "dependency", 0.9)

        state_counts = {
            "healthy": 0,
            "unused": 0,
            "external": 0,
            "leaf": 0,
            "orphan": 0,
            "warning": 0,
        }

        for node in nodes:
            outgoing = node["dependencies_out"]
            incoming = node["dependencies_in"]
            node_type = node["type"]

            if node_type == "output":
                if incoming == 0:
                    node["state"] = "external"
                    node["state_reason"] = "Output for external consumption"
                elif outgoing == 0 and incoming > 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Output with values"
                else:
                    node["state"] = "warning"
                    node["state_reason"] = "Output with unexpected dependencies"

            elif node_type == "provider":
                if outgoing == 0 and incoming == 0:
                    node["state"] = "external"
                    node["state_reason"] = "Provider configuration"
                elif outgoing > 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Provider with resources"
                else:
                    node["state"] = "warning"
                    node["state_reason"] = "Provider without resources"

            elif node_type == "variable":
                if incoming == 0:
                    node["state"] = "unused"
                    node["state_reason"] = "Variable not referenced"
                elif outgoing == 0 and incoming > 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Variable with values"
                else:
                    node["state"] = "warning"
                    node["state_reason"] = "Variable with unexpected dependencies"

            elif node_type == "resource":
                if outgoing == 0 and incoming == 0:
                    node["state"] = "unused"
                    node["state_reason"] = "Resource not connected"
                elif outgoing > 0 and incoming > 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Resource with dependencies"
                elif outgoing == 0 and incoming > 0:
                    node["state"] = "leaf"
                    node["state_reason"] = "Leaf resource (no dependencies)"
                else:
                    node["state"] = "orphan"
                    node["state_reason"] = "Resource not used by others"

            elif node_type == "module":
                if outgoing == 0 and incoming == 0:
                    node["state"] = "unused"
                    node["state_reason"] = "Module not connected"
                elif outgoing > 0 and incoming > 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Module with dependencies"
                elif outgoing == 0 and incoming > 0:
                    node["state"] = "leaf"
                    node["state_reason"] = "Leaf module (no dependencies)"
                else:
                    node["state"] = "orphan"
                    node["state_reason"] = "Module not used by others"

            elif node_type == "data":
                if outgoing == 0 and incoming == 0:
                    node["state"] = "unused"
                    node["state_reason"] = "Data source not used"
                elif outgoing > 0 and incoming == 0:
                    node["state"] = "healthy"
                    node["state_reason"] = "Data source providing data"
                else:
                    node["state"] = "warning"
                    node["state_reason"] = "Data source with unexpected pattern"

            state_counts[node["state"]] += 1

        type_counts = {}
        for node in nodes:
            node_type = node["type"]
            if node_type not in type_counts:
                type_counts[node_type] = 0
            type_counts[node_type] += 1

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def _get_theme_colors(self, theme: str) -> Dict[str, str]:
        themes = {
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
                # Additional colors from template analysis
                "purple": "#6610f2",  # Used for modules in legend
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
                # Additional colors from template analysis
                "purple": "#8b5cf6",  # Used for modules in legend
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
                # Additional colors from template analysis
                "purple": "#ff00ff",  # Used for modules in legend
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
                # Additional colors from template analysis
                "purple": "#b48ead",  # Used for modules in legend
            },
        }

        return themes.get(theme, themes["light"])

    def _get_classic_template(self) -> Template:
        """Get clean, intuitive classic template with graph nodes and enhanced visualization."""
        return Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            {% set colors = {
                'light': {
                    'bg': '#ffffff', 'bg_alt': '#f8f9fa', 'text': '#212529', 'text_muted': '#6c757d',
                    'border': '#dee2e6', 'accent': '#0d6efd', 'success': '#198754', 'warning': '#ffc107',
                    'danger': '#dc3545', 'info': '#0dcaf0', 'purple': '#6610f2'
                },
                'dark': {
                    'bg': '#1a1d29', 'bg_alt': '#252837', 'text': '#e4e6eb', 'text_muted': '#9ca3af',
                    'border': '#3a3f52', 'accent': '#3b82f6', 'success': '#10b981', 'warning': '#f59e0b',
                    'danger': '#ef4444', 'info': '#06b6d4', 'purple': '#8b5cf6'
                },
                'cyber': {
                    'bg': '#000000', 'bg_alt': '#0a0a0a', 'text': '#00ffff', 'text_muted': '#00cccc',
                    'border': '#00ffff', 'accent': '#ff00ff', 'success': '#00ff00', 'warning': '#ffff00',
                    'danger': '#ff0000', 'info': '#00ffff', 'purple': '#ff00ff'
                },
                'nord': {
                    'bg': '#2e3440', 'bg_alt': '#3b4252', 'text': '#eceff4', 'text_muted': '#d8dee9',
                    'border': '#4c566a', 'accent': '#88c0d0', 'success': '#a3be8c', 'warning': '#ebcb8b',
                    'danger': '#bf616a', 'info': '#5e81ac', 'purple': '#b48ead'
                }
            }[theme] %}
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: {{ colors.bg }};
                color: {{ colors.text }};
                line-height: 1.6;
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: {{ colors.bg_alt }};
                padding: 24px 28px;
                border-radius: 8px;
                margin-bottom: 24px;
                border: 1px solid {{ colors.border }};
            }
            
            .header h1 {
                color: {{ colors.accent }};
                font-size: 1.75em;
                font-weight: 600;
                margin-bottom: 6px;
            }
            
            .header .meta {
                color: {{ colors.text_muted }};
                font-size: 0.875em;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: {{ colors.bg_alt }};
                padding: 20px;
                border-radius: 8px;
                border: 1px solid {{ colors.border }};
                text-align: center;
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: 700;
                color: {{ colors.accent }};
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 0.85em;
                color: {{ colors.text_muted }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 500;
            }
            
            .state-indicators {
                display: flex;
                gap: 8px;
                margin-top: 8px;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .state-indicator {
                font-size: 0.7em;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
            }
            
            .state-healthy { background: {{ colors.success }}; color: white; }
            .state-unused { background: {{ colors.danger }}; color: white; }
            .state-external { background: {{ colors.info }}; color: white; }
            .state-leaf { background: {{ colors.success }}20; color: {{ colors.success }}; border: 1px solid {{ colors.success }}; }
            .state-orphan { background: {{ colors.warning }}20; color: {{ colors.warning }}; border: 1px solid {{ colors.warning }}; }
            .state-warning { background: {{ colors.warning }}; color: {{ colors.bg }}; }
            
            .main-panel {
                background: {{ colors.bg_alt }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 24px;
            }
            
            .panel-header {
                padding: 16px 20px;
                border-bottom: 1px solid {{ colors.border }};
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }
            
            .panel-title {
                font-size: 1.125em;
                font-weight: 600;
                color: {{ colors.text }};
            }
            
            .controls {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 8px 16px;
                border: 1px solid {{ colors.border }};
                background: {{ colors.bg }};
                color: {{ colors.text }};
                border-radius: 6px;
                font-size: 0.875em;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }
            
            .btn:hover {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg }};
            }
            
            .btn.active {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg }};
            }
            
            .btn-warning {
                background: {{ colors.warning }};
                border-color: {{ colors.warning }};
                color: {{ colors.bg }};
            }
            
            .btn-warning:hover {
                background: {{ colors.danger }};
                border-color: {{ colors.danger }};
            }
            
            .search-box {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid {{ colors.border }};
                background: {{ colors.bg }};
                color: {{ colors.text }};
                border-radius: 8px;
                font-size: 0.9em;
                margin: 16px 20px;
                max-width: calc(100% - 40px);
            }
            
            .search-box:focus {
                outline: none;
                border-color: {{ colors.accent }};
                box-shadow: 0 0 0 2px {{ colors.accent }}20;
            }
            
            .search-box::placeholder {
                color: {{ colors.text_muted }};
            }
            
            .graph-container {
                padding: 20px;
                max-height: 70vh;
                overflow-y: auto;
            }
            
            .graph-container::-webkit-scrollbar {
                width: 8px;
            }
            
            .graph-container::-webkit-scrollbar-track {
                background: {{ colors.bg }};
            }
            
            .graph-container::-webkit-scrollbar-thumb {
                background: {{ colors.border }};
                border-radius: 4px;
            }
            
            .graph-container::-webkit-scrollbar-thumb:hover {
                background: {{ colors.text_muted }};
            }
            
            /* Graph Nodes Styles */
            .graph-nodes {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 16px;
            }
            
            .graph-node {
                background: {{ colors.bg }};
                border: 1px solid {{ colors.border }};
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .graph-node:hover {
                border-color: {{ colors.accent }};
                transform: translateY(-4px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            /* Node states */
            .node-unused { 
                border-left: 6px solid {{ colors.danger }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.danger }}08 100%);
            }
            
            .node-external { 
                border-left: 6px solid {{ colors.info }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.info }}08 100%);
            }
            
            .node-leaf { 
                border-left: 6px solid {{ colors.success }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.success }}08 100%);
            }
            
            .node-orphan { 
                border-left: 6px solid {{ colors.warning }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.warning }}08 100%);
            }
            
            .node-warning { 
                border-left: 6px solid {{ colors.warning }};
                background: linear-gradient(135deg, {{ colors.bg }} 0%, {{ colors.warning }}08 100%);
            }
            
            .node-healthy { 
                border-left: 6px solid {{ colors.success }};
            }
            
            .graph-node-header {
                display: flex;
                align-items: flex-start;
                margin-bottom: 12px;
                gap: 12px;
            }
            
            .graph-node-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: {{ colors.bg_alt }};
                flex-shrink: 0;
                font-size: 1.2em;
                color: {{ colors.accent }};
            }
            
            .graph-node-title-container {
                flex: 1;
                min-width: 0;
            }
            
            .graph-node-title {
                font-weight: 600;
                font-size: 1.1em;
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .graph-node-type {
                color: {{ colors.text_muted }};
                font-size: 0.85em;
                font-weight: 500;
                margin-bottom: 4px;
            }
            
            .graph-node-state {
                font-size: 0.8em;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 4px;
                display: inline-block;
            }
            
            .graph-node-badges {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-top: 8px;
            }
            
            .graph-node-badge {
                background: {{ colors.info }};
                color: white;
                font-size: 0.75em;
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: 600;
            }
            
            .graph-node-badge.warning {
                background: {{ colors.warning }};
                color: {{ colors.bg }};
            }
            
            .graph-node-badge.danger {
                background: {{ colors.danger }};
                color: white;
            }
            
            .graph-node-dependencies {
                display: flex;
                gap: 16px;
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid {{ colors.border }};
            }
            
            .graph-node-deps-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.85em;
                color: {{ colors.text_muted }};
            }
            
            .graph-node-deps-count {
                background: {{ colors.info }};
                color: white;
                border-radius: 12px;
                min-width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75em;
                font-weight: 600;
            }
            
            .graph-node-deps-count.outgoing {
                background: {{ colors.success }};
            }
            
            .graph-node-deps-count.incoming {
                background: {{ colors.purple }};
            }
            
            .graph-node-reason {
                font-size: 0.8em;
                color: {{ colors.text_muted }};
                font-style: italic;
                margin-top: 8px;
            }
            
            .empty-state {
                padding: 60px 20px;
                text-align: center;
                color: {{ colors.text_muted }};
            }
            
            .empty-state-icon {
                font-size: 3em;
                margin-bottom: 16px;
                opacity: 0.5;
            }
            
            .footer {
                margin-top: 24px;
                padding: 16px;
                text-align: center;
                color: {{ colors.text_muted }};
                font-size: 0.875em;
            }
            
            .filter-info {
                background: {{ colors.bg_alt }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }
            
            .filter-tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .filter-tag {
                background: {{ colors.accent }};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 500;
            }
            
            .legend {
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
                margin-bottom: 16px;
                padding: 12px 16px;
                background: {{ colors.bg_alt }};
                border-radius: 8px;
                border: 1px solid {{ colors.border }};
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.8em;
                color: {{ colors.text_muted }};
            }
            
            .legend-color {
                width: 12px;
                height: 12px;
                border-radius: 2px;
            }
            
            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                .controls {
                    flex-direction: column;
                    width: 100%;
                }
                .btn {
                    justify-content: center;
                }
                .graph-nodes {
                    grid-template-columns: 1fr;
                }
                .panel-header {
                    flex-direction: column;
                    align-items: stretch;
                }
                .legend {
                    flex-direction: column;
                    gap: 8px;
                }
            }
            
            @media (max-width: 480px) {
                .stats-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main-panel">
                <div class="panel-header">
                    <div class="panel-title">Infrastructure Components</div>
                    <div class="controls">
                        <button class="btn" onclick="sortNodes('name')" id="sort-name">
                            <i class="fas fa-sort-alpha-down"></i> Name
                        </button>
                        <button class="btn" onclick="sortNodes('type')" id="sort-type">
                            <i class="fas fa-layer-group"></i> Type
                        </button>
                        <button class="btn" onclick="sortNodes('dependencies')" id="sort-deps">
                            <i class="fas fa-project-diagram"></i> Dependencies
                        </button>
                        <button class="btn" onclick="filterByState('unused')" id="filter-unused">
                            <i class="fas fa-eye-slash"></i> Unused
                        </button>
                        <button class="btn" onclick="filterByState('warning')" id="filter-warning">
                            <i class="fas fa-exclamation-triangle"></i> Warnings
                        </button>
                        <button class="btn" onclick="resetFilters()">
                            <i class="fas fa-redo"></i> Reset
                        </button>
                    </div>
                </div>
                
                <div class="filter-info" id="filter-info" style="display: none;">
                    <div>
                        <strong>Active Filters:</strong>
                        <div class="filter-tags" id="filter-tags"></div>
                    </div>
                    <button class="btn" onclick="resetFilters()">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </div>
                
                <input type="text" class="search-box" placeholder="Search components by name, type, or state..." onkeyup="filterNodes(this.value)" />
                
                <div class="graph-container">
                    <div class="graph-nodes" id="graph-nodes-container"></div>
                </div>
            </div>
            
            <div class="footer">
                TFKIT • Terraform Intelligence & Analysis Suite • Theme: {{ theme }}
            </div>
        </div>
        
        <script>
            const graphData = {{ graph_data|safe }};
            let currentSort = 'name';
            let currentStateFilter = null;
            let currentSearch = '';
            
            // Font Awesome icons for different node types
            const nodeIcons = {
                'resource': 'fas fa-cube',
                'module': 'fas fa-cubes',
                'variable': 'fas fa-code',
                'output': 'fas fa-arrow-right',
                'data': 'fas fa-database',
                'provider': 'fas fa-cog'
            };
            
            // State colors and icons
            const stateConfig = {
                'healthy': { class: 'node-healthy', icon: 'fas fa-check-circle', color: '{{ colors.success }}' },
                'unused': { class: 'node-unused', icon: 'fas fa-ban', color: '{{ colors.danger }}' },
                'external': { class: 'node-external', icon: 'fas fa-external-link-alt', color: '{{ colors.info }}' },
                'leaf': { class: 'node-leaf', icon: 'fas fa-leaf', color: '{{ colors.success }}' },
                'orphan': { class: 'node-orphan', icon: 'fas fa-unlink', color: '{{ colors.warning }}' },
                'warning': { class: 'node-warning', icon: 'fas fa-exclamation-triangle', color: '{{ colors.warning }}' }
            };

            function renderGraphNodes() {
                const container = document.getElementById('graph-nodes-container');
                container.innerHTML = '';
                
                let nodesToShow = graphData.nodes.filter(node => {
                    // Filter by state if enabled
                    if (currentStateFilter && node.state !== currentStateFilter) {
                        return false;
                    }
                    
                    // Filter by search term
                    if (currentSearch) {
                        const searchTerm = currentSearch.toLowerCase();
                        const matchesName = node.label.toLowerCase().includes(searchTerm);
                        const matchesType = node.type.toLowerCase().includes(searchTerm) || 
                                        node.subtype.toLowerCase().includes(searchTerm);
                        const matchesState = node.state.toLowerCase().includes(searchTerm) ||
                                        node.state_reason.toLowerCase().includes(searchTerm);
                        return matchesName || matchesType || matchesState;
                    }
                    
                    return true;
                });
                
                // Sort nodes
                nodesToShow.sort((a, b) => {
                    switch (currentSort) {
                        case 'name':
                            return a.label.localeCompare(b.label);
                        case 'type':
                            return a.type.localeCompare(b.type) || a.subtype.localeCompare(b.subtype);
                        case 'dependencies':
                            const aDeps = a.dependencies_out + a.dependencies_in;
                            const bDeps = b.dependencies_out + b.dependencies_in;
                            return bDeps - aDeps;
                        default:
                            return 0;
                    }
                });
                
                if (nodesToShow.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon"><i class="fas fa-search"></i></div>
                            <h3>No components found</h3>
                            <p>Try adjusting your search or filter criteria</p>
                        </div>
                    `;
                    return;
                }
                
                nodesToShow.forEach(node => {
                    const nodeElement = createNodeElement(node);
                    container.appendChild(nodeElement);
                });
                
                updateFilterInfo();
            }
            
            function createNodeElement(node) {
                const nodeElement = document.createElement('div');
                const state = stateConfig[node.state] || stateConfig.healthy;
                
                nodeElement.className = `graph-node ${state.class}`;
                
                // Create badges based on node status
                const badges = [];
                if (node.dependencies_out === 0 && node.dependencies_in > 0) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-leaf"></i> LEAF</span>');
                }
                if (node.dependencies_out > 5 || node.dependencies_in > 5) {
                    badges.push('<span class="graph-node-badge"><i class="fas fa-hubspot"></i> HUB</span>');
                }
                
                nodeElement.innerHTML = `
                    <div class="graph-node-header">
                        <div class="graph-node-icon">
                            <i class="${nodeIcons[node.type] || 'fas fa-cube'}"></i>
                        </div>
                        <div class="graph-node-title-container">
                            <div class="graph-node-title" title="${node.label}">${node.label}</div>
                            <div class="graph-node-type">${node.type} • ${node.subtype}</div>
                            <span class="graph-node-state" style="background: ${state.color}; color: white;">
                                <i class="${state.icon}"></i> ${node.state.toUpperCase()}
                            </span>
                            ${badges.length > 0 ? `<div class="graph-node-badges">${badges.join('')}</div>` : ''}
                        </div>
                    </div>
                    <div class="graph-node-dependencies">
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-up"></i> Uses:</span>
                            <span class="graph-node-deps-count outgoing">${node.dependencies_out}</span>
                        </div>
                        <div class="graph-node-deps-item">
                            <span><i class="fas fa-arrow-down"></i> Used by:</span>
                            <span class="graph-node-deps-count incoming">${node.dependencies_in}</span>
                        </div>
                    </div>
                    <div class="graph-node-reason">${node.state_reason}</div>
                `;
                
                return nodeElement;
            }
            
            function sortNodes(criteria) {
                currentSort = criteria;
                
                // Update active button states
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(`sort-${criteria}`).classList.add('active');
                
                renderGraphNodes();
            }
            
            function filterByState(state) {
                currentStateFilter = currentStateFilter === state ? null : state;
                
                // Update UI
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                
                if (currentStateFilter) {
                    document.getElementById(`filter-${state}`).classList.add('active');
                }
                
                renderGraphNodes();
            }
            
            function filterNodes(query) {
                currentSearch = query;
                renderGraphNodes();
            }
            
            function resetFilters() {
                currentSearch = '';
                currentStateFilter = null;
                currentSort = 'name';
                
                // Reset UI states
                document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('sort-name').classList.add('active');
                document.querySelector('.search-box').value = '';
                
                renderGraphNodes();
            }
            
            function updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                const filterTags = document.getElementById('filter-tags');
                
                const activeFilters = [];
                
                if (currentSearch) {
                    activeFilters.push(`Search: "${currentSearch}"`);
                }
                
                if (currentStateFilter) {
                    activeFilters.push(`State: ${currentStateFilter}`);
                }
                
                if (currentSort !== 'name') {
                    activeFilters.push(`Sorted by: ${currentSort}`);
                }
                
                if (activeFilters.length > 0) {
                    filterInfo.style.display = 'flex';
                    filterTags.innerHTML = activeFilters.map(filter => 
                        `<span class="filter-tag">${filter}</span>`
                    ).join('');
                } else {
                    filterInfo.style.display = 'none';
                }
            }
            
            // Initialize
            document.getElementById('sort-name').classList.add('active');
            renderGraphNodes();
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    document.querySelector('.search-box').focus();
                } else if (e.key === 'Escape') {
                    resetFilters();
                } else if (e.key === '1' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    filterByState('unused');
                } else if (e.key === '2' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    filterByState('warning');
                }
            });
        </script>
    </body>
    </html>
    """)

    def _get_graph_template(self) -> Template:
        """Get graph-focused template with advanced visualization."""
        return Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }} - Graph View</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            {% set colors = theme_colors %}
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                background: {{ colors.bg_primary }}; 
                color: {{ colors.text_primary }}; 
                overflow: hidden; 
            }
            
            #graph-container { 
                width: 100vw; 
                height: 100vh; 
                position: relative; 
                background: {{ colors.bg_primary }};
            }

            .hud {
                position: absolute; 
                top: 20px; 
                left: 20px; 
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }}; 
                border-radius: 12px; 
                padding: 20px;
                backdrop-filter: blur(10px); 
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
                min-width: 220px;
            }

            .hud h2 {
                color: {{ colors.accent }}; 
                margin-bottom: 16px; 
                font-size: 1.1em; 
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .hud-stats {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .hud-stat { 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
                font-size: 0.85em; 
            }
            
            .hud-stat-label { 
                color: {{ colors.text_secondary }}; 
            }
            
            .hud-stat-value { 
                color: {{ colors.text_primary }}; 
                font-weight: 600;
                font-size: 1.1em;
            }
            
            .state-indicators {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 6px;
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid {{ colors.border }};
            }
            
            .state-indicator {
                font-size: 0.75em;
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: 600;
                text-align: center;
            }
            
            .state-healthy { background: {{ colors.success }}15; color: {{ colors.success }}; border: 1px solid {{ colors.success }}30; }
            .state-unused { background: {{ colors.danger }}15; color: {{ colors.danger }}; border: 1px solid {{ colors.danger }}30; }
            .state-external { background: {{ colors.info }}15; color: {{ colors.info }}; border: 1px solid {{ colors.info }}30; }
            .state-leaf { background: {{ colors.success }}15; color: {{ colors.success }}; border: 1px solid {{ colors.success }}30; }
            .state-orphan { background: {{ colors.warning }}15; color: {{ colors.warning }}; border: 1px solid {{ colors.warning }}30; }
            .state-warning { background: {{ colors.warning }}15; color: {{ colors.warning }}; border: 1px solid {{ colors.warning }}30; }
            
            .controls {
                position: absolute; 
                bottom: 20px; 
                left: 50%; 
                transform: translateX(-50%);
                background: {{ colors.bg_secondary }}; 
                border: 1px solid {{ colors.border }}; 
                border-radius: 12px;
                padding: 12px 20px; 
                display: flex; 
                gap: 8px; 
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
            }
            
            .control-btn {
                background: {{ colors.bg_primary }}; 
                border: 1px solid {{ colors.border }}; 
                color: {{ colors.text_primary }};
                padding: 8px 16px; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 0.85em;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }
            
            .control-btn:hover { 
                background: {{ colors.accent }}; 
                border-color: {{ colors.accent }}; 
                color: {{ colors.bg_primary }}; 
                transform: translateY(-1px);
            }
            
            .control-btn:active {
                transform: translateY(0);
            }
            
            .scale-controls {
                position: absolute;
                bottom: 20px;
                right: 20px;
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }};
                border-radius: 12px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
            }
            
            .scale-btn {
                background: {{ colors.bg_primary }};
                border: 1px solid {{ colors.border }};
                color: {{ colors.text_primary }};
                width: 36px;
                height: 36px;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1em;
                transition: all 0.2s ease;
            }
            
            .scale-btn:hover {
                background: {{ colors.accent }};
                border-color: {{ colors.accent }};
                color: {{ colors.bg_primary }};
                transform: translateY(-1px);
            }
            
            .legend {
                position: absolute; 
                top: 20px; 
                right: 20px; 
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }}; 
                border-radius: 12px; 
                padding: 16px; 
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                z-index: 1000;
                min-width: 180px;
            }
            
            .legend-title { 
                color: {{ colors.text_primary }}; 
                margin-bottom: 12px; 
                font-size: 0.9em; 
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .legend-item { 
                display: flex; 
                align-items: center; 
                gap: 8px; 
                margin: 6px 0; 
                font-size: 0.8em; 
            }
            
            .legend-dot { 
                width: 10px; 
                height: 10px; 
                border-radius: 50%; 
                flex-shrink: 0;
            }
            
            .node { 
                cursor: pointer; 
            }
            
            .node circle { 
                stroke-width: 2px; 
                transition: all 0.3s ease;
            }
            
            .node text { 
                font-size: 10px; 
                fill: {{ colors.text_primary }}; 
                text-shadow: 0 1px 3px {{ colors.bg_primary }};
                pointer-events: none; 
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .node:hover circle { 
                stroke-width: 3px; 
                filter: drop-shadow(0 0 8px currentColor);
            }
            
            .node:hover text {
                font-weight: 600;
            }
            
            .link { 
                stroke: {{ colors.text_secondary }}; 
                stroke-opacity: 0.3; 
                stroke-width: 1.5; 
                transition: all 0.3s ease;
            }
            
            .link-arrow { 
                fill: {{ colors.text_secondary }}; 
                opacity: 0.5; 
            }
            
            .particle { 
                fill: {{ colors.accent }}; 
                opacity: 0.8; 
            }
            
            .node-tooltip {
                position: absolute;
                background: {{ colors.bg_secondary }};
                border: 1px solid {{ colors.border }};
                border-radius: 8px;
                padding: 12px;
                font-size: 0.85em;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                z-index: 1001;
                max-width: 280px;
                backdrop-filter: blur(10px);
            }
            
            .node-info {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .node-info-title {
                font-weight: 600;
                color: {{ colors.accent }};
                margin-bottom: 4px;
                font-size: 1em;
            }
            
            .node-info-deps {
                display: flex;
                gap: 12px;
                margin-top: 6px;
                padding-top: 6px;
                border-top: 1px solid {{ colors.border }};
            }
            
            .node-info-dep {
                font-size: 0.8em;
                color: {{ colors.text_secondary }};
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .node-state {
                font-size: 0.75em;
                padding: 2px 6px;
                border-radius: 4px;
                margin-top: 4px;
                display: inline-block;
                width: fit-content;
            }
        </style>
    </head>
    <body>
        <div id="graph-container"></div>
        
        <div class="hud">
            <h2><i class="fas fa-project-diagram"></i> Dependency Graph</h2>
            <div class="hud-stats">
                <div class="hud-stat">
                    <span class="hud-stat-label">Nodes</span>
                    <span class="hud-stat-value" id="node-count">0</span>
                </div>
                <div class="hud-stat">
                    <span class="hud-stat-label">Dependencies</span>
                    <span class="hud-stat-value" id="edge-count">0</span>
                </div>
                <div class="hud-stat">
                    <span class="hud-stat-label">Groups</span>
                    <span class="hud-stat-value" id="component-count">0</span>
                </div>
            </div>
            <div class="state-indicators" id="state-indicators">
                <!-- Filled by JavaScript -->
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title"><i class="fas fa-layer-group"></i> Resource Types</div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.success }};"></div><span>Resources</span></div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.accent_secondary }};"></div><span>Modules</span></div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.warning }};"></div><span>Variables</span></div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.accent }};"></div><span>Outputs</span></div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.danger }};"></div><span>Data Sources</span></div>
            <div class="legend-item"><div class="legend-dot" style="background: {{ colors.info }};"></div><span>Providers</span></div>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="resetView()"><i class="fas fa-crosshairs"></i> Reset</button>
            <button class="control-btn" onclick="togglePhysics()" id="physics-btn"><i class="fas fa-bolt"></i> Physics</button>
            <button class="control-btn" onclick="centerGraph()"><i class="fas fa-bullseye"></i> Center</button>
            <button class="control-btn" onclick="toggleAnimations()" id="animations-btn"><i class="fas fa-sparkles"></i> Animations</button>
        </div>
        
        <div class="scale-controls">
            <button class="scale-btn" onclick="zoomIn()"><i class="fas fa-search-plus"></i></button>
            <button class="scale-btn" onclick="zoomOut()"><i class="fas fa-search-minus"></i></button>
            <button class="scale-btn" onclick="resetZoom()"><i class="fas fa-expand-arrows-alt"></i></button>
        </div>
        
        <div class="node-tooltip" id="node-tooltip"></div>
        
        <script>
            const graphData = {{ graph_data|safe }};
            let simulation, physicsEnabled = true, animationsEnabled = true;
            let currentTransform = d3.zoomIdentity;
            let hoveredNode = null;
            let highlightedNodes = new Set();
            let highlightedEdges = new Set();
            
            // Enhanced configuration
            const config = {
                physics: {
                    charge: {
                        healthy: -400,
                        unused: -150,
                        orphan: -100,
                        warning: -200,
                        external: -250,
                        leaf: -180
                    },
                    link: {
                        healthy: 120,
                        unused: 60,
                        orphan: 80,
                        warning: 100,
                        external: 140,
                        leaf: 90
                    },
                    collision: {
                        base: 8,
                        module: 12,
                        resource: 10,
                        multiplier: 0.8
                    },
                    force: {
                        center: 0.1,
                        unusedAttraction: 0.05,
                        stateGrouping: 0.02
                    }
                },
                animation: {
                    particleInterval: 200,
                    transitionDuration: 300,
                    hoverGlow: true
                }
            };
            
            const summary = {
                total_nodes: graphData.nodes.length,
                total_edges: graphData.edges.length,
                state_counts: {
                    healthy: graphData.nodes.filter(n => n.state === 'healthy').length,
                    unused: graphData.nodes.filter(n => n.state === 'unused').length,
                    external: graphData.nodes.filter(n => n.state === 'external').length,
                    leaf: graphData.nodes.filter(n => n.state === 'leaf').length,
                    orphan: graphData.nodes.filter(n => n.state === 'orphan').length,
                    warning: graphData.nodes.filter(n => n.state === 'warning').length
                }
            };
            
            // Pre-calculate node relationships for faster access
            function buildNodeGraph() {
                const nodeMap = new Map();
                const adjacencyList = new Map();
                
                graphData.nodes.forEach(node => {
                    nodeMap.set(node.id, node);
                    adjacencyList.set(node.id, { in: [], out: [] });
                });
                
                graphData.edges.forEach(edge => {
                    const sourceId = edge.source.id || edge.source;
                    const targetId = edge.target.id || edge.target;
                    
                    if (adjacencyList.has(sourceId)) {
                        adjacencyList.get(sourceId).out.push(targetId);
                    }
                    if (adjacencyList.has(targetId)) {
                        adjacencyList.get(targetId).in.push(sourceId);
                    }
                });
                
                return { nodeMap, adjacencyList };
            }
            
            const { nodeMap, adjacencyList } = buildNodeGraph();
            
            // Calculate connected components with state awareness
            function calculateConnectedComponents() {
                const visited = new Set();
                let components = 0;
                
                function dfs(nodeId) {
                    const stack = [nodeId];
                    while (stack.length) {
                        const current = stack.pop();
                        if (!visited.has(current)) {
                            visited.add(current);
                            const neighbors = [...adjacencyList.get(current).in, ...adjacencyList.get(current).out];
                            neighbors.forEach(neighbor => {
                                if (!visited.has(neighbor)) stack.push(neighbor);
                            });
                        }
                    }
                }
                
                // Start with healthy nodes first for better grouping
                const sortedNodes = [...graphData.nodes].sort((a, b) => {
                    const statePriority = { healthy: 0, external: 1, leaf: 2, warning: 3, orphan: 4, unused: 5 };
                    return (statePriority[a.state] || 6) - (statePriority[b.state] || 6);
                });
                
                sortedNodes.forEach(node => {
                    if (!visited.has(node.id)) {
                        dfs(node.id);
                        components++;
                    }
                });
                
                return components;
            }
            
            summary.connected_components = calculateConnectedComponents();
            
            document.getElementById('node-count').textContent = summary.total_nodes;
            document.getElementById('edge-count').textContent = summary.total_edges;
            document.getElementById('component-count').textContent = summary.connected_components;
            
            // Update state indicators
            const stateIndicators = document.getElementById('state-indicators');
            Object.entries(summary.state_counts).forEach(([state, count]) => {
                if (count > 0) {
                    const indicator = document.createElement('div');
                    indicator.className = `state-indicator state-${state}`;
                    indicator.textContent = `${state}: ${count}`;
                    indicator.title = `${count} ${state} nodes`;
                    indicator.onclick = () => highlightState(state);
                    indicator.style.cursor = 'pointer';
                    stateIndicators.appendChild(indicator);
                }
            });

            // Enhanced node configuration with theme colors
            const nodeConfig = {
                'resource': { color: '{{ colors.success }}', icon: 'fas fa-cube' },
                'module': { color: '{{ colors.accent_secondary }}', icon: 'fas fa-cubes' },
                'variable': { color: '{{ colors.warning }}', icon: 'fas fa-code' },
                'output': { color: '{{ colors.accent }}', icon: 'fas fa-arrow-right' },
                'data': { color: '{{ colors.danger }}', icon: 'fas fa-database' },
                'provider': { color: '{{ colors.info }}', icon: 'fas fa-cog' }
            };
            
            // Enhanced state-based styling
            const stateConfig = {
                'healthy': { 
                    stroke: '{{ colors.success }}', 
                    glow: '{{ colors.success }}40',
                    charge: config.physics.charge.healthy,
                    link: config.physics.link.healthy
                },
                'unused': { 
                    stroke: '{{ colors.danger }}', 
                    glow: '{{ colors.danger }}40',
                    charge: config.physics.charge.unused,
                    link: config.physics.link.unused
                },
                'external': { 
                    stroke: '{{ colors.info }}', 
                    glow: '{{ colors.info }}40',
                    charge: config.physics.charge.external,
                    link: config.physics.link.external
                },
                'leaf': { 
                    stroke: '{{ colors.success }}', 
                    glow: '{{ colors.success }}40',
                    charge: config.physics.charge.leaf,
                    link: config.physics.link.leaf
                },
                'orphan': { 
                    stroke: '{{ colors.warning }}', 
                    glow: '{{ colors.warning }}40',
                    charge: config.physics.charge.orphan,
                    link: config.physics.link.orphan
                },
                'warning': { 
                    stroke: '{{ colors.warning }}', 
                    glow: '{{ colors.warning }}40',
                    charge: config.physics.charge.warning,
                    link: config.physics.link.warning
                }
            };

            function init() {
                const container = document.getElementById('graph-container');
                const width = container.clientWidth, height = container.clientHeight;
                
                // Clear previous SVG
                d3.select('#graph-container svg').remove();
                
                const svg = d3.select('#graph-container').append('svg')
                    .attr('width', width)
                    .attr('height', height);

                const g = svg.append('g');
                
                // Enhanced zoom with smoother behavior
                const zoom = d3.zoom()
                    .scaleExtent([0.05, 8])
                    .wheelDelta(() => -d3.event.deltaY * (d3.event.deltaMode ? 120 : 1) / 500)
                    .on('zoom', (event) => {
                        currentTransform = event.transform;
                        g.attr('transform', event.transform);
                    });
                    
                svg.call(zoom)
                .call(zoom.transform, d3.zoomIdentity);

                // Create arrow markers
                const defs = svg.append('defs');
                Object.keys(nodeConfig).forEach(type => {
                    defs.append('marker')
                        .attr('id', `arrow-${type}`)
                        .attr('viewBox', '0 -5 10 10')
                        .attr('refX', 18)
                        .attr('refY', 0)
                        .attr('markerWidth', 8)
                        .attr('markerHeight', 8)
                        .attr('orient', 'auto')
                        .append('path')
                        .attr('d', 'M0,-5L10,0L0,5')
                        .attr('class', 'link-arrow')
                        .style('fill', nodeConfig[type].color)
                        .style('opacity', '0.7');
                });

                // Initialize enhanced force simulation
                simulation = d3.forceSimulation(graphData.nodes)
                    .force('link', d3.forceLink(graphData.edges)
                        .id(d => d.id)
                        .distance(d => {
                            const source = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
                            const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                            const sourceState = source?.state || 'healthy';
                            const targetState = target?.state || 'healthy';
                            
                            // Use the minimum link distance between connected nodes
                            return Math.min(
                                stateConfig[sourceState]?.link || config.physics.link.healthy,
                                stateConfig[targetState]?.link || config.physics.link.healthy
                            );
                        })
                        .strength(0.2)
                    )
                    .force('charge', d3.forceManyBody()
                        .strength(d => {
                            const stateStrength = stateConfig[d.state]?.charge || config.physics.charge.healthy;
                            // Adjust based on node type and dependencies
                            const dependencyFactor = 1 + ((d.dependencies_out || 0) + (d.dependencies_in || 0)) * 0.1;
                            return stateStrength * dependencyFactor;
                        })
                        .distanceMax(400)
                    )
                    .force('center', d3.forceCenter(width / 2, height / 2).strength(config.physics.force.center))
                    .force('collision', d3.forceCollide()
                        .radius(d => {
                            const baseRadius = d.type === 'module' ? config.physics.collision.module : 
                                            d.type === 'resource' ? config.physics.collision.resource : 
                                            config.physics.collision.base;
                            const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                            return baseRadius + Math.min(dependencyCount * config.physics.collision.multiplier, 8);
                        })
                        .strength(0.8)
                    )
                    .force('state_grouping', d3.forceY()
                        .strength(d => {
                            // Group similar states together vertically
                            const stateGroups = { healthy: 0, external: 0.1, leaf: -0.1, warning: 0.2, orphan: -0.2, unused: 0.3 };
                            return (stateGroups[d.state] || 0) * config.physics.force.stateGrouping;
                        })
                    )
                    .force('unused_attraction', d3.forceX()
                        .strength(d => d.state === 'unused' ? config.physics.force.unusedAttraction : 0)
                        .x(width * 0.7)
                    )
                    .alphaDecay(0.0228) // Slower decay for smoother settling
                    .velocityDecay(0.4);

                // Create links with enhanced styling
                const link = g.append('g')
                    .selectAll('line')
                    .data(graphData.edges)
                    .join('line')
                    .attr('class', 'link')
                    .attr('data-source', d => typeof d.source === 'object' ? d.source.id : d.source)
                    .attr('data-target', d => typeof d.target === 'object' ? d.target.id : d.target)
                    .attr('marker-end', d => {
                        const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                        return target ? `url(#arrow-${target.type})` : '';
                    })
                    .style('stroke-width', 1.5)
                    .style('opacity', 0.4);

                // Create nodes with enhanced interactions
                const node = g.append('g')
                    .selectAll('g')
                    .data(graphData.nodes)
                    .join('g')
                    .attr('class', d => `node ${d.type} ${d.state}`)
                    .attr('data-id', d => d.id)
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended))
                    .on('mouseover', (event, d) => showTooltip(event, d))
                    .on('mouseout', (event, d) => hideTooltip(event, d))
                    .on('click', (event, d) => highlightConnected(event, d));

                // Enhanced node circles with state-based styling
                node.append('circle')
                    .attr('r', d => {
                        const baseRadius = d.type === 'module' ? 14 : d.type === 'resource' ? 11 : 9;
                        const dependencyCount = (d.dependencies_out || 0) + (d.dependencies_in || 0);
                        return baseRadius + Math.min(dependencyCount * 0.6, 6);
                    })
                    .style('fill', d => nodeConfig[d.type]?.color || '#666')
                    .style('stroke', d => stateConfig[d.state]?.stroke || nodeConfig[d.type]?.color || '#666')
                    .style('stroke-width', 2)
                    .style('cursor', 'pointer')
                    .style('filter', d => `drop-shadow(0 0 8px ${stateConfig[d.state]?.glow || nodeConfig[d.type]?.color + '40' || '#6666'})`);

                // Enhanced labels with better positioning
                node.append('text')
                    .attr('dx', d => (d.type === 'module' ? 18 : 16))
                    .attr('dy', 4)
                    .text(d => {
                        const maxLength = d.type === 'module' ? 25 : 18;
                        return d.label.length > maxLength ? d.label.substring(0, maxLength) + '...' : d.label;
                    })
                    .style('fill', '{{ colors.text_primary }}')
                    .style('font-size', d => d.type === 'module' ? '12px' : '11px')
                    .style('font-weight', '500')
                    .style('pointer-events', 'none')
                    .style('text-shadow', `0 1px 4px {{ colors.bg_primary }}`);

                // Enhanced simulation tick for better performance
                simulation.on('tick', () => {
                    link.attr('x1', d => {
                            const source = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
                            return source?.x || 0;
                        })
                        .attr('y1', d => {
                            const source = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
                            return source?.y || 0;
                        })
                        .attr('x2', d => {
                            const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                            return target?.x || 0;
                        })
                        .attr('y2', d => {
                            const target = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
                            return target?.y || 0;
                        });
                        
                    node.attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
                });

                // Start enhanced particle animations
                if (animationsEnabled) {
                    startParticleAnimations(g);
                }
                
                // Initial stabilization
                setTimeout(() => {
                    simulation.alphaTarget(0.1).restart();
                    setTimeout(() => simulation.alphaTarget(0), 1000);
                }, 500);
            }

            function startParticleAnimations(g) {
                const particleGroup = g.append('g').attr('class', 'particles');
                
                function spawnParticle() {
                    if (!animationsEnabled || graphData.edges.length === 0) return;
                    
                    const edge = graphData.edges[Math.floor(Math.random() * graphData.edges.length)];
                    const source = typeof edge.source === 'object' ? edge.source : nodeMap.get(edge.source);
                    const target = typeof edge.target === 'object' ? edge.target : nodeMap.get(edge.target);
                    
                    if (source && target && source.x && source.y && target.x && target.y) {
                        const particle = particleGroup.append('circle')
                            .attr('class', 'particle')
                            .attr('r', 2.5)
                            .attr('cx', source.x)
                            .attr('cy', source.y)
                            .style('fill', nodeConfig[source.type]?.color || '{{ colors.accent }}')
                            .style('opacity', 0.9);
                            
                        particle.transition()
                            .duration(1200 + Math.random() * 600)
                            .ease(d3.easeCubicOut)
                            .attr('cx', target.x)
                            .attr('cy', target.y)
                            .style('opacity', 0)
                            .remove();
                    }
                }
                
                const particleInterval = setInterval(spawnParticle, config.animation.particleInterval);
                
                // Cleanup interval when animations are disabled
                window.particleInterval = particleInterval;
            }

            function showTooltip(event, d) {
                if (hoveredNode === d.id) return;
                hoveredNode = d.id;
                
                const tooltip = document.getElementById('node-tooltip');
                const config = nodeConfig[d.type] || {};
                
                tooltip.innerHTML = `
                    <div class="node-info">
                        <div class="node-info-title">
                            <i class="${config.icon}"></i> ${d.label}
                        </div>
                        <div><strong>Type:</strong> ${d.type}</div>
                        <div><strong>State:</strong> <span class="node-state state-${d.state}">${d.state}</span></div>
                        ${d.state_reason ? `<div><strong>Reason:</strong> ${d.state_reason}</div>` : ''}
                        <div class="node-info-deps">
                            <div class="node-info-dep"><i class="fas fa-arrow-up"></i> Uses: ${d.dependencies_out || 0}</div>
                            <div class="node-info-dep"><i class="fas fa-arrow-down"></i> Used by: ${d.dependencies_in || 0}</div>
                        </div>
                    </div>
                `;
                
                tooltip.style.opacity = '1';
                tooltip.style.left = (event.pageX + 15) + 'px';
                tooltip.style.top = (event.pageY - 15) + 'px';
                
                // Subtle highlight on hover
                highlightConnected(event, d, true);
            }

            function hideTooltip(event, d) {
                hoveredNode = null;
                const tooltip = document.getElementById('node-tooltip');
                tooltip.style.opacity = '0';
                
                // Clear highlight if not intentionally highlighted
                if (!highlightedNodes.size) {
                    clearHighlights();
                }
            }

            function highlightConnected(event, d, isHover = false) {
                if (!isHover) {
                    event.stopPropagation();
                }
                
                if (highlightedNodes.has(d.id) && !isHover) {
                    clearHighlights();
                    return;
                }
                
                clearHighlights();
                
                const connectedNodes = new Set([d.id]);
                const connectedEdges = new Set();
                
                // Find all connected nodes (2 levels deep)
                function findConnections(nodeId, depth = 0, maxDepth = 2) {
                    if (depth >= maxDepth) return;
                    
                    const connections = adjacencyList.get(nodeId);
                    if (!connections) return;
                    
                    [...connections.in, ...connections.out].forEach(connectedId => {
                        if (!connectedNodes.has(connectedId)) {
                            connectedNodes.add(connectedId);
                            findConnections(connectedId, depth + 1, maxDepth);
                        }
                    });
                }
                
                findConnections(d.id);
                
                // Find edges between connected nodes
                graphData.edges.forEach(edge => {
                    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
                    
                    if (connectedNodes.has(sourceId) && connectedNodes.has(targetId)) {
                        connectedEdges.add(edge);
                    }
                });
                
                // Apply highlights
                connectedNodes.forEach(nodeId => highlightedNodes.add(nodeId));
                connectedEdges.forEach(edge => highlightedEdges.add(edge));
                
                updateHighlights();
                
                if (!isHover) {
                    // Center view on highlighted node
                    const node = graphData.nodes.find(n => n.id === d.id);
                    if (node && node.x && node.y) {
                        const scale = Math.min(2, Math.max(0.5, 800 / (highlightedNodes.size * 10)));
                        const transform = d3.zoomIdentity
                            .translate(window.innerWidth / 2 - node.x * scale, window.innerHeight / 2 - node.y * scale)
                            .scale(scale);
                            
                        d3.select('#graph-container svg')
                            .transition()
                            .duration(800)
                            .call(d3.zoom().transform, transform);
                    }
                }
            }

            function highlightState(state) {
                clearHighlights();
                
                graphData.nodes.forEach(node => {
                    if (node.state === state) {
                        highlightedNodes.add(node.id);
                    }
                });
                
                updateHighlights();
            }

            function clearHighlights() {
                highlightedNodes.clear();
                highlightedEdges.clear();
                updateHighlights();
            }

            function updateHighlights() {
                // Update node opacity
                d3.selectAll('.node')
                    .transition()
                    .duration(300)
                    .style('opacity', d => highlightedNodes.size === 0 || highlightedNodes.has(d.id) ? 1 : 0.2);
                    
                // Update link opacity and style
                d3.selectAll('.link')
                    .transition()
                    .duration(300)
                    .style('opacity', d => {
                        if (highlightedNodes.size === 0) return 0.4;
                        
                        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                        const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                        
                        return highlightedNodes.has(sourceId) && highlightedNodes.has(targetId) ? 0.9 : 0.1;
                    })
                    .style('stroke-width', d => {
                        if (highlightedNodes.size === 0) return 1.5;
                        
                        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                        const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                        
                        return highlightedNodes.has(sourceId) && highlightedNodes.has(targetId) ? 2.5 : 1;
                    });
            }

            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                // Keep fixed position for better UX
                // d.fx = null;
                // d.fy = null;
            }

            function resetView() {
                const svg = d3.select('#graph-container svg');
                svg.transition()
                    .duration(750)
                    .call(d3.zoom().transform, d3.zoomIdentity);
                currentTransform = d3.zoomIdentity;
                clearHighlights();
            }

            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
                const btn = document.getElementById('physics-btn');
                if (physicsEnabled) {
                    simulation.alphaTarget(0.1).restart();
                    btn.innerHTML = '<i class="fas fa-bolt"></i> Physics';
                    btn.style.background = '{{ colors.accent }}';
                    btn.style.color = '{{ colors.bg_primary }}';
                } else {
                    simulation.stop();
                    btn.innerHTML = '<i class="fas fa-pause"></i> Paused';
                    btn.style.background = '{{ colors.warning }}';
                    btn.style.color = '{{ colors.bg_primary }}';
                }
            }

            function centerGraph() {
                const container = document.getElementById('graph-container');
                simulation.force('center', d3.forceCenter(container.clientWidth / 2, container.clientHeight / 2));
                simulation.alpha(0.5).restart();
                setTimeout(() => simulation.alphaTarget(0), 1000);
            }

            function toggleAnimations() {
                animationsEnabled = !animationsEnabled;
                const btn = document.getElementById('animations-btn');
                
                if (animationsEnabled) {
                    startParticleAnimations(d3.select('#graph-container svg g'));
                    btn.innerHTML = '<i class="fas fa-sparkles"></i> Animations';
                    btn.style.background = '{{ colors.accent }}';
                    btn.style.color = '{{ colors.bg_primary }}';
                } else {
                    if (window.particleInterval) {
                        clearInterval(window.particleInterval);
                    }
                    d3.selectAll('.particle').remove();
                    btn.innerHTML = '<i class="fas fa-ban"></i> Animations';
                    btn.style.background = '{{ colors.danger }}';
                    btn.style.color = '{{ colors.bg_primary }}';
                }
            }

            function zoomIn() {
                const svg = d3.select('#graph-container svg');
                const newScale = Math.min(currentTransform.k * 1.4, 8);
                const transform = d3.zoomIdentity.scale(newScale).translate(currentTransform.x, currentTransform.y);
                svg.transition().duration(200).call(d3.zoom().transform, transform);
            }

            function zoomOut() {
                const svg = d3.select('#graph-container svg');
                const newScale = Math.max(currentTransform.k / 1.4, 0.05);
                const transform = d3.zoomIdentity.scale(newScale).translate(currentTransform.x, currentTransform.y);
                svg.transition().duration(200).call(d3.zoom().transform, transform);
            }

            function resetZoom() {
                const svg = d3.select('#graph-container svg');
                svg.transition().duration(300).call(d3.zoom().transform, d3.zoomIdentity);
            }

            // Enhanced window resize handler
            window.addEventListener('resize', () => {
                const container = document.getElementById('graph-container');
                const svg = d3.select('#graph-container svg');
                
                svg.attr('width', container.clientWidth)
                .attr('height', container.clientHeight);
                
                simulation.force('center', d3.forceCenter(container.clientWidth / 2, container.clientHeight / 2));
                simulation.alpha(0.3).restart();
            });

            // Click anywhere to clear highlights
            document.addEventListener('click', (event) => {
                if (event.target.closest('.node, .control-btn, .scale-btn, .state-indicator, .hud, .legend')) {
                    return;
                }
                clearHighlights();
            });

            // Initialize enhanced graph
            init();
        </script>
    </body>
    </html>
    """)

    def _get_dashboard_template(self) -> Template:
        """Get modern dashboard-style template with metrics and charts."""
        return Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }} - Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            * { 
                margin: 0; 
                padding: 0; 
                box-sizing: border-box; 
            }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                background: {{ theme_colors.bg_primary }}; 
                color: {{ theme_colors.text_primary }}; 
                line-height: 1.6;
                min-height: 100vh;
            }
            
            .dashboard { 
                max-width: 1400px; 
                margin: 0 auto;
                padding: 24px;
            }
            
            /* Header */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 32px;
                padding-bottom: 20px;
                border-bottom: 1px solid {{ theme_colors.border }};
            }
            
            .header-content h1 {
                color: {{ theme_colors.text_primary }};
                font-size: 2.2em;
                font-weight: 700;
                margin-bottom: 4px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .header-content p {
                color: {{ theme_colors.text_secondary }};
                font-size: 1.1em;
            }
            
            .theme-badge {
                background: {{ theme_colors.accent }};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }
            
            /* Main Grid */
            .main-grid {
                display: grid;
                grid-template-columns: 1fr 400px;
                gap: 24px;
                margin-bottom: 32px;
            }
            
            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            
            .stat-icon {
                font-size: 2em;
                margin-bottom: 12px;
                opacity: 0.9;
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: 800;
                color: {{ theme_colors.accent }};
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .stat-label {
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Charts */
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 24px;
                margin-bottom: 32px;
            }
            
            .chart-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .chart-title {
                font-size: 1.2em;
                font-weight: 600;
                color: {{ theme_colors.text_primary }};
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .chart-container {
                height: 280px;
                position: relative;
            }
            
            /* Sidebar */
            .sidebar {
                display: flex;
                flex-direction: column;
                gap: 24px;
            }
            
            .health-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .health-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .health-title {
                font-size: 1.2em;
                font-weight: 600;
                color: {{ theme_colors.text_primary }};
            }
            
            .health-stats {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .health-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid {{ theme_colors.border }}20;
            }
            
            .health-item:last-child {
                border-bottom: none;
            }
            
            .health-label {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 500;
            }
            
            .health-value {
                font-weight: 700;
                font-size: 1.1em;
            }
            
            .health-healthy { color: {{ theme_colors.success }}; }
            .health-unused { color: {{ theme_colors.danger }}; }
            .health-external { color: {{ theme_colors.info }}; }
            .health-warning { color: {{ theme_colors.warning }}; }
            
            .type-breakdown {
                background: {{ theme_colors.bg_secondary }};
                padding: 24px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .type-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .type-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid {{ theme_colors.border }}20;
            }
            
            .type-item:last-child {
                border-bottom: none;
            }
            
            .type-name {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 500;
            }
            
            .type-count {
                font-weight: 600;
                color: {{ theme_colors.accent }};
            }
            
            /* Resource Grid */
            .resources-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
                margin-bottom: 32px;
            }
            
            .resource-card {
                background: {{ theme_colors.bg_secondary }};
                padding: 20px;
                border-radius: 12px;
                border: 1px solid {{ theme_colors.border }};
                transition: all 0.3s ease;
            }
            
            .resource-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            
            .resource-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
            }
            
            .resource-icon {
                font-size: 1.5em;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                background: {{ theme_colors.accent }}20;
                color: {{ theme_colors.accent }};
            }
            
            .resource-title {
                font-weight: 600;
                font-size: 1.1em;
            }
            
            .resource-description {
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                margin-bottom: 12px;
                line-height: 1.4;
            }
            
            .resource-stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-top: 12px;
            }
            
            .resource-stat {
                text-align: center;
                padding: 8px;
                background: {{ theme_colors.bg_primary }};
                border-radius: 8px;
                border: 1px solid {{ theme_colors.border }};
            }
            
            .resource-stat-value {
                font-size: 1.3em;
                font-weight: 700;
                color: {{ theme_colors.accent }};
            }
            
            .resource-stat-label {
                font-size: 0.8em;
                color: {{ theme_colors.text_secondary }};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Footer */
            .footer {
                text-align: center;
                color: {{ theme_colors.text_secondary }};
                font-size: 0.9em;
                padding: 24px;
                border-top: 1px solid {{ theme_colors.border }};
                margin-top: 32px;
            }
            
            /* Responsive */
            @media (max-width: 1200px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .charts-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            @media (max-width: 768px) {
                .dashboard {
                    padding: 16px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .header {
                    flex-direction: column;
                    gap: 16px;
                    text-align: center;
                }
                
                .resources-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <!-- Header -->
            <div class="header">
                <div class="header-content">
                    <h1><i class="fas fa-chart-network"></i> Infrastructure Dashboard</h1>
                    <p>{{ timestamp }} • {{ title }}</p>
                </div>
            </div>
            
            <div class="main-grid">
                <!-- Main Content -->
                <div class="main-content">
                    <!-- Resource Overview -->
                    <div class="resources-grid">
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-cube"></i>
                                </div>
                                <div class="resource-title">Resources</div>
                            </div>
                            <div class="resource-description">
                                Core infrastructure components and services
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value">{{ stats.resources }}</div>
                                    <div class="resource-stat-label">Total</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="resource-unused">0</div>
                                    <div class="resource-stat-label">Unused</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-cubes"></i>
                                </div>
                                <div class="resource-title">Modules</div>
                            </div>
                            <div class="resource-description">
                                Reusable infrastructure modules and components
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value">{{ stats.modules }}</div>
                                    <div class="resource-stat-label">Total</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="module-unused">0</div>
                                    <div class="resource-stat-label">Unused</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-project-diagram"></i>
                                </div>
                                <div class="resource-title">Dependencies</div>
                            </div>
                            <div class="resource-description">
                                Component relationships and connections
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="total-dependencies">0</div>
                                    <div class="resource-stat-label">Links</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="avg-dependencies">0</div>
                                    <div class="resource-stat-label">Avg/Node</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-icon">
                                    <i class="fas fa-shield-alt"></i>
                                </div>
                                <div class="resource-title">Health Status</div>
                            </div>
                            <div class="resource-description">
                                Infrastructure health and usage analysis
                            </div>
                            <div class="resource-stats">
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="healthy-percentage">0%</div>
                                    <div class="resource-stat-label">Healthy</div>
                                </div>
                                <div class="resource-stat">
                                    <div class="resource-stat-value" id="coverage-score">0%</div>
                                    <div class="resource-stat-label">Coverage</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Charts -->
                    <div class="charts-grid">
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-chart-pie"></i> Component Distribution
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="distributionChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-chart-bar"></i> Infrastructure Overview
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="overviewChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-heartbeat"></i> Health Distribution
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="healthChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <div class="chart-title">
                                    <i class="fas fa-project-diagram"></i> Dependency Analysis
                                </div>
                            </div>
                            <div class="chart-container">
                                <canvas id="dependencyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="health-card">
                        <div class="health-header">
                            <i class="fas fa-heartbeat" style="color: {{ theme_colors.success }};"></i>
                            <div class="health-title">Health Status</div>
                        </div>
                        <div class="health-stats">
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Healthy</span>
                                </div>
                                <div class="health-value health-healthy" id="healthy-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    <span>Unused</span>
                                </div>
                                <div class="health-value health-unused" id="unused-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-external-link-alt"></i>
                                    <span>External</span>
                                </div>
                                <div class="health-value health-external" id="external-count">0</div>
                            </div>
                            <div class="health-item">
                                <div class="health-label">
                                    <i class="fas fa-bell"></i>
                                    <span>Warnings</span>
                                </div>
                                <div class="health-value health-warning" id="warning-count">0</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="type-breakdown">
                        <div class="chart-header">
                            <div class="chart-title">
                                <i class="fas fa-layer-group"></i> Type Breakdown
                            </div>
                        </div>
                        <div class="type-list">
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cube" style="color: {{ theme_colors.success }};"></i>
                                    <span>Resources</span>
                                </div>
                                <div class="type-count">{{ stats.resources }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cubes" style="color: {{ theme_colors.accent_secondary }};"></i>
                                    <span>Modules</span>
                                </div>
                                <div class="type-count">{{ stats.modules }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-code" style="color: {{ theme_colors.warning }};"></i>
                                    <span>Variables</span>
                                </div>
                                <div class="type-count">{{ stats.variables }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-arrow-right" style="color: {{ theme_colors.info }};"></i>
                                    <span>Outputs</span>
                                </div>
                                <div class="type-count">{{ stats.outputs }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-database" style="color: {{ theme_colors.danger }};"></i>
                                    <span>Data Sources</span>
                                </div>
                                <div class="type-count">{{ stats.data_sources }}</div>
                            </div>
                            <div class="type-item">
                                <div class="type-name">
                                    <i class="fas fa-cog" style="color: {{ theme_colors.accent }};"></i>
                                    <span>Providers</span>
                                </div>
                                <div class="type-count">{{ stats.providers }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                TFKIT • Terraform Intelligence & Analysis Suite • Generated on {{ timestamp }}
            </div>
        </div>
        
        <script>
            // Component Distribution Chart
            new Chart(document.getElementById('distributionChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        data: [
                            {{ stats.resources }},
                            {{ stats.modules }}, 
                            {{ stats.variables }},
                            {{ stats.outputs }},
                            {{ stats.data_sources }},
                            {{ stats.providers }}
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.accent_secondary }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.accent }}'
                        ],
                        borderWidth: 0,
                        borderColor: '{{ theme_colors.bg_primary }}',
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '{{ theme_colors.text_primary }}',
                                padding: 20,
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
            
            // Overview Bar Chart
            new Chart(document.getElementById('overviewChart'), {
                type: 'bar',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        data: [
                            {{ stats.resources }},
                            {{ stats.modules }},
                            {{ stats.variables }},
                            {{ stats.outputs }},
                            {{ stats.data_sources }},
                            {{ stats.providers }}
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.accent_secondary }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.accent }}'
                        ],
                        borderWidth: 0,
                        borderRadius: 6,
                        borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '{{ theme_colors.border }}20' },
                            ticks: { color: '{{ theme_colors.text_secondary }}' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '{{ theme_colors.text_secondary }}' }
                        }
                    }
                }
            });
            
            // Calculate health statistics from graph data
            {% if graph_data %}
            const graphData = {{ graph_data|safe }};
            
            // Calculate state counts
            const stateCounts = {
                healthy: 0,
                unused: 0,
                external: 0,
                leaf: 0,
                orphan: 0,
                warning: 0
            };
            
            graphData.nodes.forEach(node => {
                if (stateCounts.hasOwnProperty(node.state)) {
                    stateCounts[node.state]++;
                }
            });
            
            // Calculate type-specific unused counts
            let resourceUnused = 0;
            let moduleUnused = 0;
            
            graphData.nodes.forEach(node => {
                if (node.state === 'unused') {
                    if (node.type === 'resource') resourceUnused++;
                    if (node.type === 'module') moduleUnused++;
                }
            });
            
            // Calculate dependency statistics
            const totalDependencies = graphData.edges.length;
            const avgDependencies = graphData.nodes.length > 0 
                ? (totalDependencies * 2 / graphData.nodes.length).toFixed(1) 
                : '0';
            
            // Calculate health percentages
            const totalNodes = graphData.nodes.length;
            const healthyPercentage = totalNodes > 0 
                ? Math.round((stateCounts.healthy / totalNodes) * 100) 
                : 0;
            
            const coverageScore = totalNodes > 0 
                ? Math.round(((totalNodes - stateCounts.unused) / totalNodes) * 100)
                : 0;
            
            // Update UI with calculated values
            document.getElementById('healthy-count').textContent = stateCounts.healthy;
            document.getElementById('unused-count').textContent = stateCounts.unused ;
            document.getElementById('external-count').textContent = stateCounts.external;
            document.getElementById('warning-count').textContent = stateCounts.warning;
            
            document.getElementById('resource-unused').textContent = resourceUnused;
            document.getElementById('module-unused').textContent = moduleUnused;
            document.getElementById('total-dependencies').textContent = totalDependencies;
            document.getElementById('avg-dependencies').textContent = avgDependencies;
            document.getElementById('healthy-percentage').textContent = healthyPercentage + '%';
            document.getElementById('coverage-score').textContent = coverageScore + '%';
            
            // Health Distribution Chart
            new Chart(document.getElementById('healthChart'), {
                type: 'pie',
                data: {
                    labels: ['Healthy', 'Unused', 'External', 'Leaf', 'Orphan', 'Warning'],
                    datasets: [{
                        data: [
                            stateCounts.healthy,
                            stateCounts.unused,
                            stateCounts.external,
                            stateCounts.leaf,
                            stateCounts.orphan,
                            stateCounts.warning
                        ],
                        backgroundColor: [
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.danger }}',
                            '{{ theme_colors.info }}',
                            '{{ theme_colors.success }}',
                            '{{ theme_colors.warning }}',
                            '{{ theme_colors.warning }}'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '{{ theme_colors.text_primary }}',
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
            
            // Dependency Analysis Chart
            const nodeTypes = ['resource', 'module', 'variable', 'output', 'data', 'provider'];
            const avgDependenciesByType = nodeTypes.map(type => {
                const nodesOfType = graphData.nodes.filter(n => n.type === type);
                if (nodesOfType.length === 0) return 0;
                const totalDeps = nodesOfType.reduce((sum, node) => 
                    sum + (node.dependencies_out || 0) + (node.dependencies_in || 0), 0);
                return (totalDeps / nodesOfType.length).toFixed(1);
            });
            
            new Chart(document.getElementById('dependencyChart'), {
                type: 'radar',
                data: {
                    labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                    datasets: [{
                        label: 'Avg Dependencies per Node',
                        data: avgDependenciesByType,
                        backgroundColor: '{{ theme_colors.accent }}20',
                        borderColor: '{{ theme_colors.accent }}',
                        pointBackgroundColor: '{{ theme_colors.accent }}',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '{{ theme_colors.accent }}'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            grid: { color: '{{ theme_colors.border }}20' },
                            angleLines: { color: '{{ theme_colors.border }}20' },
                            pointLabels: { color: '{{ theme_colors.text_secondary }}' },
                            ticks: { color: 'transparent', backdropColor: 'transparent' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '{{ theme_colors.text_primary }}' }
                        }
                    }
                }
            });
            {% endif %}
            
            // Set chart defaults
            Chart.defaults.color = '{{ theme_colors.text_secondary }}';
            Chart.defaults.borderColor = '{{ theme_colors.border }}20';
        </script>
    </body>
    </html>
    """)
