import sys

import click
from rich.console import Console

console = Console()


def print_welcome():
    """Display welcome message."""
    from tfkit import __version__

    print(f"tfkit v{__version__} - Terraform Analysis Tool")

    print("\nRepository: https://github.com/ivasik-k7/tfkit")
    print("Homepage: https://tfkit.netlify.app")

    print("\nQuick Start:")
    print("  tfkit scan <path>        # Analyze Terraform project")
    print("  tfkit validate           # Validate configurations")
    print("  tfkit export --format    # Export analysis results")

    print("\nRun 'tfkit --help' for complete usage")


def show_version_info():
    """Show version information."""
    from tfkit import __version__

    print(f"tfkit v{__version__}")
    print("https://github.com/ivasik-k7/tfkit/releases")


# ============================================================================
# MAIN CLI GROUP
# ============================================================================


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--version", "-v", is_flag=True, help="Show version and exit")
@click.option("--welcome", "-w", is_flag=True, help="Show welcome message")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def cli(ctx, version, welcome, debug):
    """tfkit - Terraform analysis tool

    Analyze, validate, and export Terraform configurations.
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
# REGISTER COMMANDS
# ============================================================================


def _register_commands():
    """Register all CLI commands. Called after cli group is defined."""
    # Use absolute imports from tfkit.commands (not relative)
    from tfkit.commands.examples import examples
    from tfkit.commands.export import export
    from tfkit.commands.scan import scan
    from tfkit.commands.validate import validate

    cli.add_command(scan)
    cli.add_command(validate)
    cli.add_command(export)
    cli.add_command(examples)


# Register commands immediately
_register_commands()


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
