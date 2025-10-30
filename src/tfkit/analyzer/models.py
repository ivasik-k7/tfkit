import re
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
    Semantic states for Terraform objects based on comprehensive analysis.
    """

    # Healthy states
    ACTIVE = "active"
    HEALTHY = "healthy"
    INTEGRATED = "integrated"

    # Input/Output states
    INPUT = "input"
    OUTPUT_INTERFACE = "output_interface"
    CONFIGURATION = "configuration"

    # Structural states
    LEAF = "leaf"
    HUB = "hub"
    ISOLATED = "isolated"

    # Warning states
    UNUSED = "unused"
    ORPHANED = "orphaned"
    UNDERUTILIZED = "underutilized"
    COMPLEX = "complex"

    # Error states
    BROKEN = "broken"
    INCOMPLETE = "incomplete"
    MISSING_DEPENDENCY = "missing_dependency"

    # Special states
    EXTERNAL_DATA = "external_data"


@dataclass
class DependencyInfo:
    """Enhanced dependency information with comprehensive tracking."""

    # Core dependencies
    explicit_dependencies: List[str] = field(default_factory=list)
    implicit_dependencies: List[str] = field(default_factory=list)
    dependent_objects: List[str] = field(default_factory=list)

    # Advanced dependency tracking
    circular_dependencies: List[str] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    conditional_dependencies: List[str] = field(default_factory=list)

    @property
    def all_dependencies(self) -> List[str]:
        """All dependencies (explicit + implicit)."""
        return self.explicit_dependencies + self.implicit_dependencies

    @property
    def dependency_count(self) -> int:
        """Total number of dependencies."""
        return len(self.all_dependencies)

    @property
    def dependent_count(self) -> int:
        """Number of objects depending on this one."""
        return len(self.dependent_objects)

    @property
    def is_leaf(self) -> bool:
        """True if object has no dependencies."""
        return self.dependency_count == 0

    @property
    def is_unused(self) -> bool:
        """True if no objects depend on this one."""
        return self.dependent_count == 0

    @property
    def is_isolated(self) -> bool:
        """True if object has no dependencies and no dependents."""
        return self.is_leaf and self.is_unused

    @property
    def has_circular_deps(self) -> bool:
        """True if circular dependencies detected."""
        return len(self.circular_dependencies) > 0

    @property
    def has_missing_deps(self) -> bool:
        """True if has missing/undefined dependencies."""
        return len(self.missing_dependencies) > 0

    @property
    def complexity_score(self) -> float:
        """
        Calculate complexity based on dependency patterns.

        Formula:
        - Base: dependency count + (dependent count * 0.5)
        - Circular deps: multiply by 1.5
        - Missing deps: multiply by 2.0
        """
        base_score = self.dependency_count + (self.dependent_count * 0.5)

        if self.has_circular_deps:
            base_score *= 1.5
        if self.has_missing_deps:
            base_score *= 2.0

        return base_score

    @property
    def fan_in(self) -> int:
        """Number of objects this depends on (incoming edges)."""
        return self.dependency_count

    @property
    def fan_out(self) -> int:
        """Number of objects depending on this (outgoing edges)."""
        return self.dependent_count


@dataclass
class ResourceMetrics:
    """Enhanced metrics for resource analysis."""

    # Dependency metrics
    dependency_fan_in: int = 0
    dependency_fan_out: int = 0
    dependency_ratio: float = 0.0

    # Complexity metrics
    cyclomatic_complexity: int = 1
    configuration_parameters: int = 0
    nested_depth: int = 0

    # Usage metrics
    reference_count: int = 0
    cross_module_references: int = 0

    # Quality metrics
    documentation_score: int = 0
    naming_consistency: float = 0.0


@dataclass
class ProviderInfo:
    """Provider-specific information."""

    provider_name: str
    provider_alias: Optional[str] = None
    provider_version: Optional[str] = None
    provider_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_provider_reference(self) -> str:
        """Full provider reference including alias if present."""
        if self.provider_alias:
            return f"{self.provider_name}.{self.provider_alias}"
        return self.provider_name

    @property
    def is_configured(self) -> bool:
        """True if provider has configuration."""
        return len(self.provider_config) > 0


@dataclass
class LocationInfo:
    """Location information for an object."""

    file_path: str
    line_number: int
    relative_path: Optional[str] = None
    module_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "relative_path": self.relative_path,
            "module_depth": self.module_depth,
        }


@dataclass
class TerraformObject:
    """
    Comprehensive Terraform object with state management and metrics.
    """

    type: ResourceType
    name: str
    full_name: str
    location: LocationInfo

    # Dependencies (structured)
    dependency_info: DependencyInfo = field(default_factory=DependencyInfo)

    # Enhanced metrics
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)

    # Attributes (raw configuration)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Type-specific information
    resource_type: Optional[str] = None
    provider_info: Optional[ProviderInfo] = None

    # Variable-specific
    variable_type: Optional[str] = None
    default_value: Optional[Any] = None
    nullable: bool = True
    sensitive: bool = False

    # Output-specific
    output_value: Optional[Any] = None

    # Module-specific
    source: Optional[str] = None
    module_version: Optional[str] = None

    # Common metadata
    description: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    lifecycle_rules: Dict[str, Any] = field(default_factory=dict)

    # State (computed lazily)
    _state: Optional[ObjectState] = None
    _state_reason: Optional[str] = None
    _all_objects_cache: Optional[Dict[str, "TerraformObject"]] = None

    def set_all_objects_cache(self, all_objects: Dict[str, "TerraformObject"]) -> None:
        """Set reference to all objects for state computation."""
        self._all_objects_cache = all_objects

    @property
    def state(self) -> ObjectState:
        """Get the computed state (lazy evaluation)."""
        if self._state is None:
            self._state, self._state_reason = self._compute_state()
        return self._state

    @property
    def state_reason(self) -> str:
        """Get the reason for the computed state."""
        if self._state_reason is None:
            self._state, self._state_reason = self._compute_state()
        return self._state_reason

    def invalidate_state(self) -> None:
        """Invalidate cached state to force recomputation."""
        self._state = None
        self._state_reason = None

    def _compute_state(self) -> tuple[ObjectState, str]:
        """
        Compute semantic state using comprehensive criteria.

        Priority order:
        1. Critical errors (missing deps, circular deps, broken config)
        2. Type-specific logic (resources, variables, outputs, data sources)
        3. Structural patterns (isolated, leaf, hub)
        4. Quality assessment (healthy, integrated, active)

        Returns:
            Tuple of (ObjectState, reason_string)
        """
        dep_info = self.dependency_info
        dep_count = dep_info.dependency_count
        dependent_count = dep_info.dependent_count
        complexity = dep_info.complexity_score

        # ==================== CRITICAL ERRORS ====================

        # Missing dependencies (undefined references)
        if dep_info.has_missing_deps:
            missing_count = len(dep_info.missing_dependencies)
            missing_names = ", ".join(dep_info.missing_dependencies[:3])
            if missing_count > 3:
                missing_names += f" (+{missing_count - 3} more)"
            return (
                ObjectState.MISSING_DEPENDENCY,
                f"References {missing_count} undefined object(s): {missing_names}",
            )

        # Circular dependencies
        if dep_info.has_circular_deps:
            cycle_length = len(set(dep_info.circular_dependencies))
            return (
                ObjectState.BROKEN,
                f"Circular dependency detected involving {cycle_length} object(s)",
            )

        # Extreme complexity
        if complexity > 30:
            return (
                ObjectState.BROKEN,
                f"Critical complexity level (score: {complexity:.1f})",
            )

        # Incomplete configuration
        if self._is_incomplete():
            reason = self._get_incompleteness_reason()
            return ObjectState.INCOMPLETE, reason

        # ==================== DEPENDENCY CHAIN ANALYSIS ====================

        # Check if this object is part of an unused dependency chain
        if self._is_in_unused_chain():
            chain_type = "local" if self.type == ResourceType.LOCAL else "computation"
            return (
                ObjectState.UNUSED,
                f"{chain_type} value computed as part of unused dependency chain",
            )

        # ==================== TYPE-SPECIFIC LOGIC ====================

        # RESOURCES (aws_instance, aws_security_group, etc.)
        if self.type == ResourceType.RESOURCE:
            # Resources create infrastructure - they're never "unused" just because outputs aren't consumed
            if dep_count == 0 and dependent_count == 0:
                return (
                    ObjectState.ISOLATED,
                    "Resource not connected to any infrastructure",
                )

            if dep_count > 0 and dependent_count == 0:
                # This is normal for infrastructure resources!
                if self._is_core_infrastructure():
                    return (
                        ObjectState.ACTIVE,
                        f"Core infrastructure using {dep_count} dependencies",
                    )
                return (
                    ObjectState.ACTIVE,
                    f"Infrastructure resource using {dep_count} dependencies",
                )

            if dep_count == 0 and dependent_count > 0:
                return (
                    ObjectState.LEAF,
                    f"Independent infrastructure used by {dependent_count} consumer(s)",
                )

            # Resource with both inputs and consumers
            return (
                ObjectState.INTEGRATED,
                f"Infrastructure using {dep_count} deps, used by {dependent_count} consumer(s)",
            )

        # VARIABLES
        if self.type == ResourceType.VARIABLE:
            if dependent_count == 0:
                if self.default_value is not None:
                    return (
                        ObjectState.UNUSED,
                        "Variable declared with default but never referenced",
                    )
                return (ObjectState.UNUSED, "Required variable declared but never used")
            return (
                ObjectState.INPUT,
                f"Input variable used by {dependent_count} object(s)",
            )

        # OUTPUTS
        if self.type == ResourceType.OUTPUT:
            if dep_count == 0:
                return (
                    ObjectState.INCOMPLETE,
                    "Output declared but has no value source",
                )
            if dependent_count == 0:
                # Check if it references core infrastructure
                if self._references_core_infrastructure():
                    return (
                        ObjectState.OUTPUT_INTERFACE,
                        "Exports core infrastructure value (external interface)",
                    )
                return (ObjectState.ORPHANED, "Output computed but never consumed")
            return (
                ObjectState.OUTPUT_INTERFACE,
                f"Exports value used by {dependent_count} consumer(s)",
            )

        # LOCALS - Special handling for dependency chains
        if self.type == ResourceType.LOCAL:
            # Check if this local has any "real" consumers (not just other unused locals)
            has_real_consumers = self._has_real_consumers()

            if not has_real_consumers:
                if dep_count > 0:
                    return (
                        ObjectState.UNUSED,
                        f"Local value with {dep_count} deps but no real consumers",
                    )
                return (
                    ObjectState.UNUSED,
                    "Local value computed but never used in actual infrastructure",
                )

            # This local is actually used by real infrastructure
            if dep_count == 0:
                return (
                    ObjectState.ACTIVE,
                    f"Local value used by {dependent_count} infrastructure component(s)",
                )
            return (
                ObjectState.ACTIVE,
                f"Computed local using {dep_count} deps, used by {dependent_count} component(s)",
            )

        # MODULES
        if self.type == ResourceType.MODULE:
            # Modules are special - they create infrastructure even if outputs aren't used
            if dep_count == 0 and dependent_count == 0:
                return (
                    ObjectState.ISOLATED,
                    "Module not connected to any infrastructure",
                )

            if dep_count > 0 and dependent_count == 0:
                # Module creates infrastructure but outputs not used - this is normal!
                return (
                    ObjectState.ACTIVE,
                    f"Module provisions infrastructure using {dep_count} input(s)",
                )

            if dep_count == 0 and dependent_count > 0:
                return (
                    ObjectState.LEAF,
                    f"Module provides values to {dependent_count} consumer(s)",
                )

            # Module both receives inputs and provides outputs
            return (
                ObjectState.INTEGRATED,
                f"Module processes {dep_count} input(s) and provides to {dependent_count} consumer(s)",
            )

        # DATA SOURCES
        if self.type == ResourceType.DATA:
            if dependent_count == 0:
                return (ObjectState.UNUSED, "Data source queried but result never used")
            return (
                ObjectState.EXTERNAL_DATA,
                f"External data used by {dependent_count} object(s)",
            )

        # PROVIDERS
        if self.type == ResourceType.PROVIDER:
            # For providers, count only actual resources/data sources that use it
            if dependent_count == 0:
                return (
                    ObjectState.UNUSED,
                    "Provider configured but no resources use it",
                )

            # Filter to count only resources/data sources (not variables, outputs, etc.)
            resource_dependents = 0
            if self._all_objects_cache:
                for dep_name in self.dependency_info.dependent_objects:
                    if dep_name in self._all_objects_cache:
                        dep_obj = self._all_objects_cache[dep_name]
                        if dep_obj.type in [ResourceType.RESOURCE, ResourceType.DATA]:
                            resource_dependents += 1
            else:
                resource_dependents = dependent_count

            return (
                ObjectState.CONFIGURATION,
                f"Provider used by {resource_dependents} resource(s)",
            )

        # TERRAFORM BLOCKS
        if self.type == ResourceType.TERRAFORM:
            return (ObjectState.CONFIGURATION, "Terraform configuration block")

        # ==================== STRUCTURAL PATTERNS ====================

        # ISOLATED (no connections at all)
        if dep_count == 0 and dependent_count == 0:
            return (
                ObjectState.ISOLATED,
                "Not connected to any infrastructure components",
            )

        # LEAF (no deps, but used by others)
        if dep_count == 0 and dependent_count > 0:
            if self._is_external_facing():
                return (
                    ObjectState.LEAF,
                    f"External-facing resource used by {dependent_count} object(s)",
                )
            return (
                ObjectState.LEAF,
                f"Independent resource used by {dependent_count} object(s)",
            )

        # ORPHANED (has deps but nothing uses it) - ONLY for non-resource types
        if dep_count > 0 and dependent_count == 0:
            # For other non-resource types that truly create outputs
            return (
                ObjectState.UNUSED,
                f"Creates output from {dep_count} deps but result unused",
            )

        # HUB (highly connected center point)
        if dependent_count >= 10:
            return (ObjectState.HUB, f"Critical hub used by {dependent_count} objects")

        if dependent_count >= 5 and dep_count <= 3:
            return (
                ObjectState.HUB,
                f"Central resource distributing to {dependent_count} consumers",
            )

        # ==================== QUALITY WARNINGS ====================

        # UNDERUTILIZED (complex but barely used)
        if dep_count >= 5 and dependent_count == 1:
            return (
                ObjectState.UNDERUTILIZED,
                f"Complex resource ({dep_count} deps) used by only 1 object",
            )

        # COMPLEX (high complexity warning)
        if complexity >= 20:
            return (
                ObjectState.COMPLEX,
                f"High complexity (score: {complexity:.1f}) - consider refactoring",
            )

        if dep_count >= 10:
            return (
                ObjectState.COMPLEX,
                f"Very high dependency count ({dep_count}) - consider simplification",
            )

        # ==================== HEALTHY STATES ====================

        # HEALTHY (well-designed, follows best practices)
        if self._has_good_practices() and 2 <= dep_count <= 8 and dependent_count >= 2:
            return (
                ObjectState.HEALTHY,
                f"Well-designed: {dep_count} deps, {dependent_count} consumers, follows best practices",
            )

        # INTEGRATED (properly connected)
        if 2 <= dep_count <= 8 and dependent_count >= 2:
            return (
                ObjectState.INTEGRATED,
                f"Well-integrated: {dep_count} deps, {dependent_count} consumers",
            )

        if dep_count >= 1 and dependent_count >= 2:
            return (
                ObjectState.INTEGRATED,
                f"Integrated: {dep_count} deps, {dependent_count} consumers",
            )

        # ==================== DEFAULT: ACTIVE ====================

        # Active with reasonable connections
        if dep_count > 0 or dependent_count > 0:
            return (
                ObjectState.ACTIVE,
                f"Active: {dep_count} dependencies, {dependent_count} consumers",
            )

        # Fallback
        return (ObjectState.ACTIVE, "Active infrastructure component")

    def _is_in_unused_chain(self) -> bool:
        """Check if this object is part of an unused dependency chain."""
        if self.type not in [ResourceType.LOCAL, ResourceType.VARIABLE]:
            return False

        # If this object has no real consumers, check if it's part of a chain
        if not self._has_real_consumers():
            return True

        return False

    def _has_real_consumers(self) -> bool:
        """Check if this object has consumers that represent actual infrastructure."""
        if not self.dependency_info.dependent_objects:
            return False

        # Check if any dependent is a "real" infrastructure component
        real_consumer_types = [
            ResourceType.RESOURCE,
            ResourceType.MODULE,
            ResourceType.OUTPUT,
            ResourceType.DATA,
            ResourceType.PROVIDER,
        ]

        for dep_name in self.dependency_info.dependent_objects:
            if dep_name in self._all_objects_cache:
                dep_obj = self._all_objects_cache[dep_name]
                # If the dependent is a real infrastructure type, we're used
                if dep_obj.type in real_consumer_types:
                    return True
                # If the dependent is a local/variable, check if IT has real consumers
                if dep_obj.type in [ResourceType.LOCAL, ResourceType.VARIABLE]:
                    if dep_obj._has_real_consumers():
                        return True

        return False

    def _is_incomplete(self) -> bool:
        """Check if object has incomplete/invalid configuration."""

        if self.type == ResourceType.RESOURCE:
            # No attributes at all
            if not self.attributes:
                return True

            # Check common required fields by provider
            if self.resource_type:
                # AWS resources
                if self.resource_type.startswith("aws_"):
                    if "aws_instance" in self.resource_type:
                        return not (
                            "ami" in self.attributes
                            or "instance_type" in self.attributes
                        )
                    if "aws_s3_bucket" in self.resource_type:
                        # AWS bucket names are often generated, so this might be ok
                        return False
                    if "aws_security_group" in self.resource_type:
                        return (
                            "name" not in self.attributes
                            and "name_prefix" not in self.attributes
                        )

                # Azure resources
                if self.resource_type.startswith("azurerm_"):
                    if "azurerm_resource_group" in self.resource_type:
                        return (
                            "location" not in self.attributes
                            or "name" not in self.attributes
                        )

                # GCP resources
                if self.resource_type.startswith("google_"):
                    if "google_compute_instance" in self.resource_type:
                        return not (
                            "machine_type" in self.attributes
                            or "boot_disk" in self.attributes
                        )

        elif self.type == ResourceType.MODULE:
            # Module must have source
            return self.source is None or self.source == ""

        elif self.type == ResourceType.VARIABLE:
            # Required variables must have default or be explicitly nullable
            if not self.nullable and self.default_value is None:
                return True

        elif self.type == ResourceType.OUTPUT:
            # Output must have value
            return self.output_value is None and "value" not in self.attributes

        return False

    def _get_incompleteness_reason(self) -> str:
        """Get specific reason for incompleteness."""

        if self.type == ResourceType.RESOURCE:
            if not self.attributes:
                return "Resource has no configuration attributes"

            if self.resource_type:
                if "instance" in self.resource_type.lower():
                    return "Instance resource missing required configuration (ami, instance_type, etc.)"
                if "bucket" in self.resource_type.lower():
                    return "Bucket resource missing required configuration"
                if "security_group" in self.resource_type.lower():
                    return "Security group missing name configuration"
                if "resource_group" in self.resource_type.lower():
                    return "Resource group missing location or name"

                return f"Resource '{self.resource_type}' missing required configuration"

            return "Resource missing required configuration"

        elif self.type == ResourceType.MODULE:
            return "Module missing source attribute"

        elif self.type == ResourceType.VARIABLE:
            return "Required variable (nullable=false) missing default value"

        elif self.type == ResourceType.OUTPUT:
            return "Output missing value attribute"

        return "Missing required configuration"

    def _is_core_infrastructure(self) -> bool:
        """Check if this is core infrastructure resource."""
        if not self.resource_type:
            return False

        core_patterns = [
            "vpc",
            "vnet",
            "network",
            "subnet",
            "security_group",
            "firewall",
            "nsg",
            "route_table",
            "routing",
            "internet_gateway",
            "nat_gateway",
            "vpn_gateway",
            "load_balancer",
            "lb",
            "alb",
            "nlb",
            "database",
            "db",
            "rds",
            "sql",
            "cluster",
            "aks",
            "eks",
            "gke",
            "storage_account",
            "blob",
        ]

        resource_lower = self.resource_type.lower()
        return any(pattern in resource_lower for pattern in core_patterns)

    def _is_infrastructure_provisioning(self) -> bool:
        """
        Check if this object provisions real infrastructure.
        Resources and modules with dependencies are actively provisioning.
        """
        if self.type == ResourceType.RESOURCE:
            # Resources always provision infrastructure
            return True

        if self.type == ResourceType.MODULE:
            # Modules with source provision infrastructure
            return bool(self.source)

        return False

    def _is_external_facing(self) -> bool:
        """Check if this is an external-facing resource."""
        if not self.resource_type:
            return False

        external_patterns = [
            "load_balancer",
            "alb",
            "nlb",
            "lb",
            "api_gateway",
            "apigw",
            "cloudfront",
            "cdn",
            "waf",
            "firewall",
            "nat_gateway",
            "vpn",
            "direct_connect",
            "public_ip",
            "eip",
            "dns",
            "route53",
        ]

        resource_lower = self.resource_type.lower()
        return any(pattern in resource_lower for pattern in external_patterns)

    def _references_core_infrastructure(self) -> bool:
        """Check if output references core infrastructure."""
        if not self.dependency_info.all_dependencies:
            return False

        # Check if any dependency looks like core infrastructure
        for dep in self.dependency_info.all_dependencies:
            dep_lower = dep.lower()
            if any(
                pattern in dep_lower
                for pattern in ["vpc", "subnet", "network", "cluster", "database"]
            ):
                return True

        return False

    def _has_good_practices(self) -> bool:
        """Check if object follows Terraform best practices."""
        checks = []

        # Has meaningful description (10+ chars)
        has_description = bool(self.description and len(self.description.strip()) >= 10)
        checks.append(has_description)

        # Has tags (at least 2 for resources)
        if self.type == ResourceType.RESOURCE:
            has_tags = len(self.tags) >= 2
            checks.append(has_tags)

        # Consistent naming
        has_consistent_naming = self._has_consistent_naming()
        checks.append(has_consistent_naming)

        # At least 2 out of 3 checks should pass
        return sum(checks) >= 2

    def _has_consistent_naming(self) -> bool:
        """Check if naming follows consistent conventions."""
        name = self.name.lower()

        patterns = [
            r"^[a-z][a-z0-9_]*$",  # snake_case
            r"^[a-z][a-z0-9-]*$",  # kebab-case
            r"^[a-z][a-zA-Z0-9]*$",  # camelCase
        ]

        if any(re.match(pattern, name) for pattern in patterns):
            if not re.search(r"[_-]{2,}", name):
                if 2 <= len(name) <= 63:
                    return True

        return False

    @property
    def provider_prefix(self) -> Optional[str]:
        """Extract provider prefix from resource type."""
        if self.resource_type:
            parts = self.resource_type.split("_", 1)
            if parts:
                return parts[0]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
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
                "circular": self.dependency_info.circular_dependencies,
                "missing": self.dependency_info.missing_dependencies,
                "counts": {
                    "dependencies": self.dependency_info.dependency_count,
                    "dependents": self.dependency_info.dependent_count,
                },
            },
            "metrics": {
                "complexity_score": self.dependency_info.complexity_score,
                "has_circular_deps": self.dependency_info.has_circular_deps,
                "has_missing_deps": self.dependency_info.has_missing_deps,
                "fan_in": self.dependency_info.fan_in,
                "fan_out": self.dependency_info.fan_out,
            },
            "attributes": self.attributes,
        }
