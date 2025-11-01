import json

from rich.console import Console
from rich.table import Table

console = Console()


def print_banner(show_version: bool = True):
    """Print enhanced tfkit banner."""
    TFKIT_BANNER = """
████████╗███████╗██╗  ██╗██╗████████╗
╚══██╔══╝██╔════╝██║ ██╔╝██║╚══██╔══╝
   ██║   █████╗  █████╔╝ ██║   ██║
   ██║   ██╔══╝  ██╔═██╗ ██║   ██║
   ██║   ██║     ██║  ██╗██║   ██║
   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝
"""
    console.print(f"[bold blue]{TFKIT_BANNER}[/bold blue]", highlight=False)


def get_scan_data(data):
    """Extract scan data for JSON/YAML output."""
    if isinstance(data, dict) and "statistics" in data:
        stats = data["statistics"]
    else:
        stats = data if isinstance(data, dict) else {}

    return {
        "summary": {
            "total_objects": stats.get("counts", {}).get("total", 0),
            "resources": stats.get("counts", {}).get("resources", 0),
            "data_sources": stats.get("counts", {}).get("data_sources", 0),
            "variables": stats.get("counts", {}).get("variables", 0),
            "outputs": stats.get("counts", {}).get("outputs", 0),
            "providers": stats.get("counts", {}).get("providers", 0),
            "modules": stats.get("counts", {}).get("modules", 0),
            "locals": stats.get("counts", {}).get("locals", 0),
        },
        "health": {
            "score": stats.get("health", {}).get("score", 0),
            "unused_count": stats.get("health", {}).get("unused_count", 0),
            "orphaned_count": stats.get("health", {}).get("orphaned_count", 0),
            "incomplete_count": stats.get("health", {}).get("incomplete_count", 0),
        },
        "resource_types": stats.get("resource_types", {}),
        "state_distribution": stats.get("state_distribution", {}),
        "issues": {
            "unused_count": len(stats.get("issues", {}).get("unused", [])),
            "orphaned_count": len(stats.get("issues", {}).get("orphaned", [])),
            "incomplete_count": len(stats.get("issues", {}).get("incomplete", [])),
            "unused_sample": stats.get("issues", {}).get("unused", [])[:5],
            "orphaned_outputs": stats.get("issues", {}).get("orphaned", [])[:5],
            "incomplete_objects": stats.get("issues", {}).get("incomplete", []),
        },
        "providers_used": stats.get("providers", {}).get("used", []),
    }


def export_yaml(data):
    """Export data as YAML."""
    try:
        import yaml

        console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))
    except ImportError:
        console.print(
            "[red]PyYAML not installed. Install with: pip install PyYAML[/red]"
        )
        console.print(json.dumps(data, indent=2))


def export_yaml_file(data, filepath):
    """Export data to YAML file."""
    try:
        import yaml

        with filepath.open("w") as f:
            yaml.dump(data, f, default_flow_style=False)
    except ImportError:
        console.print("[yellow]⚠[/yellow] PyYAML not installed. Skipping YAML export.")


def display_scan_results(data, quiet=False):
    """Display scan results in table format."""
    if isinstance(data, dict) and "statistics" in data:
        stats = data["statistics"]
    else:
        stats = data if isinstance(data, dict) else {}

    # Overall summary
    console.print("\n[bold cyan]📊 TERRAFORM PROJECT SUMMARY[/bold cyan]")
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="white")
    summary_table.add_column("Details", style="green")

    counts = stats.get("counts", {})
    total_objects = counts.get("total", 0)
    resource_count = counts.get("resources", 0)
    data_source_count = counts.get("data_sources", 0)
    variable_count = counts.get("variables", 0)
    output_count = counts.get("outputs", 0)
    provider_count = counts.get("providers", 0)

    resource_types = stats.get("resource_types", {})
    state_dist = stats.get("state_distribution", {})
    providers = stats.get("providers", {})

    summary_table.add_row(
        "Total Objects", str(total_objects), "All Terraform components"
    )
    summary_table.add_row(
        "Resources", str(resource_count), f"{len(resource_types)} unique types"
    )
    summary_table.add_row(
        "Data Sources", str(data_source_count), "External data references"
    )
    summary_table.add_row(
        "Variables", str(variable_count), f"{state_dist.get('input', 0)} used"
    )
    summary_table.add_row(
        "Outputs", str(output_count), f"{state_dist.get('orphaned', 0)} orphaned"
    )

    provider_list = providers.get("used", [])
    summary_table.add_row("Providers", str(provider_count), ", ".join(provider_list))

    console.print(summary_table)

    # Health assessment
    console.print("\n[bold cyan]🏥 HEALTH ASSESSMENT[/bold cyan]")
    health_table = Table(show_header=True, header_style="bold magenta")
    health_table.add_column("Category", style="cyan")
    health_table.add_column("Count", style="white")
    health_table.add_column("Status", style="green")

    health_data = stats.get("health", {})
    health_score = health_data.get("score", 0)
    health_color = (
        "red" if health_score < 50 else "yellow" if health_score < 80 else "green"
    )
    health_status = (
        "Needs attention"
        if health_score < 50
        else "Good" if health_score < 80 else "Excellent"
    )

    health_table.add_row(
        "Overall Score",
        f"{health_score:.1f}%",
        f"[{health_color}]{health_status}[/{health_color}]",
    )
    health_table.add_row(
        "Unused Objects",
        str(health_data.get("unused_count", 0)),
        "[yellow]Potential cleanup[/yellow]",
    )
    health_table.add_row(
        "Orphaned Outputs",
        str(health_data.get("orphaned_count", 0)),
        "[yellow]Unused outputs[/yellow]",
    )
    health_table.add_row(
        "Incomplete",
        str(health_data.get("incomplete_count", 0)),
        "[red]Missing values[/red]",
    )

    console.print(health_table)

    # Resource types breakdown
    if not quiet and resource_types:
        console.print("\n[bold cyan]🔧 RESOURCE TYPES[/bold cyan]")
        resource_table = Table(show_header=True, header_style="bold magenta")
        resource_table.add_column("Resource Type", style="cyan")
        resource_table.add_column("Count", style="white")

        sorted_resources = sorted(
            resource_types.items(), key=lambda x: x[1], reverse=True
        )[:10]
        for resource_type, count in sorted_resources:
            resource_table.add_row(resource_type, str(count))

        if len(resource_types) > 10:
            resource_table.add_row(
                f"... and {len(resource_types) - 10} more", "", style="dim"
            )

        console.print(resource_table)

    # Issues summary
    console.print("\n[bold cyan]⚠️  POTENTIAL ISSUES[/bold cyan]")
    issues = stats.get("issues", {})

    unused_issues = issues.get("unused", [])
    if unused_issues:
        console.print(f"[yellow]• {len(unused_issues)} Unused objects[/yellow]")
        if not quiet and len(unused_issues) > 0:
            unused_sample = unused_issues[:3]
            for item in unused_sample:
                console.print(f"  └─ {item}")
            if len(unused_issues) > 3:
                console.print(f"  └─ ... and {len(unused_issues) - 3} more")

    orphaned_issues = issues.get("orphaned", [])
    if orphaned_issues:
        console.print(f"[yellow]• {len(orphaned_issues)} Orphaned outputs[/yellow]")
        if not quiet:
            for output in orphaned_issues[:3]:
                console.print(f"  └─ {output}")
            if len(orphaned_issues) > 3:
                console.print(f"  └─ ... and {len(orphaned_issues) - 3} more")

    incomplete_issues = issues.get("incomplete", [])
    if incomplete_issues:
        console.print(f"[red]• {len(incomplete_issues)} Incomplete objects[/red]")
        if not quiet:
            for item in incomplete_issues:
                console.print(f"  └─ {item}")

    # State distribution
    if not quiet and state_dist:
        console.print("\n[bold cyan]📈 STATE DISTRIBUTION[/bold cyan]")
        state_table = Table(show_header=True, header_style="bold magenta")
        state_table.add_column("State", style="cyan")
        state_table.add_column("Count", style="white")
        state_table.add_column("Description", style="green")

        state_descriptions = {
            "external_data": "Data sources",
            "integrated": "Resources with dependents",
            "active": "Core infrastructure",
            "input": "Used variables",
            "orphaned": "Unused outputs",
            "configuration": "Providers & config",
            "unused": "Unreferenced objects",
            "incomplete": "Missing values",
        }

        for state, count in state_dist.items():
            description = state_descriptions.get(state, state.replace("_", " ").title())
            state_table.add_row(
                state.replace("_", " ").title(), str(count), description
            )

        console.print(state_table)


def display_simple_results(data):
    """Display minimal scan results."""
    if isinstance(data, dict) and "statistics" in data:
        stats = data["statistics"]
    else:
        stats = data if isinstance(data, dict) else {}

    counts = stats.get("counts", {})
    health_data = stats.get("health", {})
    providers = stats.get("providers", {})
    resource_types = stats.get("resource_types", {})

    console.print("\n[bold]TERRAFORM SCAN RESULTS[/bold]")
    console.print(f"📦 Total Objects: {counts.get('total', 0)}")
    console.print(
        f"🔧 Resources: {counts.get('resources', 0)} ({len(resource_types)} types)"
    )
    console.print(f"📊 Data Sources: {counts.get('data_sources', 0)}")
    console.print(f"⚙️  Providers: {', '.join(providers.get('used', []))}")

    health_score = health_data.get("score", 0)
    health_icon = "🔴" if health_score < 50 else "🟡" if health_score < 80 else "🟢"
    console.print(f"🏥 Health: {health_icon} {health_score:.1f}%")

    if health_data.get("unused_count", 0) > 0:
        console.print(f"⚠️  Unused: {health_data.get('unused_count', 0)} objects")
    if health_data.get("orphaned_count", 0) > 0:
        console.print(f"📤 Orphaned: {health_data.get('orphaned_count', 0)} outputs")
    if health_data.get("incomplete_count", 0) > 0:
        console.print(
            f"❌ Incomplete: {health_data.get('incomplete_count', 0)} objects"
        )
