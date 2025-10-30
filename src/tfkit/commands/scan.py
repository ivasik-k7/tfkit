import json
import sys
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.visualizer.generator import ReportGenerator

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

            analyzer = TerraformAnalyzer()
            progress.update(task, advance=30, description="Parsing configurations...")
            project = analyzer.analyze_project(path)
            progress.update(task, advance=40, description="Building resource map...")
            progress.update(task, advance=30, description="Finalizing analysis...")

        if hasattr(project, "to_dict"):
            project_data = project.to_dict()
        elif hasattr(project, "__dict__"):
            project_data = project.__dict__
        else:
            project_data = project

        if format == "table":
            display_scan_results(project_data, quiet)
        elif format == "json":
            console.print(json.dumps(get_scan_data(project_data), indent=2))
        elif format == "yaml":
            export_yaml(get_scan_data(project_data))
        else:  # simple format
            display_simple_results(project_data)

        if save:
            with save.open("w") as f:
                json.dump(project.to_dict(), f, indent=2, default=str)
            if not quiet:
                console.print(f"\n✓ Results saved to: [green]{save}[/green]")

        if open:
            generator = ReportGenerator()
            html_file = generator.generate_analysis_report(
                project,
                output,
                theme=theme,
                layout=layout,
            )

            generator.open_in_browser(html_file)
            if not quiet:
                console.print(
                    f"\n🌐 Opened {layout} visualization: [green]{html_file}[/green]"
                )

    except Exception as e:
        console.print(f"\n[red]✗ Scan failed:[/red] {e}")
        sys.exit(1)
