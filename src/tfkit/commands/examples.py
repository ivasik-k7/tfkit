import click
from rich.panel import Panel

from .utils import console, print_banner


@click.command()
def examples():
    """
    Show practical usage examples and common patterns.

    Display real-world examples for scanning complex projects, validating
    multi-environment setups, and exporting data for CI/CD pipelines.
    Includes advanced usage scenarios and integration patterns.
    """
    print_banner()

    examples_content = """
[bold yellow]🔍 SCAN - Analyze Terraform Projects[/bold yellow]

  # Quick scan of current directory
  tfkit scan

  # Scan specific path with JSON output
  tfkit scan /path/to/terraform --format json

  # Save results to file
  tfkit scan --save results.json

  # Open visualization in browser
  tfkit scan --open

  # Custom theme and layout
  tfkit scan --open --theme cyber --layout dashboard

[bold yellow]✅ VALIDATE - Check Configurations[/bold yellow]

  # Basic validation
  tfkit validate

  # Full validation with all checks
  tfkit validate --all

  # Security-focused validation
  tfkit validate --check-security

  # CI/CD mode (fails on warnings)
  tfkit validate --all --fail-on-warning

  # Ignore specific rules
  tfkit validate --all --ignore TF020 --ignore TF021

[bold yellow]📦 EXPORT - Export Data[/bold yellow]

  # Export as JSON
  tfkit export --format json

  # Export multiple formats
  tfkit export --format json --format yaml

  # Export to custom directory
  tfkit export -f json -o ./exports

  # Compress exported files
  tfkit export --format json --compress

  # Custom prefix
  tfkit export --format json --prefix prod-infra

[bold yellow]⚡ QUICK WORKFLOWS[/bold yellow]

  # Complete analysis
  tfkit scan && tfkit validate --all

  # Export everything
  tfkit scan --save scan.json && tfkit export --format json --format yaml

  # Security check
  tfkit validate --check-security --fail-on-warning

  # Full analysis with visualization
  tfkit scan --open --theme dark && tfkit validate --all

[bold yellow]🚀 CI/CD INTEGRATION[/bold yellow]

  # GitHub Actions workflow
  - name: Validate Terraform
    run: |
      tfkit validate --all --fail-on-warning --format json > validation.json
      tfkit scan --format json --save scan-results.json

  # GitLab CI
  terraform-check:
    script:
      - tfkit validate --all --strict
      - tfkit export --format json -o ./reports

  # Jenkins Pipeline
  stage('Terraform Validation') {
    steps {
      sh 'tfkit validate --all --format sarif > results.sarif'
    }
  }

[bold yellow]📊 ADVANCED USAGE[/bold yellow]

  # Multiple format exports for reporting
  tfkit export --format json --format yaml --format csv --compress

  # Detailed scan with specific output
  tfkit scan --format yaml --save detailed-scan.yaml --quiet

  # Validation with custom rules
  tfkit validate --check-best-practices --check-security \\
    --ignore TF001 --ignore TF002 --format json

  # Full project analysis
  tfkit scan --open --theme github-dark --layout graph && \\
  tfkit validate --all --format table && \\
  tfkit export --format json --format yaml -o ./reports
"""

    console.print(Panel(examples_content, border_style="cyan", padding=(1, 2)))
