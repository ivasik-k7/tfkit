"""Advanced CLI interface for tfkit with comprehensive parameter support."""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from tfkit import __version__
from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.validator.models import ValidationSeverity
from tfkit.validator.validator import TerraformValidator
from tfkit.visualizer.generator import ReportGenerator

console = Console()

TFKIT_BANNER = """
████████╗███████╗██╗  ██╗██╗████████╗
╚══██╔══╝██╔════╝██║ ██╔╝██║╚══██╔══╝
   ██║   █████╗  █████╔╝ ██║   ██║
   ██║   ██╔══╝  ██╔═██╗ ██║   ██║
   ██║   ██║     ██║  ██╗██║   ██║
   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝
"""

TFKIT_TAGLINE = "[bold cyan]Terraform Intelligence & Analysis Suite[/bold cyan]"


def print_banner(show_version: bool = True):
    """Print enhanced tfkit banner."""
    console.print(f"[bold blue]{TFKIT_BANNER}[/bold blue]", highlight=False)
    if show_version:
        console.print(f"  [dim]v{__version__} [/dim]\n")


def print_welcome():
    """Print comprehensive welcome screen."""
    print_banner()

    welcome_text = """[bold white]Welcome to TFKIT[/bold white] - Your Terraform analysis companion

[bold cyan]What can TFKIT do?[/bold cyan]
  • Deep analysis of Terraform projects with dependency tracking
  • Interactive HTML visualizations with resource graphs
  • Multi-format exports (JSON, YAML, Markdown, CSV)
  • Resource dependency mapping and impact analysis
  • Security and compliance scanning
  • Cost estimation and optimization insights
  • Module usage analytics and recommendations

[bold yellow]Quick Commands:[/bold yellow]
  tfkit scan                    # Quick scan of current directory
  tfkit analyze --deep          # Deep analysis with all features
  tfkit inspect resource        # Inspect specific resources
  tfkit report --interactive    # Generate interactive report

[dim]Run 'tfkit --help' for complete documentation
Run 'tfkit examples' for common usage patterns[/dim]
"""
    console.print(Panel(welcome_text, border_style="blue", padding=(1, 2)))


# ============================================================================
# MAIN CLI GROUP
# ============================================================================


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option("--version", "-v", is_flag=True, help="Show version information")
@click.option(
    "--welcome", "-w", is_flag=True, help="Show welcome screen with quick start guide"
)
@click.option("--debug", is_flag=True, help="Enable debug mode with verbose logging")
@click.pass_context
def cli(ctx, version, welcome, debug):
    """TFKIT - Advanced Terraform Intelligence & Analysis Suite

    A comprehensive toolkit for analyzing, visualizing, and understanding
    your Terraform infrastructure. Perform deep analysis, generate reports,
    inspect resources, and gain insights into your IaC projects.

    \b
    Core Commands:
      scan       Quick scan of Terraform project
      analyze    Deep analysis with full feature set
      inspect    Detailed inspection of specific components
      report     Generate comprehensive reports
      export     Export analysis data in multiple formats
      validate   Validate Terraform configurations

    \b
    Utility Commands:
      examples   Show usage examples and patterns
      config     Manage TFKIT configuration
      info       Display system and project information

    Use 'tfkit COMMAND --help' for detailed command information.
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    if version:
        show_version_info()
        ctx.exit()

    if welcome or ctx.invoked_subcommand is None:
        print_welcome()
        if ctx.invoked_subcommand is None:
            ctx.exit()


# ============================================================================
# SCAN COMMAND - Quick Analysis
# ============================================================================


@cli.command()
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
        ["light", "dark", "cyber", "nord", "github-dark"], case_sensitive=False
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

        # if format == "table":
        #     _display_scan_results(project, quiet)
        # elif format == "json":
        #     console.print(json.dumps(_get_scan_data(project), indent=2))
        # elif format == "yaml":
        #     _export_yaml(_get_scan_data(project))
        # else:
        #     _display_simple_results(project)

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


# ============================================================================
# ANALYZE COMMAND - Deep Analysis
# ============================================================================


# @cli.command()
# @click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
# @click.option(
#     "--deep", "-d", is_flag=True, help="Enable deep analysis with dependency tracking"
# )
# @click.option(
#     "--include-dependencies", "-D", is_flag=True, help="Analyze module dependencies"
# )
# @click.option(
#     "--include-security", "-S", is_flag=True, help="Include security analysis"
# )
# @click.option("--include-costs", "-C", is_flag=True, help="Include cost estimation")
# @click.option(
#     "--output",
#     "-o",
#     type=click.Path(path_type=Path),
#     help="Output directory for reports",
# )
# @click.option("--export-json", type=click.Path(path_type=Path), help="Export as JSON")
# @click.option("--export-yaml", type=click.Path(path_type=Path), help="Export as YAML")
# @click.option(
#     "--export-markdown",
#     type=click.Path(path_type=Path),
#     help="Export as Markdown report",
# )
# @click.option(
#     "--export-csv", type=click.Path(path_type=Path), help="Export resource list as CSV"
# )
# @click.option(
#     "--open-browser", "-b", is_flag=True, help="Open visualization in browser"
# )
# @click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
# @click.option("--verbose", "-v", is_flag=True, help="Show detailed analysis steps")
# @click.option(
#     "--threads",
#     "-t",
#     type=int,
#     default=4,
#     help="Number of analysis threads (default: 4)",
# )
# @click.option(
#     "--exclude",
#     "-e",
#     multiple=True,
#     help="Exclude patterns (can be used multiple times)",
# )
# @click.option("--include-only", "-i", multiple=True, help="Include only these patterns")
# @click.option("--max-depth", type=int, help="Maximum module depth to analyze")
# @click.option("--tags", multiple=True, help="Filter resources by tags")
# @click.option("--providers", multiple=True, help="Filter by provider types")
# def analyze(
#     path,
#     deep,
#     include_dependencies,
#     include_security,
#     include_costs,
#     output,
#     export_json,
#     export_yaml,
#     export_markdown,
#     export_csv,
#     open_browser,
#     quiet,
#     verbose,
#     threads,
#     exclude,
#     include_only,
#     max_depth,
#     tags,
#     providers,
# ):
#     """Deep analysis of Terraform projects with advanced features.

#     Performs comprehensive analysis including resource relationships,
#     module dependencies, security scanning, and cost estimation.

#     \b
#     Analysis Modes:
#       --deep                  Full deep analysis (recommended)
#       --include-dependencies  Track module dependencies
#       --include-security      Security and compliance checks
#       --include-costs         Cost estimation analysis

#     \b
#     Export Options:
#       --export-json          JSON format (machine-readable)
#       --export-yaml          YAML format (human-readable)
#       --export-markdown      Markdown report (documentation)
#       --export-csv           CSV resource list (spreadsheet)

#     \b
#     Filtering:
#       --exclude PATTERN      Exclude resources matching pattern
#       --include-only PATTERN Include only matching resources
#       --tags TAG             Filter by resource tags
#       --providers PROVIDER   Filter by provider (aws, azure, gcp, etc.)

#     \b
#     Examples:
#       # Full analysis with all features
#       tfkit analyze --deep -D -S -C --open-browser

#       # Analysis with exports
#       tfkit analyze --export-json data.json --export-markdown report.md

#       # Filtered analysis
#       tfkit analyze --providers aws --tags production

#       # Fast analysis with exclusions
#       tfkit analyze --exclude "*.test.tf" --threads 8

#       # Security-focused analysis
#       tfkit analyze --include-security --export-markdown security-report.md

#     PATH: Path to Terraform project (default: current directory)
#     """
#     if not quiet:
#         print_banner(show_version=False)
#         mode = (
#             "[bold yellow]DEEP ANALYSIS[/bold yellow]"
#             if deep
#             else "[bold]Standard Analysis[/bold]"
#         )
#         console.print(f"{mode} Mode")
#         console.print(f"   Target: [cyan]{path.resolve()}[/cyan]")
#         console.print(f"   Threads: [yellow]{threads}[/yellow]")

#         features = []
#         if include_dependencies:
#             features.append("Dependencies")
#         if include_security:
#             features.append("Security")
#         if include_costs:
#             features.append("Costs")
#         if features:
#             console.print(f"   Features: [green]{', '.join(features)}[/green]")

#         if exclude:
#             console.print(f"   Excluding: [dim]{', '.join(exclude)}[/dim]")
#         if providers:
#             console.print(f"   Providers: [blue]{', '.join(providers)}[/blue]")
#         console.print()

#     try:
#         if verbose and not quiet:
#             with Progress(
#                 SpinnerColumn(),
#                 TextColumn("[progress.description]{task.description}"),
#                 BarColumn(),
#                 TaskProgressColumn(),
#                 console=console,
#             ) as progress:
#                 main_task = progress.add_task("[cyan]Analyzing project...", total=100)

#                 progress.update(
#                     main_task, advance=10, description="[cyan]Initializing analyzer..."
#                 )
#                 analyzer = TerraformAnalyzer()

#                 progress.update(
#                     main_task,
#                     advance=20,
#                     description="[cyan]Parsing Terraform files...",
#                 )
#                 project = analyzer.analyze_project(path)

#                 progress.update(
#                     main_task,
#                     advance=30,
#                     description="[cyan]Building resource graph...",
#                 )

#                 if include_dependencies:
#                     progress.update(
#                         main_task,
#                         advance=15,
#                         description="[yellow]Analyzing dependencies...",
#                     )

#                 if include_security:
#                     progress.update(
#                         main_task, advance=15, description="[red]Security scanning..."
#                     )

#                 if include_costs:
#                     progress.update(
#                         main_task, advance=10, description="[green]Cost estimation..."
#                     )

#                 progress.update(
#                     main_task, advance=100, description="[green]✓ Analysis complete"
#                 )
#         else:
#             analyzer = TerraformAnalyzer()
#             project = analyzer.analyze_project(path)

#         if providers:
#             _apply_provider_filter(project, providers)

#         exports_completed = []

#         if export_json:
#             with export_json.open("w") as f:
#                 json.dump(project.to_dict(), f, indent=2, default=str)
#             exports_completed.append(f"JSON → {export_json}")

#         if export_yaml:
#             _export_yaml_file(project.to_dict(), export_yaml)
#             exports_completed.append(f"YAML → {export_yaml}")

#         if export_markdown:
#             _export_markdown_report(
#                 project, export_markdown, include_security, include_costs
#             )
#             exports_completed.append(f"Markdown → {export_markdown}")

#         if export_csv:
#             _export_csv_resources(project, export_csv)
#             exports_completed.append(f"CSV → {export_csv}")

#         if exports_completed and not quiet:
#             console.print("\n[bold]📦 Exports completed:[/bold]")
#             for export in exports_completed:
#                 console.print(f"   ✓ {export}")

#         if output or open_browser:
#             if verbose and not quiet:
#                 console.print("\n📊 Generating visualization...")
#             generator = ReportGenerator()
#             html_file = generator.generate_visualization(project, output)
#             if not quiet:
#                 console.print(f"   ✓ Visualization: [green]{html_file}[/green]")

#             if open_browser:
#                 generator.open_in_browser(html_file)
#                 if not quiet:
#                     console.print("   🌐 Opened in browser")

#         if not quiet:
#             console.print()
#             # _display_detailed_analysis_summary(
#             #     project,
#             #     deep,
#             #     include_dependencies,
#             #     include_security,
#             #     include_costs,
#             #     verbose,
#             # )

#         return project

#     except Exception as e:
#         console.print(f"\n[red]✗ Analysis failed:[/red] {e}")
#         if verbose:
#             console.print_exception()
#         sys.exit(1)


# ============================================================================
# INSPECT COMMAND - Detailed Component Inspection
# ============================================================================


# @cli.command()
# @click.argument(
#     "component_type",
#     type=click.Choice(
#         [
#             "resource",
#             "module",
#             "variable",
#             "output",
#             "provider",
#             "data",
#             "local",
#             "terraform",
#         ],
#         case_sensitive=False,
#     ),
# )
# @click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
# @click.option("--name", "-n", help="Specific component name to inspect")
# @click.option(
#     "--type", "-t", "resource_type", help="Filter by resource type (e.g., aws_instance)"
# )
# @click.option("--show-dependencies", "-d", is_flag=True, help="Show dependency tree")
# @click.option("--show-dependents", is_flag=True, help="Show dependent components")
# @click.option("--show-references", "-r", is_flag=True, help="Show all references")
# @click.option("--show-attributes", "-a", is_flag=True, help="Show all attributes")
# @click.option("--show-metadata", "-m", is_flag=True, help="Show enhanced metadata")
# @click.option("--show-locations", "-l", is_flag=True, help="Show file locations")
# @click.option(
#     "--format",
#     "-f",
#     type=click.Choice(
#         ["tree", "table", "json", "detailed", "yaml"], case_sensitive=False
#     ),
#     default="tree",
#     help="Display format",
# )
# @click.option(
#     "--export", "-e", type=click.Path(path_type=Path), help="Export inspection results"
# )
# @click.option(
#     "--filter", "filters", multiple=True, help="Filter by attribute (key=value)"
# )
# @click.option("--sort", help="Sort by field (name, type, file, line)")
# @click.option("--limit", type=int, help="Limit number of results")
# def inspect(
#     component_type,
#     path,
#     name,
#     resource_type,
#     show_dependencies,
#     show_dependents,
#     show_references,
#     show_attributes,
#     show_metadata,
#     show_locations,
#     format,
#     export,
#     filters,
#     sort,
#     limit,
# ):
#     """Inspect specific Terraform components in detail.

#     Provides deep inspection of resources, modules, variables, outputs,
#     providers, data sources, locals, and terraform blocks with comprehensive details.

#     \b
#     Component Types:
#       resource     Inspect Terraform resources
#       module       Inspect module configurations
#       variable     Inspect input variables
#       output       Inspect output values
#       provider     Inspect provider configurations
#       data         Inspect data sources
#       local        Inspect local values
#       terraform    Inspect terraform configuration blocks

#     \b
#     Display Options:
#       --show-dependencies   Display dependency tree
#       --show-dependents     Show components that depend on this
#       --show-references     Show all references to/from component
#       --show-attributes     Display all attributes and values
#       --show-metadata       Display enhanced metadata
#       --show-locations      Show detailed file locations
#       --format tree         Tree view (default, hierarchical)
#       --format table        Table view (structured)
#       --format json         JSON output (machine-readable)
#       --format yaml         YAML output
#       --format detailed     Detailed prose format

#     \b
#     Examples:
#       # Inspect all resources
#       tfkit inspect resource

#       # Inspect specific resource with enhanced metadata
#       tfkit inspect resource --name aws_instance.web --show-metadata

#       # Inspect with dependencies and dependents
#       tfkit inspect resource --name aws_instance.web --show-dependencies --show-dependents

#       # Filter by type and show attributes
#       tfkit inspect resource --type aws_instance --show-attributes

#       # Inspect modules with enhanced information
#       tfkit inspect module --show-attributes --show-metadata --format table

#       # Export inspection results
#       tfkit inspect resource --export inspection.json

#       # Filter by attributes and sort results
#       tfkit inspect resource --filter "provider=aws" --sort name --limit 10
#     """
#     print_banner(show_version=False)
#     console.print(f"[bold]🔎 Inspecting {component_type.upper()}S[/bold]")
#     console.print(f"   Location: [cyan]{path.resolve()}[/cyan]")
#     if name:
#         console.print(f"   Target: [yellow]{name}[/yellow]")
#     if resource_type:
#         console.print(f"   Type: [blue]{resource_type}[/blue]")
#     if filters:
#         console.print(f"   Filters: [dim]{', '.join(filters)}[/dim]")
#     console.print()

#     try:
#         with console.status("[bold cyan]Analyzing Terraform project..."):
#             analyzer = TerraformAnalyzer()
#             project = analyzer.analyze_project(str(path))

#         components = _get_components_by_type(
#             project, component_type, name, resource_type, filters
#         )

#         if not components:
#             console.print(
#                 f"[yellow]⚠[/yellow]  No {component_type}s found matching criteria"
#             )
#             # Show available components of this type
#             available = _get_components_by_type(project, component_type, None, None, [])
#             if available:
#                 console.print(f"\n[dim]Available {component_type}s:[/dim]")
#                 for comp_name in sorted(available.keys())[:10]:
#                     console.print(f"  • {comp_name}")
#                 if len(available) > 10:
#                     console.print(f"  • ... and {len(available) - 10} more")
#             sys.exit(0)

#         components = _apply_sorting_and_limits(components, sort, limit)

#         if format == "tree":
#             _display_component_tree(
#                 components,
#                 component_type,
#                 show_dependencies,
#                 show_references,
#                 show_attributes,
#             )
#         # elif format == "table":
#         #     _display_component_table(
#         #         project,
#         #         components,
#         #         component_type,
#         #         show_attributes,
#         #         show_metadata,
#         #         show_locations,
#         #     )
#         # elif format == "json":
#         #     _display_component_json(project, components, component_type)
#         # elif format == "yaml":
#         #     _display_component_yaml(project, components, component_type)
#         else:
#             _display_component_detailed(
#                 project,
#                 components,
#                 component_type,
#                 show_dependencies,
#                 show_dependents,
#                 show_references,
#                 show_attributes,
#                 show_metadata,
#                 show_locations,
#             )

#         if export:
#             export_data = _prepare_export_data(project, components, component_type)
#             with export.open("w") as f:
#                 if export.suffix.lower() == ".yaml":
#                     try:
#                         import yaml

#                         yaml.dump(export_data, f, default_flow_style=False)
#                     except ImportError:
#                         json.dump(export_data, f, indent=2, default=str)
#                 else:
#                     json.dump(export_data, f, indent=2, default=str)
#             console.print(
#                 f"\n✓ Inspection results exported to: [green]{export}[/green]"
#             )

#     except Exception as e:
#         console.print(f"\n[red]✗ Inspection failed:[/red] {e}")
#         sys.exit(1)


# def _get_components_by_type(project, component_type, name, resource_type, filters):
#     """Get components filtered by type and criteria."""
#     type_map = {
#         "resource": (ResourceType.RESOURCE, project.resources),
#         "module": (ResourceType.MODULE, project.modules),
#         "variable": (ResourceType.VARIABLE, project.variables),
#         "output": (ResourceType.OUTPUT, project.outputs),
#         "provider": (ResourceType.PROVIDER, project.providers),
#         "data": (ResourceType.DATA, project.data_sources),
#         "local": (ResourceType.LOCAL, project.locals),
#         "terraform": (ResourceType.TERRAFORM, project.terraform_blocks),
#     }

#     _, components = type_map.get(component_type, (None, {}))

#     # Filter by name if specified
#     if name:
#         if name in components:
#             components = {name: components[name]}
#         else:
#             # Try partial match
#             matches = {k: v for k, v in components.items() if name in k}
#             if matches:
#                 components = matches
#             else:
#                 return {}

#     # Filter by resource type
#     if resource_type and component_type in ["resource", "data"]:
#         components = {
#             k: v
#             for k, v in components.items()
#             if hasattr(v, "resource_type") and v.resource_type == resource_type
#         }

#     # Apply attribute filters
#     if filters:
#         for filter_str in filters:
#             if "=" in filter_str:
#                 key, value = filter_str.split("=", 1)
#                 components = {
#                     k: v
#                     for k, v in components.items()
#                     if _component_matches_filter(v, key, value)
#                 }

#     return components


# def _component_matches_filter(component, key, value):
#     """Check if component matches filter criteria."""
#     # Check attributes
#     if key in component.attributes:
#         attr_value = component.attributes[key]
#         return str(attr_value) == value

#     # Check enhanced fields
#     enhanced_fields = ["resource_type", "provider", "source", "variable_type", "alias"]
#     for field in enhanced_fields:
#         if hasattr(component, field) and getattr(component, field) == value:
#             return True

#     # Check file path
#     if key == "file" and value in component.file_path:
#         return True

#     return False


# def _apply_sorting_and_limits(components, sort, limit):
#     """Apply sorting and limiting to components."""
#     sorted_components = dict(sorted(components.items()))

#     if sort:
#         if sort == "type":
#             sorted_components = dict(
#                 sorted(
#                     components.items(),
#                     key=lambda x: getattr(x[1], "resource_type", x[0]),
#                 )
#             )
#         elif sort == "file":
#             sorted_components = dict(
#                 sorted(components.items(), key=lambda x: x[1].file_path)
#             )
#         elif sort == "line":
#             sorted_components = dict(
#                 sorted(components.items(), key=lambda x: x[1].line_number)
#             )

#     if limit and limit > 0:
#         limited = dict(list(sorted_components.items())[:limit])
#         return limited

#     return sorted_components


# def _display_component_tree(
#     project,
#     components,
#     component_type,
#     show_dependencies,
#     show_dependents,
#     show_attributes,
#     show_metadata,
#     show_locations,
# ):
#     """Display components in tree format."""
#     tree = Tree(f"📁 [bold]{component_type.upper()}S[/bold]")

#     for comp_name, component in components.items():
#         branch = tree.add(f"[cyan]{comp_name}[/cyan]")

#         # Basic info
#         if hasattr(component, "resource_type") and component.resource_type:
#             branch.add(f"📦 Type: [yellow]{component.resource_type}[/yellow]")

#         if show_locations:
#             branch.add(
#                 f"📄 File: [dim]{component.file_path}:{component.line_number}[/dim]"
#             )

#         # Enhanced metadata
#         if show_metadata:
#             _add_metadata_to_branch(branch, component)

#         # Dependencies
#         if show_dependencies and component.dependencies:
#             dep_branch = branch.add("🔗 Dependencies")
#             for dep in component.dependencies:
#                 dep_obj = project.find_object(dep)
#                 status = "✓" if dep_obj else "✗"
#                 dep_branch.add(f"{status} [blue]{dep}[/blue]")

#         # Dependents
#         if show_dependents:
#             dependents = project.get_dependents(comp_name)
#             if dependents:
#                 dep_branch = branch.add("📤 Dependents")
#                 for dep in dependents:
#                     dep_branch.add(f"• [green]{dep}[/green]")

#         # Attributes
#         if show_attributes and component.attributes:
#             attr_branch = branch.add("⚙️  Attributes")
#             for key, value in list(component.attributes.items())[:5]:  # Show first 5
#                 attr_branch.add(f"[dim]{key}:[/dim] {str(value)[:50]}...")
#             if len(component.attributes) > 5:
#                 attr_branch.add(
#                     f"[dim]... and {len(component.attributes) - 5} more[/dim]"
#                 )

#     console.print(tree)


# def _add_metadata_to_branch(branch, component):
#     """Add enhanced metadata to tree branch."""
#     metadata_added = False

#     if hasattr(component, "provider") and component.provider:
#         branch.add(f"🏭 Provider: [blue]{component.provider}[/blue]")
#         metadata_added = True

#     if hasattr(component, "source") and component.source:
#         branch.add(f"📦 Source: [dim]{component.source}[/dim]")
#         metadata_added = True

#     if hasattr(component, "variable_type") and component.variable_type:
#         branch.add(f"📊 Variable Type: [yellow]{component.variable_type}[/yellow]")
#         metadata_added = True

#     if hasattr(component, "default_value") and component.default_value is not None:
#         branch.add(f"⚡ Default: [green]{component.default_value}[/green]")
#         metadata_added = True

#     if hasattr(component, "description") and component.description:
#         branch.add(f"📝 Description: [white]{component.description}[/white]")
#         metadata_added = True

#     if hasattr(component, "sensitive") and component.sensitive:
#         branch.add("🔒 [red]Sensitive: True[/red]")
#         metadata_added = True

#     if hasattr(component, "alias") and component.alias:
#         branch.add(f"🏷️  Alias: [cyan]{component.alias}[/cyan]")
#         metadata_added = True


# def _display_component_table(
#     project,
#     components,
#     component_type,
#     show_attributes,
#     show_metadata,
#     show_locations,
# ):
#     """Display components in table format."""
#     table = Table(
#         title=f"{component_type.upper()}S ({len(components)} found)",
#         show_header=True,
#         border_style="green",
#     )

#     # Base columns
#     table.add_column("Name", style="cyan")

#     if component_type in ["resource", "data"]:
#         table.add_column("Type", style="yellow")
#         table.add_column("Provider", style="blue")
#     elif component_type == "module":
#         table.add_column("Source", style="dim", max_width=30)

#     if show_locations:
#         table.add_column("File:Line", style="dim")

#     # Enhanced metadata columns
#     if show_metadata:
#         if component_type == "variable":
#             table.add_column("Type", style="yellow")
#             table.add_column("Default", style="green")
#         elif component_type == "output":
#             table.add_column("Description", style="white", max_width=30)
#             table.add_column("Sensitive", style="red")

#     if show_attributes:
#         table.add_column("Attributes", style="dim", justify="right")

#     # Add rows
#     for comp_name, component in components.items():
#         row = [comp_name]

#         if component_type in ["resource", "data"]:
#             row.extend([component.resource_type or "", component.provider or ""])
#         elif component_type == "module":
#             row.append(component.source or "")

#         if show_locations:
#             row.append(f"{Path(component.file_path).name}:{component.line_number}")

#         if show_metadata:
#             if component_type == "variable":
#                 row.extend(
#                     [
#                         component.variable_type or "",
#                         str(component.default_value)
#                         if component.default_value is not None
#                         else "",
#                     ]
#                 )
#             elif component_type == "output":
#                 row.extend(
#                     [component.description or "", "🔒" if component.sensitive else ""]
#                 )

#         if show_attributes:
#             row.append(str(len(component.attributes)))

#         table.add_row(*row)

#     console.print(table)


# def _display_component_json(project, components, component_type):
#     """Display components in JSON format."""
#     from dataclasses import asdict

#     output = {
#         "component_type": component_type,
#         "count": len(components),
#         "components": {
#             name: asdict(component) for name, component in components.items()
#         },
#         "project_metadata": project.metadata,
#     }
#     console.print(json.dumps(output, indent=2, default=str))


# def _display_component_yaml(project, components, component_type):
#     """Display components in YAML format."""
#     from dataclasses import asdict

#     try:
#         import yaml

#         output = {
#             "component_type": component_type,
#             "count": len(components),
#             "components": {
#                 name: asdict(component) for name, component in components.items()
#             },
#             "project_metadata": project.metadata,
#         }
#         console.print(yaml.dump(output, default_flow_style=False))
#     except ImportError:
#         console.print(
#             "[yellow]YAML output requires PyYAML package. Falling back to JSON.[/yellow]"
#         )
#         _display_component_json(project, components, component_type)


# def _display_component_detailed(
#     project,
#     components,
#     component_type,
#     show_dependencies,
#     show_dependents,
#     show_references,
#     show_attributes,
#     show_metadata,
#     show_locations,
# ):
#     for comp_name, component in components.items():
#         console.print(
#             Panel.fit(
#                 f"[bold cyan]{comp_name}[/bold cyan] ([dim]{component.type.value}[/dim])",
#                 border_style="green",
#             )
#         )

#         # Basic information
#         info_text = Text()
#         info_text.append("📍 ", style="bold")
#         info_text.append(f"{component.file_path}:{component.line_number}\n")

#         if hasattr(component, "resource_type") and component.resource_type:
#             info_text.append("📦 ", style="bold")
#             info_text.append(f"Type: {component.resource_type}\n")

#         # Enhanced metadata
#         if show_metadata:
#             _add_metadata_to_text(info_text, component)

#         console.print(info_text)

#         # Dependencies and dependents
#         if show_dependencies and component.dependencies:
#             console.print("🔗 [bold]Dependencies:[/bold]")
#             for dep in component.dependencies:
#                 dep_obj = project.find_object(dep)
#                 status = "✓" if dep_obj else "✗"
#                 console.print(f"   {status} {dep}")
#             console.print()

#         if show_dependents:
#             dependents = project.get_dependents(comp_name)
#             if dependents:
#                 console.print("📤 [bold]Dependents:[/bold]")
#                 for dep in dependents:
#                     console.print(f"   • {dep}")
#                 console.print()

#         # References (if show_references is used)
#         if show_references:
#             # You can implement references display here if needed
#             console.print("🔗 [bold]References:[/bold]")
#             console.print("   [dim]References display not yet implemented[/dim]")
#             console.print()

#         # Attributes
#         if show_attributes and component.attributes:
#             console.print("⚙️  [bold]Attributes:[/bold]")
#             for key, value in component.attributes.items():
#                 value_str = str(value)
#                 if len(value_str) > 100:
#                     value_str = value_str[:100] + "..."
#                 console.print(f"   [dim]{key}:[/dim] {value_str}")

#         console.print()  # Spacing between components


# def _add_metadata_to_text(text: Text, component):
#     """Add enhanced metadata to text output."""
#     metadata_fields = [
#         ("provider", "🏭 Provider: ", "blue"),
#         ("source", "📦 Source: ", "dim"),
#         ("variable_type", "📊 Type: ", "yellow"),
#         ("default_value", "⚡ Default: ", "green"),
#         ("description", "📝 Description: ", "white"),
#         ("alias", "🏷️  Alias: ", "cyan"),
#     ]

#     for field, prefix, style in metadata_fields:
#         if hasattr(component, field) and getattr(component, field):
#             value = getattr(component, field)
#             if field == "sensitive" and value:
#                 text.append("🔒 ", style="bold red")
#                 text.append("Sensitive: True\n", style="red")
#             else:
#                 text.append(prefix, style="bold")
#                 text.append(f"{value}\n", style=style)


# def _prepare_export_data(project, components, component_type):
#     """Prepare data for export."""
#     from dataclasses import asdict

#     return {
#         "export_timestamp": str(datetime.now()),
#         "project_path": project.metadata.get("project_path", ""),
#         "component_type": component_type,
#         "components": {
#             name: asdict(component) for name, component in components.items()
#         },
#         "project_metadata": project.metadata,
#         "analysis_metadata": {
#             "total_components": len(components),
#             "export_format": "enhanced",
#         },
#     }


# ============================================================================
# REPORT COMMAND - Generate Reports
# ============================================================================


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--type",
    "-t",
    "report_type",
    type=click.Choice(
        ["summary", "detailed", "security", "cost", "compliance", "custom"],
        case_sensitive=False,
    ),
    default="summary",
    help="Report type",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "pdf", "markdown", "json"], case_sensitive=False),
    default="html",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path"
)
@click.option("--title", help="Custom report title")
@click.option("--template", type=click.Path(exists=True), help="Custom template file")
@click.option(
    "--include-graph", "-g", is_flag=True, help="Include resource dependency graph"
)
@click.option("--include-metrics", "-m", is_flag=True, help="Include detailed metrics")
@click.option(
    "--interactive", "-i", is_flag=True, help="Generate interactive HTML report"
)
@click.option("--open", "-O", is_flag=True, help="Open report after generation")
@click.option(
    "--theme",
    type=click.Choice(["light", "dark", "cyber", "nord"], case_sensitive=False),
    default="dark",
    help="Report theme",
)
def report(
    path,
    report_type,
    format,
    output,
    title,
    template,
    include_graph,
    include_metrics,
    interactive,
    open,
    theme,
):
    """Generate comprehensive reports from Terraform analysis.

    Create detailed reports in multiple formats with customizable
    content and styling options.

    \b
    Report Types:
      summary      High-level overview (default)
      detailed     Comprehensive analysis
      security     Security and compliance focus
      cost         Cost analysis and optimization
      compliance   Compliance and best practices
      custom       Use custom template

    \b
    Output Formats:
      html         Interactive HTML (default)
      pdf          PDF document (requires wkhtmltopdf)
      markdown     Markdown document
      json         Structured JSON data

    \b
    Examples:
      # Generate summary report
      tfkit report

      # Detailed interactive report
      tfkit report --type detailed --interactive --open

      # Security report with graph
      tfkit report --type security --include-graph -o security.html

      # Custom styled report
      tfkit report --title "Production Infrastructure" --theme dark

      # PDF report with metrics
      tfkit report --format pdf --include-metrics -o infra-report.pdf
    """
    print_banner(show_version=False)
    console.print(f"[bold]📊 Generating {report_type.upper()} Report[/bold]")
    console.print(f"   Format: [cyan]{format.upper()}[/cyan]")
    console.print(f"   Theme: [yellow]{theme}[/yellow]")
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing project...", total=None)

            analyzer = TerraformAnalyzer()
            project = analyzer.analyze_project(path)

            progress.update(task, description="Generating report content...")

            report_file = _generate_report(
                project,
                report_type,
                format,
                output,
                title,
                template,
                include_graph,
                include_metrics,
                interactive,
                theme,
            )

            progress.update(task, description="✓ Report generation complete")

        console.print(f"\n✓ Report generated: [green]{report_file}[/green]")
        console.print(f"   Type: [cyan]{report_type}[/cyan]")
        console.print(
            f"   Size: [yellow]{report_file.stat().st_size / 1024:.1f} KB[/yellow]"
        )

        if open:
            import webbrowser

            webbrowser.open(f"file://{report_file.resolve()}")
            console.print("   🌐 Opened in browser")

    except Exception as e:
        console.print(f"\n[red]✗ Report generation failed:[/red] {e}")
        sys.exit(1)


# ============================================================================
# EXPORT COMMAND - Data Export
# ============================================================================


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--format",
    "-f",
    "formats",
    multiple=True,
    type=click.Choice(["json", "yaml", "csv", "xml", "toml"], case_sensitive=False),
    help="Export formats (can specify multiple)",
)
@click.option(
    "--output-dir", "-o", type=click.Path(path_type=Path), help="Output directory"
)
@click.option("--prefix", "-p", default="tfkit-export", help="Output filename prefix")
@click.option(
    "--split-by",
    type=click.Choice(["type", "provider", "module"], case_sensitive=False),
    help="Split exports by category",
)
@click.option("--include", multiple=True, help="Include specific components")
@click.option("--exclude", multiple=True, help="Exclude specific components")
@click.option("--compress", "-c", is_flag=True, help="Compress output files")
def export(path, formats, output_dir, prefix, split_by, include, exclude, compress):
    """Export analysis data in multiple formats.

    Export Terraform analysis data in various structured formats
    for integration with other tools and workflows.

    \b
    Supported Formats:
      json    JSON format (standard)
      yaml    YAML format (human-readable)
      csv     CSV format (spreadsheet-compatible)
      xml     XML format (legacy systems)
      toml    TOML format (config files)

    \b
    Examples:
      # Export as JSON and YAML
      tfkit export --format json --format yaml

      # Export to specific directory
      tfkit export -f json -o ./exports

      # Split by provider
      tfkit export -f csv --split-by provider

      # Export with compression
      tfkit export -f json -f yaml --compress

      # Custom prefix
      tfkit export -f json --prefix infrastructure
    """
    if not formats:
        formats = ("json",)

    print_banner(show_version=False)
    console.print("[bold]📦 Export Data[/bold]")
    console.print(f"   Formats: [cyan]{', '.join(formats)}[/cyan]")
    if split_by:
        console.print(f"   Split by: [yellow]{split_by}[/yellow]")
    console.print()

    try:
        analyzer = TerraformAnalyzer()
        project = analyzer.analyze_project(path)

        output_dir = output_dir or Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = []

        for fmt in formats:
            if split_by:
                files = _export_split(project, fmt, output_dir, prefix, split_by)
                exported_files.extend(files)
            else:
                file = _export_single(project, fmt, output_dir, prefix)
                exported_files.append(file)

            console.print(f"   ✓ Exported as {fmt.upper()}")

        if compress:
            console.print("\n[dim]Compressing files...[/dim]")
            import zipfile

            zip_path = (
                output_dir / f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
            )
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in exported_files:
                    zipf.write(file, file.name)
                    file.unlink()
            console.print(f"   ✓ Compressed to: [green]{zip_path}[/green]")
        else:
            console.print(f"\n[bold]Exported files:[/bold]")
            for file in exported_files:
                console.print(f"   • [green]{file}[/green]")

    except Exception as e:
        console.print(f"\n[red]✗ Export failed:[/red] {e}")
        sys.exit(1)


# ============================================================================
# VALIDATE COMMAND - Configuration Validation
# ============================================================================


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--strict", "-s", is_flag=True, help="Enable strict validation mode")
@click.option("--check-syntax", is_flag=True, help="Check HCL syntax")
@click.option("--check-references", is_flag=True, help="Validate references")
@click.option(
    "--check-best-practices", is_flag=True, help="Check against best practices"
)
@click.option("--check-security", is_flag=True, help="Security validation")
@click.option("--fail-on-warning", is_flag=True, help="Treat warnings as errors")
@click.option("--ignore", multiple=True, help="Ignore specific validation rules")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "sarif"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--all", "-a", is_flag=True, help="Run all validation checks")
def validate(
    path,
    strict,
    check_syntax,
    check_references,
    check_best_practices,
    check_security,
    fail_on_warning,
    ignore,
    format,
    all,
):
    """Validate Terraform configurations.

    Perform comprehensive validation of Terraform configurations
    including syntax, references, best practices, and security.

    \b
    Validation Checks:
      --check-syntax           HCL syntax validation
      --check-references       Reference validation
      --check-best-practices   Best practices compliance
      --check-security         Security configuration checks
      --all, -a               Run all validation checks

    \b
    Examples:
      # Basic validation
      tfkit validate

      # Full validation with all checks
      tfkit validate --all

      # Specific checks
      tfkit validate --check-syntax --check-references --check-security

      # Strict mode with best practices
      tfkit validate --strict --check-best-practices

      # Export validation results
      tfkit validate --all --format json > validation.json

      # CI/CD mode
      tfkit validate --all --strict --fail-on-warning

      # Ignore specific rules
      tfkit validate --all --ignore TF020 --ignore TF021
    """
    print_banner(show_version=False)
    console.print("[bold]✓ Validating Configuration[/bold]")
    console.print(f"   Path: [cyan]{path.resolve()}[/cyan]")
    if strict:
        console.print("   Mode: [yellow]STRICT[/yellow]")
    if ignore:
        console.print(f"   Ignoring rules: [dim]{', '.join(ignore)}[/dim]")
    console.print()

    if all:
        check_syntax = True
        check_references = True
        check_best_practices = True
        check_security = True

    if not any([check_syntax, check_references, check_best_practices, check_security]):
        check_syntax = True
        check_references = True

    try:
        with console.status("[bold cyan]Analyzing Terraform project..."):
            analyzer = TerraformAnalyzer()
            project = analyzer.analyze_project(str(path))

        console.print(
            f"[green]✓[/green] Found {len(project.resources)} resources, "
            f"{len(project.modules)} modules, {len(project.variables)} variables"
        )
        console.print()

        validator = TerraformValidator(strict=strict, ignore_rules=list(ignore))

        if check_syntax:
            console.print("   🔍 Checking syntax...")
        if check_references:
            console.print("   🔗 Validating references...")
        if check_best_practices:
            console.print("   📋 Checking best practices...")
        if check_security:
            console.print("   🔒 Security validation...")

        console.print()

        result = validator.validate(
            project,
            check_syntax=check_syntax,
            check_references=check_references,
            check_best_practices=check_best_practices,
            check_security=check_security,
        )

        if format == "table":
            _display_validation_results_table(result)
        elif format == "json":
            _display_validation_results_json(result)
        elif format == "sarif":
            _display_validation_results_sarif(result, path)

        exit_code = 0
        if result.has_errors:
            exit_code = 1
        elif fail_on_warning and result.has_warnings:
            exit_code = 1

        if exit_code == 0:
            console.print()
            console.print(
                "[bold green]✓ Validation completed successfully[/bold green]"
            )
        else:
            console.print()
            console.print("[bold red]✗ Validation failed[/bold red]")

        sys.exit(exit_code)

    except ImportError as e:
        console.print(f"\n[red]✗ Missing dependency:[/red] {e}")
        console.print(
            "\n[yellow]Install required dependencies:[/yellow] pip install python-hcl2"
        )
        sys.exit(1)
    except ValueError as e:
        console.print(f"\n[red]✗ Validation error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ Validation failed:[/red] {e}")
        if strict:
            raise
        sys.exit(1)


def _display_validation_results_table(result):
    """Display validation results in table format."""
    summary = result.get_summary()

    summary_text = Text()
    if summary["errors"] > 0:
        summary_text.append(f"Errors: {summary['errors']} ", style="bold red")
    else:
        summary_text.append(f"Errors: {summary['errors']} ", style="bold green")

    if summary["warnings"] > 0:
        summary_text.append(f"Warnings: {summary['warnings']} ", style="bold yellow")
    else:
        summary_text.append(f"Warnings: {summary['warnings']} ", style="bold green")

    if summary["info"] > 0:
        summary_text.append(f"Info: {summary['info']} ", style="bold blue")
    else:
        summary_text.append(f"Info: {summary['info']} ", style="bold green")

    summary_text.append(f"Passed: {summary['total_checks']}", style="bold green")

    console.print(Panel(summary_text, title="Validation Summary", border_style="cyan"))
    console.print()

    all_issues = result.errors + result.warnings + result.info

    if all_issues:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Severity", width=10)
        table.add_column("Category", width=15)
        table.add_column("Rule", width=12)
        table.add_column("Location", width=25)
        table.add_column("Resource", width=20)
        table.add_column("Message", style="white")

        for issue in all_issues:
            severity_style = {
                ValidationSeverity.ERROR: ("red", "❌"),
                ValidationSeverity.WARNING: ("yellow", "⚠️"),
                ValidationSeverity.INFO: ("blue", "ℹ️"),
            }.get(issue.severity, ("white", ""))

            color, icon = severity_style
            severity_text = Text(f"{icon} {issue.severity.value.upper()}", style=color)

            location = f"{issue.file_path}:{issue.line_number}"

            resource_name = issue.resource_name or ""

            table.add_row(
                severity_text,
                issue.category.value,
                issue.rule_id,
                location,
                resource_name,
                issue.message,
            )

        console.print(table)

        issues_with_suggestions = [issue for issue in all_issues if issue.suggestion]
        if issues_with_suggestions:
            console.print()
            console.print("[bold]💡 Suggestions:[/bold]")
            for issue in issues_with_suggestions:
                console.print(f"  • [cyan]{issue.suggestion}[/cyan]")
    else:
        console.print("🎉 [bold green]No validation issues found![/bold green]")

    if result.passed:
        console.print()
        console.print(f"✅ [green]{len(result.passed)} checks passed[/green]")


def _display_validation_results_json(result):
    """Display validation results in JSON format."""
    output = {
        "summary": result.get_summary(),
        "passed_checks": result.passed,
        "issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category.value,
                "rule_id": issue.rule_id,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "resource_name": issue.resource_name,
                "message": issue.message,
                "suggestion": issue.suggestion,
            }
            for issue in result.errors + result.warnings + result.info
        ],
    }
    console.print(json.dumps(output, indent=2))


def _display_validation_results_sarif(result, base_path):
    """Display validation results in SARIF format."""
    sarif_output = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "tfkit",
                        "informationUri": "https://github.com/your-org/tfkit",
                        "rules": [],
                    }
                },
                "results": [],
            }
        ],
    }

    all_issues = result.errors + result.warnings + result.info

    for issue in all_issues:
        try:
            if base_path and Path(issue.file_path).is_relative_to(base_path):
                file_uri = str(Path(issue.file_path).relative_to(base_path))
            else:
                file_uri = issue.file_path
        except (ValueError, TypeError):
            file_uri = issue.file_path

        result_entry = {
            "ruleId": issue.rule_id,
            "level": {
                ValidationSeverity.ERROR: "error",
                ValidationSeverity.WARNING: "warning",
                ValidationSeverity.INFO: "note",
            }.get(issue.severity, "none"),
            "message": {"text": issue.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": file_uri},
                        "region": {"startLine": issue.line_number},
                    }
                }
            ],
            "properties": {
                "category": issue.category.value,
                "resourceName": issue.resource_name or "",
            },
        }

        if issue.suggestion:
            result_entry["message"]["text"] += f"\nSuggestion: {issue.suggestion}"

        sarif_output["runs"][0]["results"].append(result_entry)

    console.print(json.dumps(sarif_output, indent=2))


# ============================================================================
# UTILITY COMMANDS
# ============================================================================


@cli.command()
def examples():
    """Show comprehensive usage examples and patterns.

    Display common usage patterns, workflows, and advanced
    examples for different scenarios.
    """
    print_banner()

    examples_content = """
[bold yellow]🚀 Quick Start Workflows[/bold yellow]

  [bold]1. Fast Project Scan[/bold]
     tfkit scan
     tfkit scan --format json --save results.json
  
  [bold]2. Full Analysis[/bold]
     tfkit analyze --deep --open-browser
     tfkit analyze -d -D -S -C -o ./reports
  
  [bold]3. Generate Reports[/bold]
     tfkit report --type detailed --interactive
     tfkit report --type security --format pdf

[bold yellow]📊 Advanced Analysis Patterns[/bold yellow]

  [bold]Deep Dive with All Features:[/bold]
  $ tfkit analyze --deep \\
      --include-dependencies \\
      --include-security \\
      --include-costs \\
      --export-json full-analysis.json \\
      --export-markdown report.md \\
      --open-browser

  [bold]Filtered Analysis:[/bold]
  $ tfkit analyze \\
      --providers aws azure \\
      --exclude "*.test.tf" \\
      --tags production \\
      --threads 8

  [bold]Multi-Format Export:[/bold]
  $ tfkit export \\
      --format json --format yaml --format csv \\
      --split-by provider \\
      --compress

[bold yellow]🔍 Inspection Examples[/bold yellow]

  [bold]Inspect Resources:[/bold]
  $ tfkit inspect resource --name aws_instance.web --show-dependencies
  $ tfkit inspect resource --type aws_s3_bucket --format table
  
  [bold]Module Analysis:[/bold]
  $ tfkit inspect module --show-attributes --format detailed
  
  [bold]Provider Investigation:[/bold]
  $ tfkit inspect provider --show-references

[bold yellow]📋 Reporting Scenarios[/bold yellow]

  [bold]Executive Summary:[/bold]
  $ tfkit report --type summary --format pdf -o executive-report.pdf
  
  [bold]Security Audit:[/bold]
  $ tfkit report --type security --include-graph --include-metrics
  
  [bold]Cost Analysis:[/bold]
  $ tfkit report --type cost --format html --theme dark --open

[bold yellow]✓ Validation & CI/CD[/bold yellow]

  [bold]Pre-commit Hook:[/bold]
  $ tfkit validate --check-syntax --check-references --fail-on-warning
  
  [bold]Full Validation Pipeline:[/bold]
  $ tfkit validate --strict \\
      --check-syntax \\
      --check-references \\
      --check-best-practices \\
      --check-security \\
      --format sarif > results.sarif

  [bold]CI/CD Integration:[/bold]
  $ tfkit scan --quiet --format json --save scan-results.json
  $ tfkit analyze --quiet --export-json analysis.json

[bold yellow]🔧 Workflow Combinations[/bold yellow]

  [bold]Complete Analysis Pipeline:[/bold]
  $ tfkit scan --save initial-scan.json
  $ tfkit analyze --deep -D -S -C --export-json detailed.json
  $ tfkit report --type detailed --include-graph --open
  $ tfkit export --format json --format yaml --compress

  [bold]Security-Focused Workflow:[/bold]
  $ tfkit analyze --include-security --export-json security-data.json
  $ tfkit validate --check-security --strict
  $ tfkit report --type security --format pdf

  [bold]Cost Optimization Workflow:[/bold]
  $ tfkit analyze --include-costs --export-csv costs.csv
  $ tfkit report --type cost --include-metrics
  $ tfkit inspect resource --filter cost>100

[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]

[dim]For detailed command help: tfkit COMMAND --help
For configuration options: tfkit config --help[/dim]
"""

    console.print(Panel(examples_content, border_style="cyan", padding=(1, 2)))


@cli.command()
@click.option("--show", "-s", is_flag=True, help="Show current configuration")
@click.option("--set", "set_key", help="Set configuration key=value")
@click.option("--reset", is_flag=True, help="Reset to defaults")
@click.option("--edit", is_flag=True, help="Open config in editor")
def config(show, set_key, reset, edit):
    """Manage TFKIT configuration settings.

    Configure default behaviors, output preferences, and
    integration settings for TFKIT.

    \b
    Examples:
      tfkit config --show                    # Show current config
      tfkit config --set theme=dark          # Set theme
      tfkit config --set default_format=json # Set default format
      tfkit config --reset                   # Reset to defaults
      tfkit config --edit                    # Edit in $EDITOR
    """
    print_banner(show_version=False)

    config_file = Path.home() / ".tfkit" / "config.json"

    if show or (not set_key and not reset and not edit):
        if config_file.exists():
            with config_file.open() as f:
                cfg = json.load(f)

            table = Table(
                title="TFKIT Configuration", show_header=True, border_style="cyan"
            )
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            for key, value in cfg.items():
                table.add_row(key, str(value))

            console.print(table)
            console.print(f"\n[dim]Config file: {config_file}[/dim]")
        else:
            console.print("[yellow]⚠[/yellow]  No configuration file found")
            console.print(f"   Run 'tfkit config --set KEY=VALUE' to create one")

    elif set_key:
        if "=" not in set_key:
            console.print("[red]✗[/red] Invalid format. Use: KEY=VALUE")
            sys.exit(1)

        key, value = set_key.split("=", 1)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        cfg = {}
        if config_file.exists():
            with config_file.open() as f:
                cfg = json.load(f)

        cfg[key] = value

        with config_file.open("w") as f:
            json.dump(cfg, f, indent=2)

        console.print(f"✓ Set [cyan]{key}[/cyan] = [green]{value}[/green]")

    elif reset:
        if config_file.exists():
            config_file.unlink()
        console.print("✓ Configuration reset to defaults")


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def info(path):
    """Display comprehensive system and project information.

    Show detailed information about the Terraform project,
    TFKIT installation, and system environment.
    """
    print_banner()

    import platform

    system_table = Table(
        title="System Information", show_header=False, border_style="blue"
    )
    system_table.add_column("Property", style="cyan")
    system_table.add_column("Value", style="white")

    system_table.add_row("TFKIT Version", __version__)
    system_table.add_row("Python Version", platform.python_version())
    system_table.add_row("Platform", platform.platform())
    system_table.add_row("Machine", platform.machine())

    console.print(system_table)
    console.print()


def show_version_info():
    """Display detailed version information."""
    import platform

    from tfkit import __version__

    print_banner()

    version_panel = Panel(
        f"""[bold cyan]TFKIT Version:[/bold cyan] {__version__}
[bold cyan]Python:[/bold cyan] {platform.python_version()}
[bold cyan]Platform:[/bold cyan] {platform.system()} {platform.release()}
[bold cyan]Architecture:[/bold cyan] {platform.machine()}

[dim]Terraform Intelligence & Analysis Suite
Advanced infrastructure code analysis and visualization
https://github.com/ivasik-k7/tfkit[/dim]""",
        title="Version Information",
        border_style="blue",
        padding=(1, 2),
    )

    console.print(version_panel)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


# def _display_scan_results(project, quiet):
#     """Display quick scan results."""
#     stats = _get_scan_data(project)

#     table = Table(title="", show_header=True, border_style="cyan")
#     table.add_column("Component", style="cyan", width=20)
#     table.add_column("Count", justify="right", style="green", width=10)
#     table.add_column("Status", style="white", width=15)

#     table.add_row("Resources", str(stats["resources"]), "✓ Analyzed")
#     table.add_row("Data Sources", str(stats["data_sources"]), "✓ Analyzed")
#     table.add_row("Modules", str(stats["modules"]), "✓ Analyzed")
#     table.add_row("Variables", str(stats["variables"]), "✓ Analyzed")
#     table.add_row("Outputs", str(stats["outputs"]), "✓ Analyzed")
#     table.add_row("Providers", str(stats["providers"]), "✓ Detected")

#     console.print(table)


# def _display_simple_results(project):
#     stats = _get_scan_data(project)
#     console.print(f"Resources: {stats['resources']}")
#     console.print(f"Modules: {stats['modules']}")
#     console.print(f"Variables: {stats['variables']}")
#     console.print(f"Outputs: {stats['outputs']}")
#     console.print(f"Providers: {stats['providers']}")
#     console.print(f"Total: {stats['total']}")


# def _display_detailed_analysis_summary(
#     project, deep, include_dependencies, include_security, include_costs, verbose
# ):
#     """Display comprehensive analysis summary."""

#     main_table = Table(
#         title="📊 Analysis Summary",
#         show_header=True,
#         header_style="bold cyan",
#         border_style="blue",
#         box=box.ROUNDED,
#     )
#     main_table.add_column("Category", style="cyan", width=25)
#     main_table.add_column("Count", justify="right", style="green", width=10)
#     main_table.add_column("Details", style="dim", width=40)

#     stats = _get_scan_data(project)

#     main_table.add_row(
#         "Resources",
#         str(stats["resources"]),
#         _get_resource_breakdown(project) if verbose else "",
#     )
#     main_table.add_row("Data Sources", str(stats["data_sources"]), "")
#     main_table.add_row(
#         "Modules",
#         str(stats["modules"]),
#         _get_module_summary(project) if verbose else "",
#     )
#     main_table.add_row("Variables", str(stats["variables"]), "")
#     main_table.add_row("Outputs", str(stats["outputs"]), "")
#     main_table.add_row(
#         "Providers",
#         str(stats["providers"]),
#         ", ".join(list(project.providers.keys())[:5]),
#     )

#     console.print(main_table)

#     # Feature summary
#     if deep or include_dependencies or include_security or include_costs:
#         console.print()
#         features_table = Table(
#             title="🎯 Enabled Features",
#             show_header=False,
#             border_style="green",
#             box=box.SIMPLE,
#         )
#         features_table.add_column("Feature", style="cyan")
#         features_table.add_column("Status", style="green")

#         if deep:
#             features_table.add_row("Deep Analysis", "✓ Enabled")
#         if include_dependencies:
#             features_table.add_row("Dependency Tracking", "✓ Enabled")
#         if include_security:
#             features_table.add_row("Security Analysis", "✓ Enabled")
#         if include_costs:
#             features_table.add_row("Cost Estimation", "✓ Enabled")

#         console.print(features_table)


def _get_resource_breakdown(project):
    """Get resource type breakdown."""
    resource_types = {}
    for res_id, res in project.resources.items():
        res_type = res.get("type", "unknown")
        resource_types[res_type] = resource_types.get(res_type, 0) + 1

    if resource_types:
        top = sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3]
        return ", ".join([f"{t}: {c}" for t, c in top])
    return ""


def _get_module_summary(project):
    """Get module summary."""
    if project.modules:
        return f"{len(project.modules)} modules detected"
    return ""


def _get_components_by_type(project, component_type, name, resource_type, filters):
    """Get components by type with filtering."""
    components = {}

    if component_type == "resource":
        components = project.resources
    elif component_type == "module":
        components = project.modules
    elif component_type == "variable":
        components = project.variables
    elif component_type == "output":
        components = project.outputs
    elif component_type == "provider":
        components = project.providers
    elif component_type == "data":
        components = project.data_sources

    # Filter by name
    if name:
        components = {k: v for k, v in components.items() if name in k}

    # Filter by type
    if resource_type:
        components = {
            k: v for k, v in components.items() if v.get("type") == resource_type
        }

    return components


def _display_component_tree(
    components,
    component_type,
    show_dependencies,
    show_references,
    show_attributes,
):
    """Display components as tree."""
    tree = Tree(f"[bold cyan]{component_type.upper()}S[/bold cyan]")

    for name, comp in list(components.items())[:20]:  # Limit to 20
        branch = tree.add(f"[green]{name}[/green]")

        if isinstance(comp, dict):
            if "type" in comp:
                branch.add(f"[dim]Type: {comp['type']}[/dim]")
            if show_attributes:
                attrs = branch.add("[yellow]Attributes[/yellow]")
                for key, value in list(comp.items())[:5]:
                    if key != "type":
                        attrs.add(f"{key}: {str(value)[:50]}")

    console.print(tree)


def _display_component_table(components, component_type, show_attributes):
    """Display components as table."""
    table = Table(
        title=f"{component_type.upper()} List", show_header=True, border_style="cyan"
    )
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")

    if show_attributes:
        table.add_column("Attributes", style="dim", max_width=40)

    for name, comp in list(components.items())[:50]:
        comp_type = comp.get("type", "N/A") if isinstance(comp, dict) else "N/A"

        if show_attributes and isinstance(comp, dict):
            attrs = ", ".join([f"{k}" for k in list(comp.keys())[:5]])
            table.add_row(name, comp_type, attrs)
        else:
            table.add_row(name, comp_type)

    console.print(table)


def _export_yaml(data):
    """Export data as YAML."""
    try:
        import yaml

        console.print(yaml.dump(data, default_flow_style=False))
    except ImportError:
        console.print(
            "[red]✗[/red] PyYAML not installed. Install with: pip install pyyaml"
        )


def _export_yaml_file(data, filepath):
    """Export data to YAML file."""
    try:
        import yaml

        with filepath.open("w") as f:
            yaml.dump(data, f, default_flow_style=False)
    except ImportError:
        console.print("[yellow]⚠[/yellow] PyYAML not installed. Skipping YAML export.")


def _export_markdown_report(project, filepath, include_security, include_costs):
    """Export Markdown report."""
    # report = f"# Terraform Project Analysis\n\n"
    # report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    # report += f"## Summary\n\n"
    # stats = _get_scan_data(project)
    # report += f"- Resources: {stats['resources']}\n"
    # report += f"- Modules: {stats['modules']}\n"
    # report += f"- Variables: {stats['variables']}\n"
    # report += f"- Outputs: {stats['outputs']}\n"
    # report += f"- Providers: {stats['providers']}\n"

    # with filepath.open("w") as f:
    #     f.write(report)


def _export_csv_resources(project, filepath):
    """Export resources as CSV."""
    import csv

    with filepath.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Type", "Provider"])

        for name, res in project.resources.items():
            res_type = res.get("type", "")
            provider = res_type.split("_")[0] if "_" in res_type else ""
            writer.writerow([name, res_type, provider])


def _apply_provider_filter(project, providers):
    """Filter project by providers."""
    filtered_resources = {}
    for name, res in project.resources.items():
        res_type = res.get("type", "")
        provider = res_type.split("_")[0] if "_" in res_type else ""
        if provider in providers:
            filtered_resources[name] = res
    project.resources = filtered_resources


def _generate_report(
    project,
    report_type,
    format,
    output,
    title,
    template,
    include_graph,
    include_metrics,
    interactive,
    theme,
):
    """Generate report file."""
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = Path(f"tfkit-{report_type}-report-{timestamp}.{format}")

    if format == "html":
        generator = ReportGenerator()
        html_file = generator.generate_visualization(project, output.parent)
        return html_file
    elif format == "markdown":
        _export_markdown_report(project, output, False, False)
        return output
    else:
        # Default to JSON
        with output.open("w") as f:
            json.dump(project.to_dict(), f, indent=2, default=str)
        return output


def _export_single(project, format, output_dir, prefix):
    """Export project data in single format."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filepath = output_dir / f"{prefix}-{timestamp}.{format}"

    if format == "json":
        with filepath.open("w") as f:
            json.dump(project.to_dict(), f, indent=2, default=str)
    elif format == "yaml":
        _export_yaml_file(project.to_dict(), filepath)
    elif format == "csv":
        _export_csv_resources(project, filepath)

    return filepath


def _export_split(project, format, output_dir, prefix, split_by):
    """Export project data split by category."""
    files = []
    # Simplified: just export as single for now
    files.append(_export_single(project, format, output_dir, f"{prefix}-all"))
    return files


def _display_validation_results(results):
    """Display validation results."""
    # Passed checks
    if results["passed"]:
        passed_table = Table(
            title="✓ Passed Checks", border_style="green", show_header=False
        )
        passed_table.add_column("Check", style="green")
        for check in results["passed"]:
            passed_table.add_row(f"✓ {check}")
        console.print(passed_table)
        console.print()

    # Warnings
    if results["warnings"]:
        warn_table = Table(title="⚠ Warnings", border_style="yellow", show_header=False)
        warn_table.add_column("Warning", style="yellow")
        for warning in results["warnings"]:
            warn_table.add_row(f"⚠ {warning}")
        console.print(warn_table)
        console.print()

    # Errors
    if results["errors"]:
        error_table = Table(title="✗ Errors", border_style="red", show_header=False)
        error_table.add_column("Error", style="red")
        for error in results["errors"]:
            error_table.add_row(f"✗ {error}")
        console.print(error_table)

    # Summary
    summary = f"\n[bold]Validation Complete:[/bold] "
    summary += f"[green]{len(results['passed'])} passed[/green], "
    summary += f"[yellow]{len(results['warnings'])} warnings[/yellow], "
    summary += f"[red]{len(results['errors'])} errors[/red]"
    console.print(summary)


def _export_sarif(results):
    """Export validation results in SARIF format."""
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "TFKIT", "version": __version__}},
                "results": [],
            }
        ],
    }
    console.print(json.dumps(sarif, indent=2))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main CLI entry point with error handling."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠[/yellow]  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error:[/red] {e}")
        console.print("\n[dim]Run with --debug for detailed traceback[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
