import json
import sys
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.validator.models import ValidationSeverity
from tfkit.validator.validator import TerraformValidator

from .utils import console, print_banner


@click.command()
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
