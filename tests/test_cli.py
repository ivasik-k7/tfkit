# """Test CLI commands"""

# import pytest
# from click.testing import CliRunner

# from tfkit.cli import main


# class TestCLI:
#     def setup_method(self):
#         self.runner = CliRunner()

#     def test_cli_help(self):
#         """Test that CLI help works"""
#         result = self.runner.invoke(main, ["--help"])
#         assert result.exit_code == 0
#         assert "tfkit" in result.output
#         assert "scan" in result.output
#         assert "validate" in result.output

#     def test_scan_command_help(self):
#         """Test scan command help"""
#         result = self.runner.invoke(main, ["scan", "--help"])
#         assert result.exit_code == 0

#     def test_validate_command_help(self):
#         """Test validate command help"""
#         result = self.runner.invoke(main, ["validate", "--help"])
#         assert result.exit_code == 0

#     def test_scan_with_examples(self):
#         """Test scan command with examples directory"""
#         result = self.runner.invoke(main, ["scan", "examples/project"])
#         assert result.exit_code in [0, 1]
