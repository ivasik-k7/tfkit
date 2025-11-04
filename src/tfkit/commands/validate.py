import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tfkit.analyzer.terraform_analyzer import TerraformAnalyzer
from tfkit.validator.models import ValidationCategory, ValidationSeverity
from tfkit.validator.rule_register import rule_registry
from tfkit.validator.validator import TerraformValidator, ValidatorConfig

from .utils import console, print_banner


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--checks",
    "-c",
    type=click.Choice(["syntax", "references", "best-practices", "security", "all"]),
    multiple=True,
    help="Validation checks to run (can specify multiple)",
)
@click.option("--strict", "-s", is_flag=True, help="Enable strict validation mode")
@click.option("--fail-on-warning", is_flag=True, help="Treat warnings as errors")
@click.option("--ignore", multiple=True, help="Ignore specific validation rules")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (format determined by extension: .json, .sarif, .txt)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "sarif"], case_sensitive=False),
    default="table",
    help="Output format (used when no file extension specified)",
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Suppress console output (only file output)"
)
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Enable/disable parallel validation (default: enabled)",
)
@click.option(
    "--max-workers",
    type=int,
    default=4,
    help="Maximum number of parallel workers (default: 4)",
)
@click.option(
    "--list-rules",
    is_flag=True,
    help="List all available validation rules and exit",
)
@click.option(
    "--show-rules",
    is_flag=True,
    help="Show loaded rules before validation",
)
@click.option(
    "--rules-package",
    default="tfkit.validator.rules",
    help="Package name to load rules from (default: tfkit.validator.rules)",
)
@click.option(
    "--enable-rule",
    multiple=True,
    help="Enable specific rules (can specify multiple)",
)
@click.option(
    "--disable-rule",
    multiple=True,
    help="Disable specific rules (can specify multiple)",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    help="Stop validation on first error",
)
def validate(
    path,
    checks,
    strict,
    fail_on_warning,
    ignore,
    output,
    format,
    quiet,
    parallel,
    max_workers,
    list_rules,
    show_rules,
    rules_package,
    enable_rule,
    disable_rule,
    fail_fast,
):
    """Validate Terraform configurations.

    Perform comprehensive validation of Terraform configurations
    including syntax, references, best practices, and security.

    \b
    Validation Checks (use --checks/-c):
      syntax           HCL syntax validation
      references       Reference validation
      best-practices   Best practices compliance
      security         Security configuration checks
      all              Run all validation checks

    \b
    Examples:
      # Basic validation (syntax + references)
      tfkit validate

      # Run specific checks
      tfkit validate --checks syntax --checks security

      # Run all checks
      tfkit validate --checks all

      # List all available rules
      tfkit validate --list-rules

      # Show loaded rules before validation
      tfkit validate --show-rules

      # Disable specific rules
      tfkit validate --disable-rule AWS-001 --disable-rule NAMING-001

      # Enable parallel validation with custom workers
      tfkit validate --parallel --max-workers 8

      # Fast fail on first error
      tfkit validate --fail-fast

      # Save to file (format auto-detected from extension)
      tfkit validate --checks all --output validation.json
      tfkit validate --checks all --output results.sarif

      # CI/CD mode (quiet + fail on warnings)
      tfkit validate --checks all --strict --fail-on-warning --quiet --output results.json

      # Ignore specific rules
      tfkit validate --checks all --ignore TF020 --ignore TF021
    """
    print_banner(show_version=False)

    # Initialize validator configuration
    config = ValidatorConfig(
        strict=strict,
        ignore_rules=set(ignore),
        parallel=parallel,
        max_workers=max_workers,
        fail_fast=fail_fast,
        auto_load_rules=True,
        rules_package=rules_package,
    )

    validator = TerraformValidator(config)

    if not quiet:
        with console.status("[bold cyan]Loading validation rules..."):
            validator.initialize()
    else:
        validator.initialize()

    stats = validator.get_stats()
    registry_stats = stats.get("registry_stats", {})

    if not quiet:
        console.print(
            f"[green]✓[/green] Loaded [cyan]{registry_stats.get('total_rules', 0)}[/cyan] validation rules "
            f"([cyan]{registry_stats.get('enabled_rules', 0)}[/cyan] enabled)"
        )
        console.print()

    # Apply enable/disable rules
    for rule_id in disable_rule:
        if validator.disable_rule(rule_id):
            if not quiet:
                console.print(f"   [yellow]Disabled rule:[/yellow] {rule_id}")
        else:
            console.print(f"   [red]Warning: Rule '{rule_id}' not found[/red]")

    for rule_id in enable_rule:
        if validator.enable_rule(rule_id):
            if not quiet:
                console.print(f"   [green]Enabled rule:[/green] {rule_id}")
        else:
            console.print(f"   [red]Warning: Rule '{rule_id}' not found[/red]")

    # List rules and exit if requested
    if list_rules:
        _display_available_rules(validator)
        sys.exit(0)

    if show_rules and not quiet:
        _display_loaded_rules_summary(validator)

    check_categories = _resolve_check_categories(checks)

    if not quiet:
        console.print("[bold]✓ Validating Configuration[/bold]")
        console.print(f"   Path: [cyan]{path.resolve()}[/cyan]")
        console.print(f"   Mode: [yellow]{'STRICT' if strict else 'NORMAL'}[/yellow]")
        console.print(
            f"   Parallel: [cyan]{'Yes' if parallel else 'No'}[/cyan]"
            + (f" ({max_workers} workers)" if parallel else "")
        )
        if fail_fast:
            console.print("   Fail Fast: [yellow]Enabled[/yellow]")
        if ignore:
            console.print(f"   Ignoring rules: [dim]{', '.join(ignore)}[/dim]")

        console.print("\n   Active check categories:")
        for category in check_categories:
            rules_count = len(rule_registry.get_rules_by_category(category))
            console.print(f"     • {category.value} ({rules_count} rules)")
        console.print()

    try:
        if not quiet:
            with console.status("[bold cyan]Analyzing Terraform project..."):
                analyzer = TerraformAnalyzer()
                project = analyzer.analyze_project(str(path))

            console.print(
                f"[green]✓[/green] Found {len(project.resources)} resources, "
                f"{len(project.modules)} modules, {len(project.variables)} variables"
            )
            console.print()
        else:
            analyzer = TerraformAnalyzer()
            project = analyzer.analyze_project(str(path))

        if not quiet:
            console.print("[bold cyan]Running validation checks...[/bold cyan]")
            console.print()

        result = validator.validate(
            project,
            check_categories=check_categories,
            specific_resources=None,
        )

        # Get validation statistics
        validation_stats = validator.get_stats()

        # Determine output format from file extension if provided
        output_format = _get_output_format(output, format)

        # Save to file if requested
        if output:
            output_file = _save_validation_results(
                result, output, output_format, path, validation_stats
            )
            if not quiet:
                console.print(
                    f"\n[green]✓ Validation results saved to:[/green] [cyan]{output_file}[/cyan]"
                )

        # Display results unless quiet mode
        if not quiet:
            _display_validation_results(result, output_format, path, validation_stats)

        exit_code = 0
        if result.has_errors:
            exit_code = 1
        elif fail_on_warning and result.has_warnings:
            exit_code = 1

        if not quiet:
            console.print()
            if exit_code == 0:
                console.print(
                    "[bold green]✓ Validation completed successfully[/bold green]"
                )

                # Show performance stats
                duration = validation_stats.get("duration", 0)
                resources = validation_stats.get("resources_validated", 0)
                rules_exec = validation_stats.get("rules_executed", 0)
                console.print(
                    f"\n[dim]Validated {resources} resources with {rules_exec} rule checks in {duration:.2f}s[/dim]"
                )
            else:
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


def _resolve_check_categories(checks):
    """Determine which check categories to run based on the checks list."""
    if "all" in checks:
        return set(ValidationCategory)

    # Default checks if none specified
    if not checks:
        return {ValidationCategory.SYNTAX, ValidationCategory.REFERENCES}

    categories = set()
    check_mapping = {
        "syntax": ValidationCategory.SYNTAX,
        "references": ValidationCategory.REFERENCES,
        "best-practices": ValidationCategory.BEST_PRACTICES,
        "security": ValidationCategory.SECURITY,
    }

    for check in checks:
        if check in check_mapping:
            categories.add(check_mapping[check])

    return categories


def _display_available_rules(validator):
    """Display all available validation rules in a detailed table."""
    console.print("\n[bold cyan]Available Validation Rules[/bold cyan]\n")

    rules = validator.list_available_rules()

    if not rules:
        console.print("[yellow]No rules loaded.[/yellow]")
        return

    # Group rules by category
    rules_by_category = {}
    for rule in rules:
        category = rule["category"]
        if category not in rules_by_category:
            rules_by_category[category] = []
        rules_by_category[category].append(rule)

    # Display rules by category
    for category in sorted(rules_by_category.keys()):
        category_rules = rules_by_category[category]

        table = Table(
            show_header=True,
            header_style="bold magenta",
            title=f"[bold]{category.upper()}[/bold]",
            title_style="bold cyan",
        )
        table.add_column("Rule ID", width=15)
        table.add_column("Severity", width=10)
        table.add_column("Scope", width=15)
        table.add_column("Priority", width=8, justify="right")
        table.add_column("Status", width=10)
        table.add_column("Description")

        for rule in sorted(category_rules, key=lambda r: r["rule_id"]):
            severity_style = {
                "error": "red",
                "warning": "yellow",
                "info": "blue",
            }.get(rule["severity"], "white")

            status_text = (
                Text("Enabled", style="green")
                if rule["enabled"]
                else Text("Disabled", style="dim")
            )

            table.add_row(
                rule["rule_id"],
                Text(rule["severity"].upper(), style=severity_style),
                rule["scope"],
                str(rule["priority"]),
                status_text,
                rule["description"],
            )

        console.print(table)
        console.print()

    # Summary
    total_rules = len(rules)
    enabled_rules = sum(1 for r in rules if r["enabled"])
    console.print(
        f"[bold]Total:[/bold] {total_rules} rules ({enabled_rules} enabled, {total_rules - enabled_rules} disabled)"
    )


def _display_loaded_rules_summary(validator):
    """Display a summary of loaded rules."""
    console.print("\n[bold cyan]Loaded Rules Summary[/bold cyan]\n")

    stats = validator.get_stats()
    registry_stats = stats.get("registry_stats", {})

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Label", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Rules:", str(registry_stats.get("total_rules", 0)))
    summary_table.add_row("Enabled Rules:", str(registry_stats.get("enabled_rules", 0)))
    summary_table.add_row("Generic Rules:", str(registry_stats.get("generic_rules", 0)))
    summary_table.add_row("Project Rules:", str(registry_stats.get("project_rules", 0)))
    summary_table.add_row(
        "Resource-Specific:",
        str(registry_stats.get("resource_specific_rules", 0)),
    )

    console.print(summary_table)

    # Show rules by category
    categories = registry_stats.get("categories", {})
    if categories:
        console.print("\n[bold]Rules by Category:[/bold]")
        for category, count in sorted(categories.items()):
            console.print(f"  • {category}: [cyan]{count}[/cyan]")

    console.print()


def _get_output_format(output_path, default_format):
    """Determine output format from file extension or use default."""
    if not output_path:
        return default_format

    extension_to_format = {
        ".json": "json",
        ".sarif": "sarif",
        ".txt": "table",
        ".md": "table",
    }

    ext = Path(output_path).suffix.lower()
    return extension_to_format.get(ext, default_format)


def _save_validation_results(result, output_path, format, base_path=None, stats=None):
    """Save validation results to a file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "table":
            content = _format_validation_results_table(result, stats)
        elif format == "json":
            content = _format_validation_results_json(result, stats)
        elif format == "sarif":
            content = _format_validation_results_sarif(result, base_path)
        else:
            content = _format_validation_results_table(result, stats)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file.resolve()

    except Exception as e:
        console.print(f"[red]✗ Failed to save results to {output_path}: {e}[/red]")
        return None


def _display_validation_results(result, format, base_path=None, stats=None):
    """Display validation results in the specified format."""
    if format == "table":
        _display_validation_results_table(result, stats)
    elif format == "json":
        _display_validation_results_json(result, stats)
    elif format == "sarif":
        _display_validation_results_sarif(result, base_path)


def _display_validation_results_table(result, stats=None):
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

    if summary.get("passed"):
        summary_text.append(f"Passed: {summary['passed']}", style="bold green")

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


def _display_validation_results_json(result, stats=None):
    """Display validation results in JSON format."""
    output = _format_validation_results_json(result, stats)
    console.print(output)


def _display_validation_results_sarif(result, base_path):
    """Display validation results in SARIF format."""
    output = _format_validation_results_sarif(result, base_path)
    console.print(output)


def _format_validation_results_table(result, stats=None):
    """Format validation results as plain text for file output."""
    summary = result.get_summary()

    output = []
    output.append("VALIDATION SUMMARY")
    output.append("=" * 50)
    output.append(f"Errors: {summary['errors']}")
    output.append(f"Warnings: {summary['warnings']}")
    output.append(f"Info: {summary['info']}")
    if summary.get("passed"):
        output.append(f"Passed: {summary['passed']}")

    if stats:
        output.append("")
        output.append("PERFORMANCE STATISTICS")
        output.append("=" * 50)
        output.append(f"Duration: {stats.get('duration', 0):.2f}s")
        output.append(f"Resources Validated: {stats.get('resources_validated', 0)}")
        output.append(f"Rules Executed: {stats.get('rules_executed', 0)}")

    output.append("")

    all_issues = result.errors + result.warnings + result.info

    if all_issues:
        output.append("VALIDATION ISSUES")
        output.append("=" * 50)

        for issue in all_issues:
            output.append(f"Severity: {issue.severity.value.upper()}")
            output.append(f"Category: {issue.category.value}")
            output.append(f"Rule: {issue.rule_id}")
            output.append(f"Location: {issue.file_path}:{issue.line_number}")
            output.append(f"Resource: {issue.resource_name or 'N/A'}")
            output.append(f"Message: {issue.message}")
            if issue.suggestion:
                output.append(f"Suggestion: {issue.suggestion}")
            output.append("-" * 40)

        issues_with_suggestions = [issue for issue in all_issues if issue.suggestion]
        if issues_with_suggestions:
            output.append("")
            output.append("SUGGESTIONS")
            output.append("=" * 50)
            for issue in issues_with_suggestions:
                output.append(f"• {issue.suggestion}")
    else:
        output.append("No validation issues found!")

    if result.passed:
        output.append("")
        output.append(f"✅ {len(result.passed)} checks passed")

    return "\n".join(output)


def _format_validation_results_json(result, stats=None):
    """Format validation results as JSON for file output."""
    summary = result.get_summary()

    output = {
        "summary": summary,
        "passed_checks": result.passed if hasattr(result, "passed") else [],
        "issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category.value,
                "rule_id": issue.rule_id,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "resource_name": issue.resource_name,
                "resource_type": getattr(issue, "resource_type", "unknown"),
                "message": issue.message,
                "suggestion": issue.suggestion,
            }
            for issue in result.errors + result.warnings + result.info
        ],
        "timestamp": datetime.now().isoformat(),
    }

    if stats:
        output["performance"] = {
            "duration": stats.get("duration", 0),
            "resources_validated": stats.get("resources_validated", 0),
            "rules_executed": stats.get("rules_executed", 0),
        }

    return json.dumps(output, indent=2)


def _format_validation_results_sarif(result, base_path):
    """Format validation results as SARIF for file output."""
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

    return json.dumps(sarif_output, indent=2)
