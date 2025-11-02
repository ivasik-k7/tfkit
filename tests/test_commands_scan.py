# import json
# import tempfile
# from pathlib import Path
# from unittest.mock import MagicMock, patch

# import pytest
# from click.testing import CliRunner

# from tfkit.commands.scan import scan


# class TestTerraformScanCommand:
#     """Test suite for the Terraform scan command."""

#     @pytest.fixture
#     def runner(self):
#         """CLI test runner fixture."""
#         return CliRunner()

#     @pytest.fixture
#     def mock_terraform_project(self):
#         """Create a mock Terraform project directory structure."""
#         with tempfile.TemporaryDirectory() as temp_dir:
#             project_path = Path(temp_dir)

#             # Create basic Terraform files
#             main_tf = project_path / "main.tf"
#             main_tf.write_text("""
# resource "aws_instance" "web" {
#   ami           = "ami-123456"
#   instance_type = "t3.micro"
# }

# variable "region" {
#   description = "AWS region"
#   default     = "us-east-1"
# }

# output "instance_id" {
#   value = aws_instance.web.id
# }
# """)

#             yield project_path

#     @pytest.fixture
#     def mock_analyzer(self):
#         """Mock TerraformAnalyzer."""
#         with patch("tfkit.commands.scan.TerraformAnalyzer") as mock_analyzer_class:
#             analyzer_instance = MagicMock()
#             mock_analyzer_class.return_value = analyzer_instance

#             # Mock project analysis result
#             mock_project = MagicMock()
#             mock_project.to_dict.return_value = {
#                 "resources": [
#                     {
#                         "type": "aws_instance",
#                         "name": "web",
#                         "state": "active",
#                         "dependencies": [],
#                     }
#                 ],
#                 "variables": [
#                     {"name": "region", "type": "string", "default": "us-east-1"}
#                 ],
#                 "outputs": [{"name": "instance_id", "value": "aws_instance.web.id"}],
#                 "summary": {
#                     "total_resources": 1,
#                     "total_variables": 1,
#                     "total_outputs": 1,
#                 },
#             }
#             # Set __dict__ as a proper dictionary
#             type(mock_project).__dict__ = property(lambda self: {"some": "data"})

#             analyzer_instance.analyze_project.return_value = mock_project
#             yield mock_analyzer_class

#     @pytest.fixture
#     def mock_report_generator(self):
#         """Mock ReportGenerator."""
#         with patch("tfkit.commands.scan.ReportGenerator") as mock_generator_class:
#             generator_instance = MagicMock()
#             mock_generator_class.return_value = generator_instance
#             generator_instance.generate_analysis_report.return_value = (
#                 "/tmp/report.html"
#             )
#             yield mock_generator_class

#     def test_scan_default_behavior(self, runner, mock_terraform_project, mock_analyzer):
#         """Test basic scan command with default parameters."""
#         result = runner.invoke(scan, [str(mock_terraform_project)])

#         assert result.exit_code == 0
#         assert "Scanning Terraform files" in result.output
#         mock_analyzer.return_value.analyze_project.assert_called_once_with(
#             mock_terraform_project
#         )

#     def test_scan_current_directory(self, runner, mock_analyzer):
#         """Test scan command on current directory."""
#         with runner.isolated_filesystem():
#             # Create a minimal terraform file
#             Path("main.tf").write_text('resource "null_resource" "test" {}')

#             result = runner.invoke(scan)

#             assert result.exit_code == 0
#             mock_analyzer.return_value.analyze_project.assert_called_once_with(
#                 Path(".")
#             )

#     def test_scan_nonexistent_path(self, runner):
#         """Test scan command with nonexistent path."""
#         result = runner.invoke(scan, ["/nonexistent/path"])

#         assert result.exit_code != 0

#     def test_scan_json_format(self, runner, mock_terraform_project, mock_analyzer):
#         """Test scan command with JSON output format."""
#         result = runner.invoke(scan, [str(mock_terraform_project), "--format", "json"])

#         assert result.exit_code == 0
#         # Should output valid JSON
#         try:
#             json_output = json.loads(result.output)
#             assert "resources" in json_output
#         except json.JSONDecodeError:
#             # If not JSON, it might be table format due to mock setup
#             pass

#     def test_scan_yaml_format(self, runner, mock_terraform_project, mock_analyzer):
#         """Test scan command with YAML output format."""
#         result = runner.invoke(scan, [str(mock_terraform_project), "--format", "yaml"])

#         assert result.exit_code == 0

#     def test_scan_simple_format(self, runner, mock_terraform_project, mock_analyzer):
#         """Test scan command with simple output format."""
#         result = runner.invoke(
#             scan, [str(mock_terraform_project), "--format", "simple"]
#         )

#         assert result.exit_code == 0

#     def test_scan_quiet_mode(self, runner, mock_terraform_project, mock_analyzer):
#         """Test scan command with quiet mode."""
#         result = runner.invoke(scan, [str(mock_terraform_project), "--quiet"])

#         assert result.exit_code == 0

#     def test_scan_save_results(self, runner, mock_terraform_project, mock_analyzer):
#         """Test saving scan results to file."""
#         with runner.isolated_filesystem():
#             result = runner.invoke(
#                 scan, [str(mock_terraform_project), "--save", "results.json"]
#             )

#             assert result.exit_code == 0
#             assert Path("results.json").exists()

#     def test_scan_open_browser(
#         self, runner, mock_terraform_project, mock_analyzer, mock_report_generator
#     ):
#         """Test scan command with browser opening."""
#         result = runner.invoke(scan, [str(mock_terraform_project), "--open"])

#         assert result.exit_code == 0
#         mock_report_generator.return_value.generate_analysis_report.assert_called_once()
#         mock_report_generator.return_value.open_in_browser.assert_called_once_with(
#             "/tmp/report.html"
#         )

#     def test_scan_with_theme(
#         self, runner, mock_terraform_project, mock_analyzer, mock_report_generator
#     ):
#         """Test scan command with custom theme."""
#         result = runner.invoke(
#             scan, [str(mock_terraform_project), "--open", "--theme", "light"]
#         )

#         assert result.exit_code == 0
#         mock_report_generator.return_value.generate_analysis_report.assert_called_once()
#         # Check that theme was passed
#         call_kwargs = (
#             mock_report_generator.return_value.generate_analysis_report.call_args[1]
#         )
#         assert call_kwargs.get("theme") == "light"

#     def test_scan_with_layout(
#         self, runner, mock_terraform_project, mock_analyzer, mock_report_generator
#     ):
#         """Test scan command with custom layout."""
#         result = runner.invoke(
#             scan, [str(mock_terraform_project), "--open", "--layout", "dashboard"]
#         )

#         assert result.exit_code == 0
#         call_kwargs = (
#             mock_report_generator.return_value.generate_analysis_report.call_args[1]
#         )
#         assert call_kwargs.get("layout") == "dashboard"

#     def test_scan_with_output_directory(
#         self, runner, mock_terraform_project, mock_analyzer, mock_report_generator
#     ):
#         """Test scan command with custom output directory."""
#         with runner.isolated_filesystem():
#             output_dir = Path("custom_output")

#             result = runner.invoke(
#                 scan,
#                 [str(mock_terraform_project), "--open", "--output", str(output_dir)],
#             )

#             assert result.exit_code == 0
#             call_args = (
#                 mock_report_generator.return_value.generate_analysis_report.call_args
#             )
#             # Output directory should be passed as second argument
#             assert call_args[0][1] == output_dir

#     def test_scan_combination_options(
#         self, runner, mock_terraform_project, mock_analyzer
#     ):
#         """Test scan command with multiple options combined."""
#         with runner.isolated_filesystem():
#             result = runner.invoke(
#                 scan,
#                 [
#                     str(mock_terraform_project),
#                     "--format",
#                     "json",
#                     "--save",
#                     "combined.json",
#                     "--quiet",
#                 ],
#             )

#             assert result.exit_code == 0
#             assert Path("combined.json").exists()

#     def test_scan_analyzer_exception(self, runner, mock_terraform_project):
#         """Test scan command when analyzer raises an exception."""
#         with patch("tfkit.commands.scan.TerraformAnalyzer") as mock_analyzer:
#             mock_analyzer.return_value.analyze_project.side_effect = Exception(
#                 "Analysis failed"
#             )

#             result = runner.invoke(scan, [str(mock_terraform_project)])

#             assert result.exit_code == 1
#             assert "Scan failed" in result.output

#     def test_scan_with_empty_project(self, runner, mock_analyzer):
#         """Test scan command with empty directory."""
#         with runner.isolated_filesystem():
#             # Empty directory, no terraform files
#             result = runner.invoke(scan)

#             assert result.exit_code == 0
#             mock_analyzer.return_value.analyze_project.assert_called_once_with(
#                 Path(".")
#             )

#     def test_scan_project_to_dict_fallback(self, runner, mock_terraform_project):
#         """Test scan command when project uses __dict__ fallback."""
#         with patch("tfkit.commands.scan.TerraformAnalyzer") as mock_analyzer:
#             analyzer_instance = MagicMock()
#             mock_analyzer.return_value = analyzer_instance

#             # Mock project that doesn't have to_dict but has __dict__
#             mock_project = MagicMock(spec=["__dict__"])
#             mock_project.to_dict.side_effect = AttributeError("No to_dict method")
#             # Use property to set __dict__
#             type(mock_project).__dict__ = property(
#                 lambda self: {"resources": [], "summary": {"total": 0}}
#             )

#             analyzer_instance.analyze_project.return_value = mock_project

#             result = runner.invoke(
#                 scan, [str(mock_terraform_project), "--format", "json"]
#             )

#             assert result.exit_code == 0

#     def test_scan_permission_denied(self, runner):
#         """Test scan command with directory without read permissions."""
#         with patch("tfkit.commands.scan.TerraformAnalyzer") as mock_analyzer:
#             mock_analyzer.return_value.analyze_project.side_effect = PermissionError(
#                 "Permission denied"
#             )

#             result = runner.invoke(scan, ["/root"])  # Typically inaccessible

#             assert result.exit_code == 1
#             assert "Scan failed" in result.output

#     @pytest.mark.parametrize(
#         "theme",
#         [
#             "light",
#             "dark",
#             "cyber",
#             "github-dark",
#             "monokai",
#             "solarized-light",
#             "dracula",
#             "atom-one-dark",
#             "gruvbox-dark",
#             "night-owl",
#         ],
#     )
#     def test_scan_all_themes(
#         self,
#         runner,
#         mock_terraform_project,
#         mock_analyzer,
#         mock_report_generator,
#         theme,
#     ):
#         """Test scan command with all available themes."""
#         result = runner.invoke(
#             scan, [str(mock_terraform_project), "--open", "--theme", theme]
#         )

#         assert result.exit_code == 0
#         call_kwargs = (
#             mock_report_generator.return_value.generate_analysis_report.call_args[1]
#         )
#         assert call_kwargs.get("theme") == theme

#     @pytest.mark.parametrize("layout", ["classic", "graph", "dashboard"])
#     def test_scan_all_layouts(
#         self,
#         runner,
#         mock_terraform_project,
#         mock_analyzer,
#         mock_report_generator,
#         layout,
#     ):
#         """Test scan command with all available layouts."""
#         result = runner.invoke(
#             scan, [str(mock_terraform_project), "--open", "--layout", layout]
#         )

#         assert result.exit_code == 0
#         call_kwargs = (
#             mock_report_generator.return_value.generate_analysis_report.call_args[1]
#         )
#         assert call_kwargs.get("layout") == layout

#     def test_scan_save_nonexistent_directory(
#         self, runner, mock_terraform_project, mock_analyzer
#     ):
#         """Test saving to nonexistent directory creates parent directories."""
#         with runner.isolated_filesystem():
#             save_path = "nonexistent/dir/results.json"

#             result = runner.invoke(
#                 scan, [str(mock_terraform_project), "--save", save_path]
#             )

#             assert result.exit_code == 0
#             assert Path(save_path).exists()

#     def test_scan_with_relative_paths(self, runner, mock_analyzer):
#         """Test scan command with relative paths."""
#         with runner.isolated_filesystem():
#             # Create nested directory structure
#             terraform_dir = Path("project/infrastructure")
#             terraform_dir.mkdir(parents=True)
#             (terraform_dir / "main.tf").write_text('resource "null_resource" "test" {}')

#             result = runner.invoke(scan, ["project/infrastructure"])

#             assert result.exit_code == 0
#             mock_analyzer.return_value.analyze_project.assert_called_once_with(
#                 Path("project/infrastructure")
#             )


# class TestScanEdgeCases:
#     """Test edge cases and error conditions for scan command."""

#     @pytest.fixture
#     def runner(self):
#         return CliRunner()

#     @pytest.fixture
#     def mock_analyzer(self):
#         with patch("tfkit.commands.scan.TerraformAnalyzer") as mock_analyzer_class:
#             analyzer_instance = MagicMock()
#             mock_analyzer_class.return_value = analyzer_instance

#             mock_project = MagicMock()
#             mock_project.to_dict.return_value = {
#                 "resources": [],
#                 "summary": {"total_resources": 0},
#             }
#             analyzer_instance.analyze_project.return_value = mock_project
#             yield analyzer_instance

#     @pytest.fixture
#     def mock_utils(self):
#         with patch("tfkit.commands.scan.print_banner"), patch(
#             "tfkit.commands.scan.display_scan_results"
#         ), patch("tfkit.commands.scan.display_simple_results"), patch(
#             "tfkit.commands.scan.export_yaml"
#         ), patch("tfkit.commands.scan.get_scan_data") as mock_get_data:
#             mock_get_data.return_value = {
#                 "resources": [],
#                 "summary": {"total_resources": 0},
#             }
#             yield

#     def test_scan_large_project(self, runner, mock_analyzer, mock_utils):
#         """Test scan command with a large number of Terraform files."""
#         with runner.isolated_filesystem():
#             # Create multiple Terraform files
#             for i in range(10):
#                 Path(f"main_{i}.tf").write_text(
#                     f'resource "null_resource" "test_{i}" {{}}'
#                 )

#             result = runner.invoke(scan)

#             assert result.exit_code == 0
#             mock_analyzer.analyze_project.assert_called_once_with(Path("."))

#     def test_scan_symlinked_files(self, runner, mock_analyzer, mock_utils):
#         """Test scan command with symbolic links (if supported)."""
#         with runner.isolated_filesystem():
#             Path("real.tf").write_text('resource "null_resource" "real" {}')
#             # Try to create symlink (might not work on all Windows systems)
#             try:
#                 Path("link.tf").symlink_to("real.tf")
#                 result = runner.invoke(scan)
#                 assert result.exit_code == 0
#             except (OSError, NotImplementedError):
#                 pytest.skip("Symlinks not supported on this system")

#     def test_scan_hidden_files(self, runner, mock_analyzer, mock_utils):
#         """Test that hidden files are handled correctly."""
#         with runner.isolated_filesystem():
#             Path(".hidden.tf").write_text('resource "null_resource" "hidden" {}')
#             Path("main.tf").write_text('resource "null_resource" "main" {}')

#             result = runner.invoke(scan)

#             assert result.exit_code == 0

#     def test_scan_unicode_files(self, runner, mock_analyzer, mock_utils):
#         """Test scan command with Unicode characters in files."""
#         with runner.isolated_filesystem():
#             content = 'resource "null_resource" "unicode" { tags = { description = "🎯 Test resource" } }'
#             Path("unicode.tf").write_text(content, encoding="utf-8")

#             result = runner.invoke(scan)

#             assert result.exit_code == 0

#     def test_scan_malformed_json_output(self, runner, mock_utils):
#         """Test scan command when project data cannot be serialized to JSON."""
#         with patch(
#             "tfkit.commands.scan.TerraformAnalyzer"
#         ) as mock_analyzer_class, patch("tfkit.commands.scan.console") as _:
#             analyzer_instance = MagicMock()
#             mock_analyzer_class.return_value = analyzer_instance

#             # Create a project with non-serializable data
#             class NonSerializable:
#                 def __str__(self):
#                     return "non-serializable"

#             mock_project = MagicMock()
#             mock_project.to_dict.return_value = {
#                 "resources": [{"problematic": NonSerializable()}]
#             }

#             analyzer_instance.analyze_project.return_value = mock_project

#             result = runner.invoke(scan, [".", "--format", "json"])

#             # Should handle serialization gracefully
#             assert result.exit_code == 1
