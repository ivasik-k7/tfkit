import os
from pathlib import Path

import pytest

from tfkit.analyzer.models import DependencyInfo, ResourceType
from tfkit.analyzer.terraform_analyzer import DependencyExtractor, TerraformAnalyzer


class TestTerraformAnalyzer:
    def test_analyzer_initialization(self):
        """Test that analyzer can be initialized"""
        analyzer = TerraformAnalyzer()
        assert analyzer is not None
        assert analyzer.project is None

    def test_analyze_project_structure(self):
        """Test basic project structure analysis"""
        analyzer = TerraformAnalyzer()
        project_path = "examples/project"

        if os.path.exists(project_path):
            result = analyzer.analyze_project(project_path)
            assert result is not None
            assert hasattr(result, "all_objects")
            assert hasattr(result, "metadata")
            assert result.metadata.total_files > 0

    def test_analyze_nonexistent_directory(self):
        """Test analysis of non-existent directory"""
        analyzer = TerraformAnalyzer()
        with pytest.raises(ValueError, match="Project path does not exist"):
            analyzer.analyze_project("non_existent_directory")

    def test_analyze_empty_directory(self, tmp_path):
        """Test analysis of directory with no Terraform files"""
        analyzer = TerraformAnalyzer()
        with pytest.raises(ValueError, match="No Terraform files found"):
            analyzer.analyze_project(str(tmp_path))

    def test_find_terraform_files(self):
        """Test Terraform file discovery"""
        analyzer = TerraformAnalyzer()
        project_path = Path("examples/project")

        if project_path.exists():
            files = analyzer._find_terraform_files(project_path)
            assert len(files) > 0
            assert all(f.endswith((".tf", ".tf.json")) for f in files)

    @pytest.mark.skipif(not os.path.exists("examples"), reason="Examples not available")
    def test_parse_terraform_files(self):
        """Test Terraform file parsing"""
        analyzer = TerraformAnalyzer()
        project_path = "examples"
        project = analyzer.analyze_project(project_path)

        assert len(project.all_objects) > 0

        object_types = [obj.type for obj in project.all_objects.values()]
        assert (
            ResourceType.RESOURCE in object_types
            or ResourceType.VARIABLE in object_types
        )


class TestDependencyExtractor:
    def test_extractor_initialization(self):
        """Test dependency extractor initialization"""
        extractor = DependencyExtractor({})
        assert extractor is not None
        assert extractor.all_objects == {}
        assert extractor.defined_names == set()

    def test_extract_from_empty_config(self):
        """Test dependency extraction from empty config"""
        extractor = DependencyExtractor({})
        dep_info = extractor.extract(None)
        assert isinstance(dep_info, DependencyInfo)
        assert dep_info.explicit_dependencies == []
        assert dep_info.implicit_dependencies == []
        assert dep_info.missing_dependencies == []

    def test_extract_from_string(self):
        """Test dependency extraction from string"""
        extractor = DependencyExtractor({})
        config = "var.example"
        dep_info = extractor.extract(config)
        assert isinstance(dep_info, DependencyInfo)

    def test_normalize_reference(self):
        """Test reference normalization"""
        extractor = DependencyExtractor({})

        test_cases = [
            ("var.name", "var.name"),
            ('"var.name"', "var.name"),
            ("'var.name'", "var.name"),
            ("var.name.", "var.name"),
            ("  var.name  ", "var.name"),
        ]

        for input_ref, expected in test_cases:
            assert extractor._normalize_reference(input_ref) == expected


def test_debug_is_valid_reference():
    """Debug the reference validation"""
    extractor = DependencyExtractor({})

    test_cases = [
        ("var.", "Should be invalid - trailing dot"),
        ("var.name", "Should be valid"),
        ("var", "Should be invalid - no name"),
        ("", "Should be invalid - empty"),
    ]

    for ref, description in test_cases:
        result = extractor._is_valid_reference(ref)
        print(f"'{ref}' -> {result} ({description})")
        print(f"  Parts: {ref.split('.')}")
        print(f"  Length: {len(ref.split('.'))}")

    def test_serialize_config(self):
        """Test config serialization"""
        extractor = DependencyExtractor({})

        config_dict = {"key": "value", "nested": {"inner": "var.test"}}
        result = extractor._serialize_config(config_dict)
        assert "var.test" in result

        config_list = ["var.test1", "var.test2"]
        result = extractor._serialize_config(config_list)
        assert "var.test1" in result

        config_str = "var.test"
        result = extractor._serialize_config(config_str)
        assert "var.test" in result


class TestObjectFactory:
    def test_factory_initialization(self):
        """Test object factory initialization"""
        from tfkit.analyzer.terraform_analyzer import FileParser, ObjectFactory

        file_parser = FileParser()
        factory = ObjectFactory(file_parser)
        assert factory is not None
        assert factory.file_parser == file_parser

    def test_extract_provider_from_type(self):
        """Test provider extraction from resource type"""
        from tfkit.analyzer.terraform_analyzer import FileParser, ObjectFactory

        file_parser = FileParser()
        factory = ObjectFactory(file_parser)

        test_cases = [
            ("aws_instance", "aws"),
            ("google_compute_instance", "google"),
            ("azurerm_virtual_machine", "azurerm"),
            ("invalid", "invalid"),
            ("", None),
            (None, None),
        ]

        for resource_type, expected in test_cases:
            assert factory._extract_provider_from_type(resource_type) == expected
