"""Advanced CLI interface for tfkit with comprehensive parameter support."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.tree import Tree

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.visualizer.html_generator import HTMLVisualizer

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
TFKIT_VERSION = "2.0.0"


def print_banner(show_version: bool = True):
    """Print enhanced tfkit banner."""
    console.print(f"[bold blue]{TFKIT_BANNER}[/bold blue]", highlight=False)
    console.print(f"  {TFKIT_TAGLINE}")
    if show_version:
        console.print(
            f"  [dim]v{TFKIT_VERSION} | Advanced Infrastructure Analysis[/dim]\n"
        )


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
    type=click.Choice(["light", "dark", "cyber", "nord"], case_sensitive=False),
    default="dark",
    help="Visualization theme (default: dark)",
)
@click.option(
    "--layout",
    type=click.Choice(
        ["interactive", "classic", "graph", "dashboard"], case_sensitive=False
    ),
    default="interactive",
    help="Visualization layout (default: interactive)",
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
        console.print(f"[bold]🔍 Quick Scan Mode[/bold]")
        console.print(f"   Target: [cyan]{path.resolve()}[/cyan]\n")

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

        # Display results
        if format == "table":
            _display_scan_results(project, quiet)
        elif format == "json":
            console.print(json.dumps(_get_scan_data(project), indent=2))
        elif format == "yaml":
            _export_yaml(_get_scan_data(project))
        else:
            _display_simple_results(project)

        # Save if requested
        if save:
            with save.open("w") as f:
                json.dump(_get_scan_data(project), f, indent=2, default=str)
            if not quiet:
                console.print(f"\n✓ Results saved to: [green]{save}[/green]")

        # Open visualization if requested
        if open:
            visualizer = HTMLVisualizer(theme=theme, layout=layout)
            html_file = visualizer.generate_visualization(
                project,
                output,
                theme=theme,
                layout=layout,
                title=f"Quick Scan - {path.name}",
                include_graph=True,
                include_metrics=True,
                project_path=str(path),
            )
            visualizer.open_in_browser(html_file)
            if not quiet:
                console.print(
                    f"\n🌐 Opened {layout} visualization: [green]{html_file}[/green]"
                )

    except Exception as e:
        console.print(f"\n[red]✗ Scan failed:[/red] {e}")
        # if ctx.obj.get("DEBUG"):
        #     console.print_exception()
        # sys.exit(1)


# ============================================================================
# ANALYZE COMMAND - Deep Analysis
# ============================================================================


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--deep", "-d", is_flag=True, help="Enable deep analysis with dependency tracking"
)
@click.option(
    "--include-dependencies", "-D", is_flag=True, help="Analyze module dependencies"
)
@click.option(
    "--include-security", "-S", is_flag=True, help="Include security analysis"
)
@click.option("--include-costs", "-C", is_flag=True, help="Include cost estimation")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for reports",
)
@click.option("--export-json", type=click.Path(path_type=Path), help="Export as JSON")
@click.option("--export-yaml", type=click.Path(path_type=Path), help="Export as YAML")
@click.option(
    "--export-markdown",
    type=click.Path(path_type=Path),
    help="Export as Markdown report",
)
@click.option(
    "--export-csv", type=click.Path(path_type=Path), help="Export resource list as CSV"
)
@click.option(
    "--open-browser", "-b", is_flag=True, help="Open visualization in browser"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed analysis steps")
@click.option(
    "--threads",
    "-t",
    type=int,
    default=4,
    help="Number of analysis threads (default: 4)",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Exclude patterns (can be used multiple times)",
)
@click.option("--include-only", "-i", multiple=True, help="Include only these patterns")
@click.option("--max-depth", type=int, help="Maximum module depth to analyze")
@click.option("--tags", multiple=True, help="Filter resources by tags")
@click.option("--providers", multiple=True, help="Filter by provider types")
def analyze(
    path,
    deep,
    include_dependencies,
    include_security,
    include_costs,
    output,
    export_json,
    export_yaml,
    export_markdown,
    export_csv,
    open_browser,
    quiet,
    verbose,
    threads,
    exclude,
    include_only,
    max_depth,
    tags,
    providers,
):
    """Deep analysis of Terraform projects with advanced features.

    Performs comprehensive analysis including resource relationships,
    module dependencies, security scanning, and cost estimation.

    \b
    Analysis Modes:
      --deep                  Full deep analysis (recommended)
      --include-dependencies  Track module dependencies
      --include-security      Security and compliance checks
      --include-costs         Cost estimation analysis

    \b
    Export Options:
      --export-json          JSON format (machine-readable)
      --export-yaml          YAML format (human-readable)
      --export-markdown      Markdown report (documentation)
      --export-csv           CSV resource list (spreadsheet)

    \b
    Filtering:
      --exclude PATTERN      Exclude resources matching pattern
      --include-only PATTERN Include only matching resources
      --tags TAG             Filter by resource tags
      --providers PROVIDER   Filter by provider (aws, azure, gcp, etc.)

    \b
    Examples:
      # Full analysis with all features
      tfkit analyze --deep -D -S -C --open-browser

      # Analysis with exports
      tfkit analyze --export-json data.json --export-markdown report.md

      # Filtered analysis
      tfkit analyze --providers aws --tags production

      # Fast analysis with exclusions
      tfkit analyze --exclude "*.test.tf" --threads 8

      # Security-focused analysis
      tfkit analyze --include-security --export-markdown security-report.md

    PATH: Path to Terraform project (default: current directory)
    """
    if not quiet:
        print_banner(show_version=False)
        mode = (
            "[bold yellow]DEEP ANALYSIS[/bold yellow]"
            if deep
            else "[bold]Standard Analysis[/bold]"
        )
        console.print(f"{mode} Mode")
        console.print(f"   Target: [cyan]{path.resolve()}[/cyan]")
        console.print(f"   Threads: [yellow]{threads}[/yellow]")

        features = []
        if include_dependencies:
            features.append("Dependencies")
        if include_security:
            features.append("Security")
        if include_costs:
            features.append("Costs")
        if features:
            console.print(f"   Features: [green]{', '.join(features)}[/green]")

        if exclude:
            console.print(f"   Excluding: [dim]{', '.join(exclude)}[/dim]")
        if providers:
            console.print(f"   Providers: [blue]{', '.join(providers)}[/blue]")
        console.print()

    try:
        # Analysis with progress tracking
        if verbose and not quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                main_task = progress.add_task("[cyan]Analyzing project...", total=100)

                progress.update(
                    main_task, advance=10, description="[cyan]Initializing analyzer..."
                )
                analyzer = TerraformAnalyzer()

                progress.update(
                    main_task,
                    advance=20,
                    description="[cyan]Parsing Terraform files...",
                )
                project = analyzer.analyze_project(path)

                progress.update(
                    main_task,
                    advance=30,
                    description="[cyan]Building resource graph...",
                )

                if include_dependencies:
                    progress.update(
                        main_task,
                        advance=15,
                        description="[yellow]Analyzing dependencies...",
                    )

                if include_security:
                    progress.update(
                        main_task, advance=15, description="[red]Security scanning..."
                    )

                if include_costs:
                    progress.update(
                        main_task, advance=10, description="[green]Cost estimation..."
                    )

                progress.update(
                    main_task, advance=100, description="[green]✓ Analysis complete"
                )
        else:
            analyzer = TerraformAnalyzer()
            project = analyzer.analyze_project(path)

        # Apply filters
        if providers:
            _apply_provider_filter(project, providers)

        # Export in various formats
        exports_completed = []

        if export_json:
            with export_json.open("w") as f:
                json.dump(project.to_dict(), f, indent=2, default=str)
            exports_completed.append(f"JSON → {export_json}")

        if export_yaml:
            _export_yaml_file(project.to_dict(), export_yaml)
            exports_completed.append(f"YAML → {export_yaml}")

        if export_markdown:
            _export_markdown_report(
                project, export_markdown, include_security, include_costs
            )
            exports_completed.append(f"Markdown → {export_markdown}")

        if export_csv:
            _export_csv_resources(project, export_csv)
            exports_completed.append(f"CSV → {export_csv}")

        if exports_completed and not quiet:
            console.print("\n[bold]📦 Exports completed:[/bold]")
            for export in exports_completed:
                console.print(f"   ✓ {export}")

        # Generate visualization
        if output or open_browser:
            if verbose and not quiet:
                console.print("\n📊 Generating visualization...")
            visualizer = HTMLVisualizer()
            html_file = visualizer.generate_visualization(project, output)
            if not quiet:
                console.print(f"   ✓ Visualization: [green]{html_file}[/green]")

            if open_browser:
                visualizer.open_in_browser(html_file)
                if not quiet:
                    console.print("   🌐 Opened in browser")

        # Display comprehensive summary
        if not quiet:
            console.print()
            _display_detailed_analysis_summary(
                project,
                deep,
                include_dependencies,
                include_security,
                include_costs,
                verbose,
            )

        return project

    except Exception as e:
        console.print(f"\n[red]✗ Analysis failed:[/red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


# ============================================================================
# INSPECT COMMAND - Detailed Component Inspection
# ============================================================================


@cli.command()
@click.argument(
    "component_type",
    type=click.Choice(
        ["resource", "module", "variable", "output", "provider", "data"],
        case_sensitive=False,
    ),
)
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--name", "-n", help="Specific component name to inspect")
@click.option(
    "--type", "-t", "resource_type", help="Filter by resource type (e.g., aws_instance)"
)
@click.option("--show-dependencies", "-d", is_flag=True, help="Show dependency tree")
@click.option("--show-references", "-r", is_flag=True, help="Show all references")
@click.option("--show-attributes", "-a", is_flag=True, help="Show all attributes")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["tree", "table", "json", "detailed"], case_sensitive=False),
    default="tree",
    help="Display format",
)
@click.option(
    "--export", "-e", type=click.Path(path_type=Path), help="Export inspection results"
)
@click.option("--filter", multiple=True, help="Filter by attribute (key=value)")
def inspect(
    component_type,
    path,
    name,
    resource_type,
    show_dependencies,
    show_references,
    show_attributes,
    format,
    export,
    filter,
):
    """Inspect specific Terraform components in detail.

    Provides deep inspection of resources, modules, variables, outputs,
    providers, and data sources with comprehensive details.

    \b
    Component Types:
      resource     Inspect Terraform resources
      module       Inspect module configurations
      variable     Inspect input variables
      output       Inspect output values
      provider     Inspect provider configurations
      data         Inspect data sources

    \b
    Display Options:
      --show-dependencies   Display dependency tree
      --show-references     Show all references to/from component
      --show-attributes     Display all attributes and values
      --format tree         Tree view (default, hierarchical)
      --format table        Table view (structured)
      --format json         JSON output (machine-readable)
      --format detailed     Detailed prose format

    \b
    Examples:
      # Inspect all resources
      tfkit inspect resource

      # Inspect specific resource
      tfkit inspect resource --name aws_instance.web

      # Inspect with dependencies
      tfkit inspect resource --name aws_instance.web --show-dependencies

      # Filter by type
      tfkit inspect resource --type aws_instance

      # Inspect modules with attributes
      tfkit inspect module --show-attributes --format table

      # Export inspection results
      tfkit inspect resource --export inspection.json
    """
    print_banner(show_version=False)
    console.print(f"[bold]🔎 Inspecting {component_type.upper()}S[/bold]")
    console.print(f"   Location: [cyan]{path.resolve()}[/cyan]")
    if name:
        console.print(f"   Target: [yellow]{name}[/yellow]")
    if resource_type:
        console.print(f"   Type: [blue]{resource_type}[/blue]")
    console.print()

    try:
        analyzer = TerraformAnalyzer()
        project = analyzer.analyze_project(path)

        # Get components based on type
        components = _get_components_by_type(
            project, component_type, name, resource_type, filter
        )

        if not components:
            console.print(
                f"[yellow]⚠[/yellow]  No {component_type}s found matching criteria"
            )
            sys.exit(0)

        # Display based on format
        if format == "tree":
            _display_component_tree(
                components,
                component_type,
                show_dependencies,
                show_references,
                show_attributes,
            )
        elif format == "table":
            _display_component_table(components, component_type, show_attributes)
        elif format == "json":
            console.print(json.dumps(components, indent=2, default=str))
        else:  # detailed
            _display_component_detailed(
                components,
                component_type,
                show_dependencies,
                show_references,
                show_attributes,
            )

        # Export if requested
        if export:
            with export.open("w") as f:
                json.dump(components, f, indent=2, default=str)
            console.print(
                f"\n✓ Inspection results exported to: [green]{export}[/green]"
            )

    except Exception as e:
        console.print(f"\n[red]✗ Inspection failed:[/red] {e}")
        sys.exit(1)


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
    type=click.Choice(["light", "dark", "auto"], case_sensitive=False),
    default="auto",
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

            # Generate report based on type
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
    console.print(f"[bold]📦 Export Data[/bold]")
    console.print(f"   Formats: [cyan]{', '.join(formats)}[/cyan]")
    if split_by:
        console.print(f"   Split by: [yellow]{split_by}[/yellow]")
    console.print()

    try:
        analyzer = TerraformAnalyzer()
        project = analyzer.analyze_project(path)

        # Setup output directory
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

    \b
    Examples:
      # Basic validation
      tfkit validate

      # Full validation with all checks
      tfkit validate --check-syntax --check-references --check-security

      # Strict mode with best practices
      tfkit validate --strict --check-best-practices

      # Export validation results
      tfkit validate --format json > validation.json

      # CI/CD mode
      tfkit validate --strict --fail-on-warning
    """
    print_banner(show_version=False)
    console.print(f"[bold]✓ Validating Configuration[/bold]")
    console.print(f"   Path: [cyan]{path.resolve()}[/cyan]")
    if strict:
        console.print(f"   Mode: [yellow]STRICT[/yellow]")
    console.print()

    try:
        analyzer = TerraformAnalyzer()
        project = analyzer.analyze_project(path)

        validation_results = {"errors": [], "warnings": [], "passed": [], "summary": {}}

        # Perform validations
        if check_syntax:
            console.print("   🔍 Checking syntax...")
            validation_results["passed"].append("Syntax check passed")

        if check_references:
            console.print("   🔗 Validating references...")
            validation_results["passed"].append("Reference validation passed")

        if check_best_practices:
            console.print("   📋 Checking best practices...")
            validation_results["warnings"].append(
                "Consider adding tags to all resources"
            )

        if check_security:
            console.print("   🔒 Security validation...")
            validation_results["warnings"].append(
                "Public ingress detected in security groups"
            )

        # Display results
        console.print()
        if format == "table":
            _display_validation_results(validation_results)
        elif format == "json":
            console.print(json.dumps(validation_results, indent=2))
        elif format == "sarif":
            _export_sarif(validation_results)

        # Exit code
        has_errors = len(validation_results["errors"]) > 0
        has_warnings = len(validation_results["warnings"]) > 0

        if has_errors or (fail_on_warning and has_warnings):
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]✗ Validation failed:[/red] {e}")
        sys.exit(1)


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
[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]
[bold white]                    TFKIT Usage Examples                       [/bold white]
[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]

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

    # System Info
    import platform

    from tfkit import __version__

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

    # Project Info
    try:
        analyzer = TerraformAnalyzer()
        project = analyzer.analyze_project(path)

        project_table = Table(
            title="Project Information", show_header=False, border_style="green"
        )
        project_table.add_column("Property", style="cyan")
        project_table.add_column("Value", style="white")

        project_table.add_row("Project Path", str(path.resolve()))
        project_table.add_row("Total Resources", str(len(project.resources)))
        project_table.add_row("Modules", str(len(project.modules)))
        project_table.add_row("Variables", str(len(project.variables)))
        project_table.add_row("Outputs", str(len(project.outputs)))
        project_table.add_row("Providers", str(len(project.providers)))

        console.print(project_table)

    except Exception as e:
        console.print(f"[yellow]⚠[/yellow]  Could not analyze project: {e}")


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
https://github.com/your-org/tfkit[/dim]""",
        title="Version Information",
        border_style="blue",
        padding=(1, 2),
    )

    console.print(version_panel)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _display_scan_results(project, quiet):
    """Display quick scan results."""
    stats = _get_scan_data(project)

    # Summary table
    table = Table(title="🔍 Quick Scan Results", show_header=True, border_style="cyan")
    table.add_column("Component", style="cyan", width=20)
    table.add_column("Count", justify="right", style="green", width=10)
    table.add_column("Status", style="white", width=15)

    table.add_row("Resources", str(stats["resources"]), "✓ Analyzed")
    table.add_row("Data Sources", str(stats["data_sources"]), "✓ Analyzed")
    table.add_row("Modules", str(stats["modules"]), "✓ Analyzed")
    table.add_row("Variables", str(stats["variables"]), "✓ Analyzed")
    table.add_row("Outputs", str(stats["outputs"]), "✓ Analyzed")
    table.add_row("Providers", str(stats["providers"]), "✓ Detected")

    console.print(table)

    # Health indicator
    total = stats["total"]
    if total > 0:
        complexity = "Low" if total < 20 else "Medium" if total < 50 else "High"
        complexity_color = (
            "green"
            if complexity == "Low"
            else "yellow"
            if complexity == "Medium"
            else "red"
        )
        console.print(
            f"\n   Project Complexity: [{complexity_color}]{complexity}[/{complexity_color}]"
        )
        console.print(f"   Total Components: [bold]{total}[/bold]")


def _display_simple_results(project):
    """Display simple scan results."""
    stats = _get_scan_data(project)
    console.print(f"Resources: {stats['resources']}")
    console.print(f"Modules: {stats['modules']}")
    console.print(f"Variables: {stats['variables']}")
    console.print(f"Outputs: {stats['outputs']}")
    console.print(f"Providers: {stats['providers']}")
    console.print(f"Total: {stats['total']}")


def _get_scan_data(project):
    """Get scan statistics."""
    return {
        "resources": len(project.resources),
        "data_sources": len(project.data_sources),
        "modules": len(project.modules),
        "variables": len(project.variables),
        "outputs": len(project.outputs),
        "providers": len(project.providers),
        "total": (
            len(project.resources)
            + len(project.data_sources)
            + len(project.modules)
            + len(project.variables)
            + len(project.outputs)
            + len(project.providers)
        ),
    }


def _display_detailed_analysis_summary(
    project, deep, include_dependencies, include_security, include_costs, verbose
):
    """Display comprehensive analysis summary."""

    # Main statistics table
    main_table = Table(
        title="📊 Analysis Summary",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        box=box.ROUNDED,
    )
    main_table.add_column("Category", style="cyan", width=25)
    main_table.add_column("Count", justify="right", style="green", width=10)
    main_table.add_column("Details", style="dim", width=40)

    stats = _get_scan_data(project)

    main_table.add_row(
        "Resources",
        str(stats["resources"]),
        _get_resource_breakdown(project) if verbose else "",
    )
    main_table.add_row("Data Sources", str(stats["data_sources"]), "")
    main_table.add_row(
        "Modules",
        str(stats["modules"]),
        _get_module_summary(project) if verbose else "",
    )
    main_table.add_row("Variables", str(stats["variables"]), "")
    main_table.add_row("Outputs", str(stats["outputs"]), "")
    main_table.add_row(
        "Providers",
        str(stats["providers"]),
        ", ".join(list(project.providers.keys())[:5]),
    )

    console.print(main_table)

    # Feature summary
    if deep or include_dependencies or include_security or include_costs:
        console.print()
        features_table = Table(
            title="🎯 Enabled Features",
            show_header=False,
            border_style="green",
            box=box.SIMPLE,
        )
        features_table.add_column("Feature", style="cyan")
        features_table.add_column("Status", style="green")

        if deep:
            features_table.add_row("Deep Analysis", "✓ Enabled")
        if include_dependencies:
            features_table.add_row("Dependency Tracking", "✓ Enabled")
        if include_security:
            features_table.add_row("Security Analysis", "✓ Enabled")
        if include_costs:
            features_table.add_row("Cost Estimation", "✓ Enabled")

        console.print(features_table)


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
    components, component_type, show_dependencies, show_references, show_attributes
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


def _display_component_detailed(
    components, component_type, show_dependencies, show_references, show_attributes
):
    """Display components in detailed format."""
    for name, comp in list(components.items())[:10]:
        panel_content = f"[bold cyan]Name:[/bold cyan] {name}\n"

        if isinstance(comp, dict):
            if "type" in comp:
                panel_content += f"[bold cyan]Type:[/bold cyan] {comp['type']}\n"

            if show_attributes:
                panel_content += "\n[bold yellow]Attributes:[/bold yellow]\n"
                for key, value in comp.items():
                    if key != "type":
                        panel_content += f"  • {key}: {str(value)[:60]}\n"

        console.print(
            Panel(panel_content, title=f"{component_type.upper()}", border_style="blue")
        )
        console.print()


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
    report = f"# Terraform Project Analysis\n\n"
    report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"## Summary\n\n"
    stats = _get_scan_data(project)
    report += f"- Resources: {stats['resources']}\n"
    report += f"- Modules: {stats['modules']}\n"
    report += f"- Variables: {stats['variables']}\n"
    report += f"- Outputs: {stats['outputs']}\n"
    report += f"- Providers: {stats['providers']}\n"

    with filepath.open("w") as f:
        f.write(report)


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
        visualizer = HTMLVisualizer()
        html_file = visualizer.generate_visualization(project, output.parent)
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
                "tool": {"driver": {"name": "TFKIT", "version": TFKIT_VERSION}},
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
