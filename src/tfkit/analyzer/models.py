"""Enhanced data models for Terraform analysis with clear state management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResourceType(Enum):
    """Types of Terraform objects."""

    RESOURCE = "resource"
    DATA = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    TERRAFORM = "terraform"
    LOCAL = "local"


class ObjectState(Enum):
    """
    Semantic states for Terraform objects based on their role and usage.

    ACTIVE: Object is properly integrated into the infrastructure
    UNUSED: Object exists but is not referenced by anything
    ISOLATED: Object has no dependencies or dependents (standalone)
    INPUT: Object serves as an input (variables, data sources)
    OUTPUT_INTERFACE: Object exports values for external consumption
    CONFIGURATION: Object configures system behavior (providers, terraform blocks)
    ORPHANED: Object depends on others but nothing uses it
    INCOMPLETE: Object is missing required dependencies or configuration
    """

    ACTIVE = "active"
    UNUSED = "unused"
    ISOLATED = "isolated"
    INPUT = "input"
    OUTPUT_INTERFACE = "output_interface"
    CONFIGURATION = "configuration"
    ORPHANED = "orphaned"
    INCOMPLETE = "incomplete"


@dataclass
class DependencyInfo:
    """Structured information about an object's dependencies."""

    # Dependencies this object needs
    explicit_dependencies: List[str] = field(default_factory=list)
    implicit_dependencies: List[str] = field(default_factory=list)

    # Objects that depend on this object
    dependent_objects: List[str] = field(default_factory=list)

    @property
    def all_dependencies(self) -> List[str]:
        """Get all dependencies (explicit + implicit)."""
        return self.explicit_dependencies + self.implicit_dependencies

    @property
    def dependency_count(self) -> int:
        """Total number of dependencies."""
        return len(self.all_dependencies)

    @property
    def dependent_count(self) -> int:
        """Number of objects that depend on this object."""
        return len(self.dependent_objects)

    @property
    def is_leaf(self) -> bool:
        """True if object has no dependencies."""
        return self.dependency_count == 0

    @property
    def is_unused(self) -> bool:
        """True if nothing depends on this object."""
        return self.dependent_count == 0

    @property
    def is_isolated(self) -> bool:
        """True if object has no dependencies and no dependents."""
        return self.is_leaf and self.is_unused


@dataclass
class ProviderInfo:
    """Provider-specific information."""

    provider_name: str
    provider_alias: Optional[str] = None
    provider_version: Optional[str] = None

    @property
    def full_provider_reference(self) -> str:
        """Get full provider reference including alias."""
        if self.provider_alias:
            return f"{self.provider_name}.{self.provider_alias}"
        return self.provider_name


@dataclass
class LocationInfo:
    """Location information for an object."""

    file_path: str
    line_number: int
    relative_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "relative_path": self.relative_path,
        }


@dataclass
class TerraformObject:
    """
    Enhanced Terraform object with clear state management and structured data.
    """

    type: ResourceType
    name: str
    full_name: str

    # Location
    location: LocationInfo

    # Dependencies (structured)
    dependency_info: DependencyInfo = field(default_factory=DependencyInfo)

    # Attributes (raw configuration)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Type-specific information
    resource_type: Optional[str] = None  # e.g., "aws_instance"
    provider_info: Optional[ProviderInfo] = None

    # Variable-specific
    variable_type: Optional[str] = None
    default_value: Optional[Any] = None

    # Output-specific
    sensitive: bool = False

    # Module-specific
    source: Optional[str] = None

    # Common metadata
    description: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    # State (computed)
    _state: Optional[ObjectState] = None
    _state_reason: Optional[str] = None

    @property
    def state(self) -> ObjectState:
        """Get the computed state of this object."""
        if self._state is None:
            self._state, self._state_reason = self._compute_state()
        return self._state

    @property
    def state_reason(self) -> str:
        """Get the reason for the current state."""
        if self._state_reason is None:
            self._state, self._state_reason = self._compute_state()
        return self._state_reason

    def invalidate_state(self) -> None:
        """Invalidate cached state (call when dependencies change)."""
        self._state = None
        self._state_reason = None

    def _compute_state(self) -> tuple[ObjectState, str]:
        """
        Compute the semantic state of this object based on its type and dependencies.

        Returns:
            Tuple of (ObjectState, reason_string)
        """
        dep_info = self.dependency_info

        # Variables are always inputs
        if self.type == ResourceType.VARIABLE:
            if dep_info.is_unused:
                return ObjectState.UNUSED, "Variable declared but never referenced"
            return (
                ObjectState.INPUT,
                f"Input variable used by {dep_info.dependent_count} object(s)",
            )

        # Outputs are always output interfaces
        if self.type == ResourceType.OUTPUT:
            if dep_info.is_leaf:
                return ObjectState.INCOMPLETE, "Output has no value source"
            return (
                ObjectState.OUTPUT_INTERFACE,
                "Value exported for external consumption",
            )

        # Providers and terraform blocks are configuration
        if self.type in (ResourceType.PROVIDER, ResourceType.TERRAFORM):
            if self.type == ResourceType.PROVIDER and dep_info.is_unused:
                return ObjectState.UNUSED, "Provider configured but not used"
            return ObjectState.CONFIGURATION, "System configuration"

        # Data sources are external inputs
        if self.type == ResourceType.DATA:
            if dep_info.is_unused:
                return ObjectState.UNUSED, "Data source declared but never referenced"
            return (
                ObjectState.INPUT,
                f"External data source for {dep_info.dependent_count} object(s)",
            )

        # For resources, modules, and locals - analyze connection patterns
        if dep_info.is_isolated:
            return ObjectState.ISOLATED, "Not connected to any other infrastructure"

        if dep_info.is_unused:
            if dep_info.dependency_count > 0:
                return (
                    ObjectState.ORPHANED,
                    f"Has {dep_info.dependency_count} dependencies but is not used",
                )
            return ObjectState.UNUSED, "Not referenced by any other object"

        # Has dependencies and is used - this is healthy/active
        return (
            ObjectState.ACTIVE,
            f"Integrated with {dep_info.dependency_count} dep(s), used by {dep_info.dependent_count} object(s)",
        )

    @property
    def provider_prefix(self) -> Optional[str]:
        """Extract provider prefix from resource_type (e.g., 'aws' from 'aws_instance')."""
        if self.resource_type:
            parts = self.resource_type.split("_", 1)
            if parts:
                return parts[0]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "name": self.name,
            "full_name": self.full_name,
            "location": self.location.to_dict(),
            "state": self.state.value,
            "state_reason": self.state_reason,
            "resource_type": self.resource_type,
            "provider": self.provider_info.full_provider_reference
            if self.provider_info
            else None,
            "source": self.source,
            "variable_type": self.variable_type,
            "default_value": self.default_value,
            "description": self.description,
            "sensitive": self.sensitive,
            "tags": self.tags,
            "dependencies": {
                "explicit": self.dependency_info.explicit_dependencies,
                "implicit": self.dependency_info.implicit_dependencies,
                "dependents": self.dependency_info.dependent_objects,
                "counts": {
                    "dependencies": self.dependency_info.dependency_count,
                    "dependents": self.dependency_info.dependent_count,
                },
            },
            "attributes": self.attributes,
        }

    @classmethod
    def create_resource(
        cls,
        name: str,
        full_name: str,
        resource_type: str,
        location: LocationInfo,
        attributes: Dict[str, Any],
        provider: Optional[str] = None,
    ) -> "TerraformObject":
        """Factory method for creating resource objects."""
        provider_info = None
        if provider:
            provider_info = ProviderInfo(provider_name=provider)

        return cls(
            type=ResourceType.RESOURCE,
            name=name,
            full_name=full_name,
            location=location,
            resource_type=resource_type,
            attributes=attributes,
            provider_info=provider_info,
        )

    @classmethod
    def create_variable(
        cls,
        name: str,
        full_name: str,
        location: LocationInfo,
        variable_type: Optional[str] = None,
        default_value: Optional[Any] = None,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "TerraformObject":
        """Factory method for creating variable objects."""
        return cls(
            type=ResourceType.VARIABLE,
            name=name,
            full_name=full_name,
            location=location,
            variable_type=variable_type,
            default_value=default_value,
            description=description,
            attributes=attributes or {},
        )

    @classmethod
    def create_output(
        cls,
        name: str,
        full_name: str,
        location: LocationInfo,
        sensitive: bool = False,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "TerraformObject":
        """Factory method for creating output objects."""
        return cls(
            type=ResourceType.OUTPUT,
            name=name,
            full_name=full_name,
            location=location,
            sensitive=sensitive,
            description=description,
            attributes=attributes or {},
        )
