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

    def __init__(self, theme: str = "dark", layout: str = "interactive"):
        """
        Initialize visualizer.

        Args:
            theme: Visual theme ('light', 'dark', 'cyberpunk', 'minimal')
            layout: Layout type ('interactive', 'classic', 'graph', 'dashboard')
        """
        self.theme = theme
        self.layout = layout
        self.templates = {
            "interactive": self._get_interactive_template(),
            "classic": self._get_classic_template(),
            "graph": self._get_graph_template(),
            "dashboard": self._get_dashboard_template(),
        }

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
        # Override theme/layout from options
        theme = options.get("theme", self.theme)
        layout = options.get("layout", self.layout)

        # Prepare data - convert to dict with str conversion for enums
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

        # Get template
        template = self.templates.get(layout, self.templates["interactive"])

        # Render HTML
        html_content = template.render(
            sections=sections,
            stats=stats,
            graph_data=json.dumps(graph_data),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            theme=theme,
            title=options.get("title", "Terraform Project Visualization"),
            include_graph=options.get("include_graph", True),
            include_metrics=options.get("include_metrics", True),
            project_path=options.get("project_path", "."),
        )

        # Determine output file
        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / "terraform_visualization.html"
        else:
            temp_dir = tempfile.mkdtemp()
            output_file = Path(temp_dir) / "terraform_visualization.html"

        # Write file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def open_in_browser(self, html_file: Path):
        """Open the generated HTML in default browser."""
        webbrowser.open(f"file://{html_file.resolve()}")

    def _build_graph_data(self, project_dict: Dict) -> Dict:
        """Build graph data structure for visualization."""
        nodes = []
        edges = []
        node_id = 0
        node_map = {}

        # Add resources as nodes
        for res_name, res_data in project_dict["resources"].items():
            nodes.append(
                {
                    "id": node_id,
                    "label": res_name,
                    "type": "resource",
                    "subtype": res_data.get("type", "unknown"),
                    "group": 1,
                }
            )
            node_map[res_name] = node_id
            node_id += 1

        # Add modules as nodes
        for mod_name, mod_data in project_dict["modules"].items():
            nodes.append(
                {
                    "id": node_id,
                    "label": mod_name,
                    "type": "module",
                    "subtype": "module",
                    "group": 2,
                }
            )
            node_map[mod_name] = node_id
            node_id += 1

        # Add variables as nodes
        for var_name in project_dict["variables"].keys():
            nodes.append(
                {
                    "id": node_id,
                    "label": var_name,
                    "type": "variable",
                    "subtype": "variable",
                    "group": 3,
                }
            )
            node_map[var_name] = node_id
            node_id += 1

        # Add outputs as nodes
        for out_name in project_dict["outputs"].keys():
            nodes.append(
                {
                    "id": node_id,
                    "label": out_name,
                    "type": "output",
                    "subtype": "output",
                    "group": 4,
                }
            )
            node_map[out_name] = node_id
            node_id += 1

        # Add data sources as nodes
        for data_name, data_data in project_dict["data_sources"].items():
            nodes.append(
                {
                    "id": node_id,
                    "label": data_name,
                    "type": "data",
                    "subtype": data_data.get("type", "unknown"),
                    "group": 5,
                }
            )
            node_map[data_name] = node_id
            node_id += 1

        # Build edges from dependencies
        for res_name, res_data in project_dict["resources"].items():
            if res_name in node_map and "dependencies" in res_data:
                deps = res_data["dependencies"]
                if isinstance(deps, list):
                    for dep in deps:
                        if dep in node_map:
                            edges.append(
                                {
                                    "source": node_map[res_name],
                                    "target": node_map[dep],
                                    "type": "dependency",
                                }
                            )

        return {"nodes": nodes, "edges": edges}

    def _get_interactive_template(self) -> Template:
        """Get modern interactive template with D3.js graph visualization."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0a0e27; --bg-secondary: #141b3d; --bg-tertiary: #1a2347;
            --text-primary: #e0e6f7; --text-secondary: #a0a8c1;
            --accent-blue: #3b82f6; --accent-cyan: #06b6d4; --accent-purple: #8b5cf6;
            --accent-green: #10b981; --accent-orange: #f59e0b; --accent-red: #ef4444;
            --border-color: #2d3a5f; --glow-blue: rgba(59, 130, 246, 0.3);
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: var(--text-primary); overflow-x: hidden;
        }
        .grid-background {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(59, 130, 246, 0.05) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
            background-size: 50px 50px; pointer-events: none; z-index: 0;
        }
        .container { position: relative; z-index: 1; max-width: 1600px; margin: 0 auto; padding: 20px; }
        .header {
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            border-radius: 16px; padding: 30px; margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); position: relative; overflow: hidden;
        }
        .header::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan), var(--accent-purple));
        }
        .header h1 {
            font-size: 2.5em; font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px;
        }
        .header .subtitle { color: var(--text-secondary); font-size: 0.95em; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .stat-card {
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            border-radius: 12px; padding: 25px; position: relative; overflow: hidden;
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px); border-color: var(--accent-blue);
            box-shadow: 0 8px 24px var(--glow-blue);
        }
        .stat-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
            background: linear-gradient(180deg, var(--accent-blue), var(--accent-cyan));
        }
        .stat-number {
            font-size: 3em; font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            line-height: 1; margin-bottom: 8px;
        }
        .stat-label {
            color: var(--text-secondary); font-size: 0.9em;
            text-transform: uppercase; letter-spacing: 1px;
        }
        .main-content { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
        @media (max-width: 1200px) { .main-content { grid-template-columns: 1fr; } }
        .graph-container {
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            border-radius: 16px; padding: 25px; grid-column: 1 / -1; min-height: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        .graph-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .graph-title { font-size: 1.5em; font-weight: 600; color: var(--text-primary); }
        .graph-controls { display: flex; gap: 10px; }
        .control-btn {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            color: var(--text-primary); padding: 8px 16px; border-radius: 8px;
            cursor: pointer; font-size: 0.9em; transition: all 0.3s ease;
        }
        .control-btn:hover {
            background: var(--accent-blue); border-color: var(--accent-blue);
            box-shadow: 0 4px 12px var(--glow-blue);
        }
        #graph {
            width: 100%; height: 550px; background: var(--bg-tertiary);
            border-radius: 12px; border: 1px solid var(--border-color);
        }
        .section-panel {
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            border-radius: 16px; padding: 25px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        .section-title {
            font-size: 1.3em; font-weight: 600; color: var(--text-primary);
            margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;
        }
        .section-count {
            background: var(--bg-tertiary); padding: 4px 12px; border-radius: 20px;
            font-size: 0.8em; color: var(--accent-cyan);
        }
        .resource-grid { display: grid; gap: 12px; max-height: 500px; overflow-y: auto; padding-right: 10px; }
        .resource-grid::-webkit-scrollbar { width: 8px; }
        .resource-grid::-webkit-scrollbar-track { background: var(--bg-tertiary); border-radius: 4px; }
        .resource-grid::-webkit-scrollbar-thumb { background: var(--accent-blue); border-radius: 4px; }
        .resource-item {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            border-radius: 10px; padding: 15px; transition: all 0.3s ease; cursor: pointer; position: relative;
        }
        .resource-item:hover {
            border-color: var(--accent-blue); transform: translateX(5px);
            box-shadow: 0 4px 16px var(--glow-blue);
        }
        .resource-item.type-resource { border-left: 3px solid var(--accent-green); }
        .resource-item.type-data { border-left: 3px solid var(--accent-red); }
        .resource-item.type-module { border-left: 3px solid var(--accent-purple); }
        .resource-item.type-variable { border-left: 3px solid var(--accent-orange); }
        .resource-item.type-output { border-left: 3px solid var(--accent-blue); }
        .resource-item.type-provider { border-left: 3px solid var(--accent-cyan); }
        .resource-type {
            font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px;
            color: var(--text-secondary); margin-bottom: 6px;
        }
        .resource-name {
            font-family: 'Fira Code', monospace; font-size: 0.9em;
            color: var(--text-primary); margin-bottom: 8px; word-break: break-all;
        }
        .resource-file {
            font-size: 0.75em; color: var(--text-secondary); font-family: 'Fira Code', monospace;
        }
        .dependencies { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color); }
        .dependencies-label { font-size: 0.75em; color: var(--text-secondary); margin-bottom: 6px; }
        .dependency-tag {
            display: inline-block; background: var(--bg-primary); border: 1px solid var(--accent-blue);
            color: var(--accent-cyan); padding: 3px 8px; border-radius: 6px;
            font-size: 0.7em; margin: 2px; font-family: 'Fira Code', monospace;
        }
        .footer { text-align: center; padding: 30px; color: var(--text-secondary); font-size: 0.9em; }
        .search-box {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            border-radius: 10px; padding: 12px 16px; color: var(--text-primary);
            width: 100%; margin-bottom: 15px; font-size: 0.9em; transition: all 0.3s ease;
        }
        .search-box:focus {
            outline: none; border-color: var(--accent-blue); box-shadow: 0 0 0 3px var(--glow-blue);
        }
        .node { cursor: pointer; }
        .node circle { stroke-width: 2px; }
        .node.resource circle { fill: var(--accent-green); stroke: var(--accent-green); }
        .node.module circle { fill: var(--accent-purple); stroke: var(--accent-purple); }
        .node.variable circle { fill: var(--accent-orange); stroke: var(--accent-orange); }
        .node.output circle { fill: var(--accent-blue); stroke: var(--accent-blue); }
        .node.data circle { fill: var(--accent-red); stroke: var(--accent-red); }
        .node text { font-size: 11px; fill: var(--text-primary); pointer-events: none; }
        .link { stroke: var(--accent-blue); stroke-opacity: 0.3; stroke-width: 1.5px; }
        .node:hover circle { stroke-width: 4px; filter: drop-shadow(0 0 8px currentColor); }
        .legend { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 15px; }
        .legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.85em; }
        .legend-color { width: 16px; height: 16px; border-radius: 50%; }
    </style>
</head>
<body>
    <div class="grid-background"></div>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">📁 Generated at {{ timestamp }} | 🚀 Powered by TFKIT</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-number">{{ stats.resources }}</div><div class="stat-label">Resources</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.data_sources }}</div><div class="stat-label">Data Sources</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.modules }}</div><div class="stat-label">Modules</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.variables }}</div><div class="stat-label">Variables</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.outputs }}</div><div class="stat-label">Outputs</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.providers }}</div><div class="stat-label">Providers</div></div>
        </div>
        {% if include_graph %}
        <div class="graph-container">
            <div class="graph-header">
                <div class="graph-title">🔗 Dependency Graph</div>
                <div class="graph-controls">
                    <button class="control-btn" onclick="resetGraph()">Reset View</button>
                    <button class="control-btn" onclick="togglePhysics()">Toggle Physics</button>
                </div>
            </div>
            <div id="graph"></div>
            <div class="legend">
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-green);"></div><span>Resources</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-purple);"></div><span>Modules</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-orange);"></div><span>Variables</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-blue);"></div><span>Outputs</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-red);"></div><span>Data Sources</span></div>
            </div>
        </div>
        {% endif %}
        <div class="main-content">
            {% for section_name, objects in sections.items() if objects %}
            <div class="section-panel">
                <div class="section-title"><span>{{ section_name|title }}</span><span class="section-count">{{ objects|length }}</span></div>
                <input type="text" class="search-box" placeholder="Search {{ section_name }}..." onkeyup="filterSection(this, '{{ section_name }}')" />
                <div class="resource-grid" id="{{ section_name }}-grid">
                    {% for obj in objects %}
                    <div class="resource-item type-{{ obj.type }}" data-name="{{ obj.full_name|lower }}">
                        <div class="resource-type">{{ obj.type|upper }}</div>
                        <div class="resource-name">{{ obj.full_name }}</div>
                        {% if obj.dependencies %}
                        <div class="dependencies">
                            <div class="dependencies-label">Dependencies:</div>
                            {% for dep in obj.dependencies %}<span class="dependency-tag">{{ dep }}</span>{% endfor %}
                        </div>
                        {% endif %}
                        <div class="resource-file">{{ obj.file_path }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="footer">Generated by <strong>TFKIT</strong> - Terraform Intelligence & Analysis Suite</div>
    </div>
    <script>
        const graphData = {{ graph_data|safe }};
        let simulation, physicsEnabled = true;
        function initGraph() {
            const container = document.getElementById('graph');
            const width = container.clientWidth, height = container.clientHeight;
            const svg = d3.select('#graph').append('svg').attr('width', width).attr('height', height);
            const g = svg.append('g');
            const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (event) => g.attr('transform', event.transform));
            svg.call(zoom);
            simulation = d3.forceSimulation(graphData.nodes)
                .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(30));
            const link = g.append('g').selectAll('line').data(graphData.edges).join('line').attr('class', 'link');
            const node = g.append('g').selectAll('g').data(graphData.nodes).join('g')
                .attr('class', d => `node ${d.type}`)
                .call(d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended));
            node.append('circle').attr('r', 8);
            node.append('text').attr('dx', 12).attr('dy', 4)
                .text(d => d.label.length > 30 ? d.label.substring(0, 30) + '...' : d.label);
            node.append('title').text(d => `${d.type}: ${d.label}`);
            simulation.on('tick', () => {
                link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
        }
        function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
        function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
        function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }
        function resetGraph() { d3.select('#graph svg').select('g').transition().duration(750).attr('transform', 'translate(0,0) scale(1)'); }
        function togglePhysics() { physicsEnabled = !physicsEnabled; physicsEnabled ? simulation.alphaTarget(0.3).restart() : simulation.stop(); }
        function filterSection(input, sectionName) {
            const filter = input.value.toLowerCase();
            const grid = document.getElementById(sectionName + '-grid');
            const items = grid.getElementsByClassName('resource-item');
            for (let item of items) {
                const name = item.getAttribute('data-name');
                item.style.display = name.includes(filter) ? '' : 'none';
            }
        }
        if (graphData && graphData.nodes.length > 0) { initGraph(); }
    </script>
</body>
</html>
        """
        return Template(template_str)

    def _get_classic_template(self) -> Template:
        """Get classic light theme template."""
        return Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .resource-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 15px; }
        .resource-card { border: 1px solid #ccc; border-radius: 5px; padding: 15px; background: #f9f9f9; transition: transform 0.2s; }
        .resource-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .resource-type { font-weight: bold; color: #2c3e50; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px solid #eee; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .stat-card { background: #3498db; color: white; padding: 15px; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <p>Generated at: {{ timestamp }}</p>
        <div class="stats">
            {% for key, value in stats.items() %}
            <div class="stat-card">
                <div style="font-size: 2em; font-weight: bold;">{{ value }}</div>
                <div style="font-size: 0.9em;">{{ key|title }}</div>
            </div>
            {% endfor %}
        </div>
        {% for section_name, objects in sections.items() if objects %}
        <div class="section">
            <h2>{{ section_name|title }} ({{ objects|length }})</h2>
            <div class="resource-grid">
                {% for obj in objects %}
                <div class="resource-card">
                    <div class="resource-type">{{ obj.type|upper }}</div>
                    <div>{{ obj.full_name }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #000000; color: #ffffff; overflow: hidden; }
        #graph-container { width: 100vw; height: 100vh; position: relative; }
        .hud {
            position: absolute; top: 20px; left: 20px; background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ffff; border-radius: 10px; padding: 20px;
            backdrop-filter: blur(10px); box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
        }
        .hud h2 { color: #00ffff; margin-bottom: 15px; font-size: 1.2em; text-shadow: 0 0 10px #00ffff; }
        .hud-stat { display: flex; justify-content: space-between; margin: 8px 0; font-size: 0.9em; }
        .hud-stat-label { color: #888; }
        .hud-stat-value { color: #00ffff; font-weight: bold; }
        .controls {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8); border: 1px solid #00ffff; border-radius: 30px;
            padding: 15px 30px; display: flex; gap: 15px; backdrop-filter: blur(10px);
        }
        .control-btn {
            background: transparent; border: 1px solid #00ffff; color: #00ffff;
            padding: 10px 20px; border-radius: 20px; cursor: pointer; font-size: 0.9em;
            transition: all 0.3s ease;
        }
        .control-btn:hover { background: #00ffff; color: #000; box-shadow: 0 0 20px #00ffff; }
        .legend {
            position: absolute; top: 20px; right: 20px; background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ffff; border-radius: 10px; padding: 20px; backdrop-filter: blur(10px);
        }
        .legend-title { color: #00ffff; margin-bottom: 15px; font-size: 1.1em; }
        .legend-item { display: flex; align-items: center; gap: 10px; margin: 8px 0; font-size: 0.85em; }
        .legend-dot { width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 10px currentColor; }
        .node { cursor: pointer; }
        .node circle { stroke-width: 2px; filter: drop-shadow(0 0 5px currentColor); }
        .link { stroke: #00ffff; stroke-opacity: 0.4; stroke-width: 2px; }
        .link-arrow { fill: #00ffff; opacity: 0.6; }
        .node text { font-size: 10px; fill: #ffffff; text-shadow: 0 0 5px #000; pointer-events: none; }
        .node:hover circle { stroke-width: 4px; filter: drop-shadow(0 0 15px currentColor); }
        .particle { fill: #00ffff; opacity: 0.8; }
    </style>
</head>
<body>
    <div id="graph-container"></div>
    <div class="hud">
        <h2>⚡ TERRAFORM GRAPH</h2>
        <div class="hud-stat"><span class="hud-stat-label">Total Nodes:</span><span class="hud-stat-value">{{ stats.total }}</span></div>
        <div class="hud-stat"><span class="hud-stat-label">Resources:</span><span class="hud-stat-value">{{ stats.resources }}</span></div>
        <div class="hud-stat"><span class="hud-stat-label">Modules:</span><span class="hud-stat-value">{{ stats.modules }}</span></div>
        <div class="hud-stat"><span class="hud-stat-label">Variables:</span><span class="hud-stat-value">{{ stats.variables }}</span></div>
        <div class="hud-stat"><span class="hud-stat-label">Outputs:</span><span class="hud-stat-value">{{ stats.outputs }}</span></div>
    </div>
    <div class="legend">
        <div class="legend-title">Node Types</div>
        <div class="legend-item"><div class="legend-dot" style="background: #10b981; color: #10b981;"></div><span>Resources</span></div>
        <div class="legend-item"><div class="legend-dot" style="background: #8b5cf6; color: #8b5cf6;"></div><span>Modules</span></div>
        <div class="legend-item"><div class="legend-dot" style="background: #f59e0b; color: #f59e0b;"></div><span>Variables</span></div>
        <div class="legend-item"><div class="legend-dot" style="background: #3b82f6; color: #3b82f6;"></div><span>Outputs</span></div>
        <div class="legend-item"><div class="legend-dot" style="background: #ef4444; color: #ef4444;"></div><span>Data Sources</span></div>
    </div>
    <div class="controls">
        <button class="control-btn" onclick="resetView()">🎯 Reset</button>
        <button class="control-btn" onclick="togglePhysics()">⚡ Physics</button>
        <button class="control-btn" onclick="centerGraph()">📍 Center</button>
    </div>
    <script>
        const graphData = {{ graph_data|safe }};
        let simulation, physicsEnabled = true;
        const colors = { resource: '#10b981', module: '#8b5cf6', variable: '#f59e0b', output: '#3b82f6', data: '#ef4444' };
        function init() {
            const container = document.getElementById('graph-container');
            const width = container.clientWidth, height = container.clientHeight;
            const svg = d3.select('#graph-container').append('svg').attr('width', width).attr('height', height);
            const defs = svg.append('defs');
            Object.keys(colors).forEach(type => {
                defs.append('marker').attr('id', `arrow-${type}`).attr('viewBox', '0 -5 10 10')
                    .attr('refX', 20).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6)
                    .attr('orient', 'auto').append('path').attr('d', 'M0,-5L10,0L0,5')
                    .attr('class', 'link-arrow').style('fill', colors[type]);
            });
            const g = svg.append('g');
            const zoom = d3.zoom().scaleExtent([0.1, 8]).on('zoom', (event) => g.attr('transform', event.transform));
            svg.call(zoom);
            simulation = d3.forceSimulation(graphData.nodes)
                .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(150))
                .force('charge', d3.forceManyBody().strength(-500))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(40));
            const link = g.append('g').selectAll('line').data(graphData.edges).join('line').attr('class', 'link')
                .attr('marker-end', d => {
                    const target = graphData.nodes.find(n => n.id === d.target.id || n.id === d.target);
                    return target ? `url(#arrow-${target.type})` : '';
                });
            const node = g.append('g').selectAll('g').data(graphData.nodes).join('g')
                .attr('class', d => `node ${d.type}`)
                .call(d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended));
            node.append('circle')
                .attr('r', d => d.type === 'module' ? 12 : d.type === 'resource' ? 10 : 8)
                .style('fill', d => colors[d.type] || '#00ffff')
                .style('stroke', d => colors[d.type] || '#00ffff');
            node.append('text').attr('dx', 15).attr('dy', 4)
                .text(d => d.label.length > 25 ? d.label.substring(0, 25) + '...' : d.label)
                .style('fill', '#ffffff').style('font-size', '11px');
            node.append('title').text(d => `${d.type.toUpperCase()}\\n${d.label}\\nType: ${d.subtype}`);
            simulation.on('tick', () => {
                link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
            setInterval(() => {
                if (graphData.edges.length > 0) {
                    const edge = graphData.edges[Math.floor(Math.random() * graphData.edges.length)];
                    const particle = g.append('circle').attr('class', 'particle').attr('r', 3)
                        .attr('cx', edge.source.x).attr('cy', edge.source.y);
                    particle.transition().duration(1000).attr('cx', edge.target.x).attr('cy', edge.target.y)
                        .style('opacity', 0).remove();
                }
            }, 200);
        }
        function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
        function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
        function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }
        function resetView() { d3.select('#graph-container svg').transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity); }
        function togglePhysics() { physicsEnabled = !physicsEnabled; physicsEnabled ? simulation.alphaTarget(0.3).restart() : simulation.stop(); }
        function centerGraph() {
            const container = document.getElementById('graph-container');
            simulation.force('center', d3.forceCenter(container.clientWidth / 2, container.clientHeight / 2));
            simulation.alpha(1).restart();
        }
        init();
    </script>
</body>
</html>
        """)

    def _get_dashboard_template(self) -> Template:
        """Get dashboard-style template with metrics and charts."""
        return Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .dashboard { max-width: 1600px; margin: 0 auto; }
        .header {
            background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { color: #667eea; margin-bottom: 10px; }
        .metrics-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 20px;
        }
        .metric-card {
            background: white; padding: 25px; border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-value { font-size: 3em; font-weight: bold; color: #667eea; }
        .metric-label { color: #888; text-transform: uppercase; font-size: 0.85em; margin-top: 10px; }
        .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .chart-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .chart-title { font-size: 1.2em; color: #333; margin-bottom: 20px; }
        canvas { max-height: 300px; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>📊 {{ title }}</h1>
            <p>Infrastructure Analytics Dashboard - {{ timestamp }}</p>
        </div>
        <div class="metrics-grid">
            <div class="metric-card"><div class="metric-value">{{ stats.resources }}</div><div class="metric-label">Resources</div></div>
            <div class="metric-card"><div class="metric-value">{{ stats.modules }}</div><div class="metric-label">Modules</div></div>
            <div class="metric-card"><div class="metric-value">{{ stats.variables }}</div><div class="metric-label">Variables</div></div>
            <div class="metric-card"><div class="metric-value">{{ stats.outputs }}</div><div class="metric-label">Outputs</div></div>
            <div class="metric-card"><div class="metric-value">{{ stats.data_sources }}</div><div class="metric-label">Data Sources</div></div>
            <div class="metric-card"><div class="metric-value">{{ stats.providers }}</div><div class="metric-label">Providers</div></div>
        </div>
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Component Distribution</div>
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">Infrastructure Overview</div>
                <canvas id="barChart"></canvas>
            </div>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('pieChart'), {
            type: 'doughnut',
            data: {
                labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data Sources', 'Providers'],
                datasets: [{
                    data: [{{ stats.resources }}, {{ stats.modules }}, {{ stats.variables }}, {{ stats.outputs }}, {{ stats.data_sources }}, {{ stats.providers }}],
                    backgroundColor: ['#10b981', '#8b5cf6', '#f59e0b', '#3b82f6', '#ef4444', '#06b6d4']
                }]
            },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }
        });
        new Chart(document.getElementById('barChart'), {
            type: 'bar',
            data: {
                labels: ['Resources', 'Modules', 'Variables', 'Outputs', 'Data', 'Providers'],
                datasets: [{
                    label: 'Count',
                    data: [{{ stats.resources }}, {{ stats.modules }}, {{ stats.variables }}, {{ stats.outputs }}, {{ stats.data_sources }}, {{ stats.providers }}],
                    backgroundColor: ['#10b981', '#8b5cf6', '#f59e0b', '#3b82f6', '#ef4444', '#06b6d4']
                }]
            },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    </script>
</body>
</html>
        """)
