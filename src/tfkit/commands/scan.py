import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from tfkit.analyzer.converter import TerraformToGraphModelConverter

# from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
# from tfkit.visualizer.generator import ReportGenerator
from .utils import (
    console,
    display_scan_results,
    display_simple_results,
    export_yaml,
    get_scan_data,
    print_banner,
)


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output directory"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml", "simple"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--open", "-O", is_flag=True, help="Open results in browser")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option(
    "--save", "-s", type=click.Path(path_type=Path), help="Save scan results to file"
)
@click.option(
    "--theme",
    type=click.Choice(
        [
            "light",
            "dark",
            "cyber",
            "github-dark",
            "monokai",
            "solarized-light",
            "dracula",
            "atom-one-dark",
            "gruvbox-dark",
            "night-owl",
        ],
        case_sensitive=False,
    ),
    default="dark",
    help="Visualization theme (default: dark)",
)
@click.option(
    "--layout",
    type=click.Choice(["classic", "graph", "dashboard"], case_sensitive=False),
    default="graph",
    help="Visualization layout (default: graph)",
)
def scan(path, output, format, open, quiet, save, theme, layout):
    """Quick scan of Terraform project for rapid insights.

    Performs a fast scan of your Terraform project and displays
    key metrics, resource counts, and potential issues.

    \b
    Examples:
      tfkit scan                          # Scan current directory
      tfkit scan /path/to/terraform       # Scan specific path
      tfkit scan --format json            # Output as JSON
      tfkit scan --open                   # Scan and open visualization
      tfkit scan --save scan.json         # Save results

    PATH: Path to Terraform project (default: current directory)
    """
    from tfkit.inspector.parser import TerraformParser

    if not quiet:
        print_banner(show_version=False)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Scanning Terraform files...", total=100)

            parser = TerraformParser()
            # analyzer = TerraformAnalyzer()
            progress.update(task, advance=30, description="Parsing configurations...")
            module = parser.parse_module(path, recursive=True)
            # project = analyzer.analyze_project(path)
            progress.update(task, advance=40, description="Building resource map...")
            progress.update(task, advance=30, description="Finalizing analysis...")

        if hasattr(module, "to_dict"):
            project_data = module.to_dict()
        elif hasattr(module, "__dict__"):
            project_data = module.__dict__
        else:
            project_data = module

        # if format == "table":
        #     display_scan_results(project_data, quiet)
        # elif format == "json":
        #     console.print(json.dumps(get_scan_data(project_data), indent=2))
        # elif format == "yaml":
        #     export_yaml(get_scan_data(project_data))
        # else:  # simple format
        #     display_simple_results(project_data)

        converter = TerraformToGraphModelConverter()
        graph_data = converter.convert_module_to_graph(module)

        save_path = Path("out/")
        module_save_path = save_path.with_suffix(".module.json")
        output_file_path = save_path.with_suffix(".index.html")

        if save:
            graph_save_path = save_path.with_suffix(".graph.json")
            with graph_save_path.open("w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)

            with module_save_path.open("w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2)

        if open:
            from tfkit.templates.template_factory import TemplateFactory
            from tfkit.templates.theme_manager import ThemeManager

            try:
                from tfkit import __version__
            except ImportError:
                __version__ = "Unknown"

            report_context = {
                "title": "Integration test",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tfkit_version": __version__,
                "project_path": "",
                "config_data": json.dumps({}),
                "graph_data": json.dumps(graph_data),
                "theme_name": theme,
                "theme_colors": ThemeManager.get_theme_colors(theme),
            }

            TemplateFactory().render_to_file(
                "graph",
                output_file_path,
                **report_context,
            )

            absolute_path = output_file_path.resolve()

            print("📊 Opening Terraform Graph...")
            print(f"📍 File: {absolute_path}")

            import webbrowser

            webbrowser.open(f"file://{absolute_path}")
            # generator = ReportGenerator()
            # html_file = generator.generate_analysis_report(
            #     project,
            #     output,
            #     theme=theme,
            #     layout=layout,
            # )

            # generator.open_in_browser(html_file)
            # if not quiet:
            #     console.print(
            #         f"\n🌐 Opened {layout} visualization: [green]{html_file}[/green]"
            #     )

    except Exception as e:
        console.print(f"\n[red]✗ Scan failed:[/red] {e}")
        sys.exit(1)
