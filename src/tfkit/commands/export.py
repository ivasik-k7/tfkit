import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import click

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer

from .utils import console, export_yaml_file, print_banner


@click.command()
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
            console.print("\n[bold]Exported files:[/bold]")
            for file in exported_files:
                console.print(f"   • [green]{file}[/green]")

    except Exception as e:
        console.print(f"\n[red]✗ Export failed:[/red] {e}")
        sys.exit(1)


def _export_single(project, format, output_dir, prefix):
    """Export project data in single format."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filepath = output_dir / f"{prefix}-{timestamp}.{format}"

    if format == "json":
        with filepath.open("w") as f:
            json.dump(project.to_dict(), f, indent=2, default=str)
    elif format == "yaml":
        export_yaml_file(project.to_dict(), filepath)
    elif format == "csv":
        _export_csv_resources(project, filepath)
    elif format == "xml":
        _export_xml(project, filepath)
    elif format == "toml":
        _export_toml(project, filepath)

    return filepath


def _export_split(project, format, output_dir, prefix, split_by):
    """Export project data split by category."""
    files = []
    files.append(_export_single(project, format, output_dir, f"{prefix}-all"))
    return files


def _export_csv_resources(project, filepath):
    """Export resources as CSV."""
    with filepath.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Type", "Provider", "File", "Line"])

        for name, res in project.resources.items():
            res_type = res.resource_type if hasattr(res, "resource_type") else ""
            provider = res.provider if hasattr(res, "provider") else ""
            file_path = res.file_path if hasattr(res, "file_path") else ""
            line_num = res.line_number if hasattr(res, "line_number") else ""
            writer.writerow([name, res_type, provider, file_path, line_num])


def _export_xml(project, filepath):
    """Export as XML."""
    try:
        import xml.etree.ElementTree as ET

        root = ET.Element("terraform_project")

        resources_elem = ET.SubElement(root, "resources")
        for name, res in project.resources.items():
            res_elem = ET.SubElement(resources_elem, "resource", name=name)
            if hasattr(res, "resource_type"):
                ET.SubElement(res_elem, "type").text = res.resource_type
            if hasattr(res, "provider"):
                ET.SubElement(res_elem, "provider").text = res.provider

        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] XML export error: {e}")
        with filepath.open("w") as f:
            json.dump(project.to_dict(), f, indent=2, default=str)


def _export_toml(project, filepath):
    """Export as TOML."""
    try:
        import toml

        data = project.to_dict()
        with filepath.open("w") as f:
            toml.dump(data, f)
    except ImportError:
        console.print(
            "[yellow]⚠[/yellow] TOML export requires 'toml' package. Falling back to JSON."
        )
        with filepath.open("w") as f:
            json.dump(project.to_dict(), f, indent=2, default=str)
