import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfkit.analyzer.models import (
    DependencyInfo,
    LocationInfo,
    ObjectState,
    ProviderInfo,
    ResourceType,
    TerraformObject,
)


class TestDependencyInfo:
    """Test DependencyInfo class functionality."""

    def test_basic_dependencies(self):
        """Test basic dependency tracking."""
        deps = DependencyInfo(
            explicit_dependencies=["var.region", "aws_vpc.main"],
            implicit_dependencies=["module.network"],
            dependent_objects=["aws_instance.web", "output.vpc_id"],
        )

        assert deps.dependency_count == 3
        assert deps.dependent_count == 2
        assert not deps.is_leaf
        assert not deps.is_unused
        assert not deps.is_isolated

    def test_leaf_object(self):
        """Test object with no dependencies."""
        deps = DependencyInfo(
            explicit_dependencies=[],
            dependent_objects=["output.instance_id"],
        )

        assert deps.is_leaf
        assert not deps.is_unused
        assert not deps.is_isolated

    def test_unused_object(self):
        """Test object with no dependents."""
        deps = DependencyInfo(
            explicit_dependencies=["var.region", "aws_vpc.main"],
            dependent_objects=[],
        )

        assert not deps.is_leaf
        assert deps.is_unused
        assert not deps.is_isolated

    def test_isolated_object(self):
        """Test completely isolated object."""
        deps = DependencyInfo()

        assert deps.is_leaf
        assert deps.is_unused
        assert deps.is_isolated

    def test_circular_dependencies(self):
        """Test circular dependency detection."""
        deps = DependencyInfo(
            explicit_dependencies=["aws_instance.a"],
            circular_dependencies=["aws_instance.a", "aws_instance.b"],
        )

        assert deps.has_circular_deps
        assert len(deps.circular_dependencies) == 2

    def test_missing_dependencies(self):
        """Test missing dependency tracking."""
        deps = DependencyInfo(
            missing_dependencies=["undefined.var", "unknown.resource"]
        )

        assert deps.has_missing_deps
        assert len(deps.missing_dependencies) == 2

    def test_complexity_score_calculation(self):
        """Test complexity score calculation."""
        # Base case
        deps = DependencyInfo(
            explicit_dependencies=["a", "b", "c"],  # 3 deps
            dependent_objects=["x", "y"],  # 2 dependents
        )
        expected_score = 3 + (2 * 0.5)  # 3 + 1 = 4
        assert deps.complexity_score == expected_score

        # With circular dependencies
        deps_circular = DependencyInfo(
            explicit_dependencies=["a", "b", "c"],
            dependent_objects=["x", "y"],
            circular_dependencies=["a", "b"],
        )
        expected_circular = expected_score * 1.5  # 4 * 1.5 = 6
        assert deps_circular.complexity_score == expected_circular

        # With missing dependencies
        deps_missing = DependencyInfo(
            explicit_dependencies=["a", "b", "c"],
            dependent_objects=["x", "y"],
            missing_dependencies=["undefined"],
        )
        expected_missing = expected_score * 2.0  # 4 * 2 = 8
        assert deps_missing.complexity_score == expected_missing

        # Combined penalties
        deps_both = DependencyInfo(
            explicit_dependencies=["a", "b", "c"],
            dependent_objects=["x", "y"],
            circular_dependencies=["a", "b"],
            missing_dependencies=["undefined"],
        )
        expected_both = expected_score * 1.5 * 2.0  # 4 * 1.5 * 2 = 12
        assert deps_both.complexity_score == expected_both


class TestTerraformObjectStateComputation:
    """Test Terraform object state computation logic."""

    @pytest.fixture
    def mock_objects_dict(self):
        """Create a mock dictionary of all objects for testing."""
        return {}

    def create_test_object(self, resource_type: ResourceType, **kwargs):
        """Helper to create test TerraformObject instances."""
        defaults = {
            "type": resource_type,
            "name": "test",
            "full_name": f"{resource_type.value}.test",
            "location": LocationInfo("main.tf", 1),
            "dependency_info": DependencyInfo(),
        }
        defaults.update(kwargs)
        return TerraformObject(**defaults)

    def test_variable_states(self, mock_objects_dict):
        """Test variable state computation."""
        # Unused variable
        var_unused = self.create_test_object(
            ResourceType.VARIABLE,
            dependency_info=DependencyInfo(dependent_objects=[]),
        )
        var_unused.set_all_objects_cache(mock_objects_dict)
        assert var_unused.state == ObjectState.UNUSED
        assert "never used" in var_unused.state_reason.lower()

        # Used variable
        var_used = self.create_test_object(
            ResourceType.VARIABLE,
            dependency_info=DependencyInfo(dependent_objects=["aws_instance.web"]),
        )
        var_used.set_all_objects_cache(mock_objects_dict)
        assert var_used.state == ObjectState.INPUT
        assert "used by" in var_used.state_reason.lower()

    def test_module_states(self, mock_objects_dict):
        """Test module state computation."""
        # Isolated module
        module_isolated = self.create_test_object(
            ResourceType.MODULE,
            source="./modules/vpc",
            dependency_info=DependencyInfo(),
        )
        module_isolated.set_all_objects_cache(mock_objects_dict)
        assert module_isolated.state == ObjectState.ISOLATED

        # Active module
        module_active = self.create_test_object(
            ResourceType.MODULE,
            source="./modules/vpc",
            dependency_info=DependencyInfo(explicit_dependencies=["var.region"]),
        )
        module_active.set_all_objects_cache(mock_objects_dict)
        assert module_active.state == ObjectState.ACTIVE

    def test_provider_states(self, mock_objects_dict):
        """Test provider state computation."""
        # Unused provider
        provider_unused = self.create_test_object(
            ResourceType.PROVIDER,
            dependency_info=DependencyInfo(),
        )
        provider_unused.set_all_objects_cache(mock_objects_dict)
        assert provider_unused.state == ObjectState.UNUSED

    def test_missing_dependency_state(self, mock_objects_dict):
        """Test state when missing dependencies are present."""
        obj_with_missing_deps = self.create_test_object(
            ResourceType.RESOURCE,
            dependency_info=DependencyInfo(
                missing_dependencies=["undefined.resource", "var.missing_var"]
            ),
        )
        obj_with_missing_deps.set_all_objects_cache(mock_objects_dict)
        assert obj_with_missing_deps.state == ObjectState.MISSING_DEPENDENCY
        assert "undefined" in obj_with_missing_deps.state_reason.lower()

    def test_circular_dependency_state(self, mock_objects_dict):
        """Test state when circular dependencies are present."""
        obj_with_circular_deps = self.create_test_object(
            ResourceType.RESOURCE,
            dependency_info=DependencyInfo(
                circular_dependencies=["resource.a", "resource.b"]
            ),
        )
        obj_with_circular_deps.set_all_objects_cache(mock_objects_dict)
        assert obj_with_circular_deps.state == ObjectState.BROKEN
        assert "circular" in obj_with_circular_deps.state_reason.lower()

    def test_good_practices_detection(self):
        """Test best practices detection."""
        # Object with good practices
        obj_good = self.create_test_object(
            ResourceType.RESOURCE,
            description="This is a well-described resource with proper documentation",
            tags={"Environment": "prod", "Team": "platform"},
            name="well_named_resource",
        )
        assert obj_good._has_good_practices()

        # Object with poor practices
        obj_poor = self.create_test_object(
            ResourceType.RESOURCE,
            description="",  # No description
            tags={},  # No tags
            name="Badly-Named-Resource-With-Inconsistent-Naming",  # Inconsistent naming
        )
        assert not obj_poor._has_good_practices()


class TestTerraformObjectSerialization:
    """Test Terraform object serialization to dictionaries."""

    def test_to_dict_completeness(self):
        """Test that to_dict includes all important fields."""
        obj = TerraformObject(
            type=ResourceType.RESOURCE,
            name="web_server",
            full_name="aws_instance.web_server",
            location=LocationInfo("main.tf", 10),
            resource_type="aws_instance",
            provider_info=ProviderInfo("aws"),
            description="Web server instance",
            tags={"Environment": "prod"},
            attributes={"instance_type": "t3.micro", "ami": "ami-123456"},
        )

        result = obj.to_dict()

        # Check top-level fields
        assert result["type"] == "resource"
        assert result["name"] == "web_server"
        assert result["full_name"] == "aws_instance.web_server"
        assert result["resource_type"] == "aws_instance"
        assert result["provider"] == "aws"
        assert result["description"] == "Web server instance"
        assert result["tags"] == {"Environment": "prod"}

        # Check nested structures
        assert "location" in result
        assert "dependencies" in result
        assert "metrics" in result
        assert "attributes" in result

        # Check dependencies structure
        deps = result["dependencies"]
        assert "explicit" in deps
        assert "implicit" in deps
        assert "dependents" in deps
        assert "circular" in deps
        assert "missing" in deps
        assert "counts" in deps

        # Check metrics structure
        metrics = result["metrics"]
        assert "complexity_score" in metrics
        assert "has_circular_deps" in metrics
        assert "has_missing_deps" in metrics
        assert "fan_in" in metrics
        assert "fan_out" in metrics

    def test_to_dict_with_dependencies(self):
        """Test serialization with dependency information."""
        dep_info = DependencyInfo(
            explicit_dependencies=["var.region", "aws_vpc.main"],
            implicit_dependencies=["module.network"],
            dependent_objects=["aws_instance.web", "output.vpc_id"],
            circular_dependencies=[],
            missing_dependencies=["undefined.var"],
        )

        obj = TerraformObject(
            type=ResourceType.RESOURCE,
            name="test",
            full_name="aws_instance.test",
            location=LocationInfo("main.tf", 1),
            dependency_info=dep_info,
        )

        result = obj.to_dict()
        deps = result["dependencies"]

        assert deps["explicit"] == ["var.region", "aws_vpc.main"]
        assert deps["implicit"] == ["module.network"]
        assert deps["dependents"] == ["aws_instance.web", "output.vpc_id"]
        assert deps["circular"] == []
        assert deps["missing"] == ["undefined.var"]
        assert deps["counts"]["dependencies"] == 3
        assert deps["counts"]["dependents"] == 2

    def test_state_in_serialization(self):
        """Test that state information is included in serialization."""
        obj = TerraformObject(
            type=ResourceType.VARIABLE,
            name="region",
            full_name="var.region",
            location=LocationInfo("variables.tf", 1),
            dependency_info=DependencyInfo(),  # Unused variable
        )

        result = obj.to_dict()

        assert "state" in result
        assert "state_reason" in result
        # State should be computed and included
        assert result["state"] == ObjectState.UNUSED.value


class TestProviderInfo:
    """Test ProviderInfo functionality."""

    def test_full_provider_reference(self):
        """Test full provider reference generation."""
        # Provider without alias
        provider1 = ProviderInfo("aws")
        assert provider1.full_provider_reference == "aws"

    def test_is_configured(self):
        """Test provider configuration detection."""
        # Unconfigured provider
        provider1 = ProviderInfo("aws")
        assert not provider1.is_configured

        # Configured provider
        provider2 = ProviderInfo("aws", provider_config={"region": "us-east-1"})
        assert provider2.is_configured


class TestLocationInfo:
    """Test LocationInfo functionality."""

    def test_to_dict(self):
        """Test location info serialization."""
        location = LocationInfo(
            file_path="/terraform/main.tf",
            line_number=42,
            relative_path="main.tf",
            module_depth=1,
        )

        result = location.to_dict()

        assert result["file_path"] == "/terraform/main.tf"
        assert result["line_number"] == 42
        assert result["relative_path"] == "main.tf"
        assert result["module_depth"] == 1


def test_object_state_enum_completeness():
    """Test that all ObjectState values are properly defined."""
    expected_states = [
        "ACTIVE",
        "HEALTHY",
        "INTEGRATED",
        "INPUT",
        "OUTPUT_INTERFACE",
        "CONFIGURATION",
        "LEAF",
        "HUB",
        "ISOLATED",
        "UNUSED",
        "ORPHANED",
        "UNDERUTILIZED",
        "COMPLEX",
        "BROKEN",
        "INCOMPLETE",
        "MISSING_DEPENDENCY",
        "EXTERNAL_DATA",
    ]

    actual_states = [state.name for state in ObjectState]

    for expected_state in expected_states:
        assert expected_state in actual_states, f"Missing state: {expected_state}"


def test_resource_type_enum_completeness():
    """Test that all ResourceType values are properly defined."""
    expected_types = [
        "RESOURCE",
        "DATA",
        "MODULE",
        "VARIABLE",
        "OUTPUT",
        "PROVIDER",
        "TERRAFORM",
        "LOCAL",
    ]

    actual_types = [rtype.name for rtype in ResourceType]

    for expected_type in expected_types:
        assert expected_type in actual_types, f"Missing resource type: {expected_type}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
