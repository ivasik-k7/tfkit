from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import ObjectState, ResourceType, TerraformObject


@dataclass
class ProjectMetadata:
    """Metadata about the Terraform project."""

    project_path: str
    total_files: int = 0
    analysis_timestamp: Optional[str] = None
    terraform_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_path": self.project_path,
            "total_files": self.total_files,
            "analysis_timestamp": self.analysis_timestamp,
            "terraform_version": self.terraform_version,
        }


@dataclass
class ProjectStatistics:
    """Computed statistics about the project."""

    # Object counts by type
    resource_count: int = 0
    data_source_count: int = 0
    module_count: int = 0
    variable_count: int = 0
    output_count: int = 0
    provider_count: int = 0
    local_count: int = 0

    # State distribution
    state_distribution: Dict[str, int] = field(default_factory=dict)

    # Provider usage
    providers_used: List[str] = field(default_factory=list)
    resource_counts_by_type: Dict[str, int] = field(default_factory=dict)

    # Health metrics
    unused_objects: List[str] = field(default_factory=list)
    orphaned_objects: List[str] = field(default_factory=list)
    isolated_objects: List[str] = field(default_factory=list)
    incomplete_objects: List[str] = field(default_factory=list)

    @property
    def total_objects(self) -> int:
        """Total number of objects in the project."""
        return (
            self.resource_count
            + self.data_source_count
            + self.module_count
            + self.variable_count
            + self.output_count
            + self.provider_count
            + self.local_count
        )

    @property
    def health_score(self) -> float:
        """
        Calculate overall project health score (0-100).

        Based on ratio of active objects vs problematic ones.
        """
        if self.total_objects == 0:
            return 100.0

        active = self.state_distribution.get(ObjectState.ACTIVE.value, 0)
        input_output = self.state_distribution.get(
            ObjectState.INPUT.value, 0
        ) + self.state_distribution.get(ObjectState.OUTPUT_INTERFACE.value, 0)
        config = self.state_distribution.get(ObjectState.CONFIGURATION.value, 0)

        healthy = active + input_output + config

        unused = len(self.unused_objects)
        orphaned = len(self.orphaned_objects)
        incomplete = len(self.incomplete_objects)

        # Base score from healthy ratio
        score = (healthy / self.total_objects) * 100

        # Penalties
        score -= (unused / self.total_objects) * 15  # -15% per unused
        score -= (orphaned / self.total_objects) * 10  # -10% per orphaned
        score -= (incomplete / self.total_objects) * 20  # -20% per incomplete

        return max(0.0, min(100.0, score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "counts": {
                "resources": self.resource_count,
                "data_sources": self.data_source_count,
                "modules": self.module_count,
                "variables": self.variable_count,
                "outputs": self.output_count,
                "providers": self.provider_count,
                "locals": self.local_count,
                "total": self.total_objects,
            },
            "state_distribution": self.state_distribution,
            "providers": {
                "used": self.providers_used,
                "count": len(self.providers_used),
            },
            "resource_types": self.resource_counts_by_type,
            "health": {
                "score": round(self.health_score, 2),
                "unused_count": len(self.unused_objects),
                "orphaned_count": len(self.orphaned_objects),
                "isolated_count": len(self.isolated_objects),
                "incomplete_count": len(self.incomplete_objects),
            },
            "issues": {
                "unused": self.unused_objects,
                "orphaned": self.orphaned_objects,
                "isolated": self.isolated_objects,
                "incomplete": self.incomplete_objects,
            },
        }


class TerraformProject:
    """
    Enhanced Terraform project container with comprehensive object management.

    This class maintains all Terraform objects and provides high-level
    operations for querying, analyzing, and managing the project structure.
    """

    def __init__(self, project_path: Optional[str] = None):
        """Initialize an empty project."""
        self._objects: Dict[str, TerraformObject] = {}

        # Type-specific indexes for fast access
        self._resources: Dict[str, TerraformObject] = {}
        self._data_sources: Dict[str, TerraformObject] = {}
        self._modules: Dict[str, TerraformObject] = {}
        self._variables: Dict[str, TerraformObject] = {}
        self._outputs: Dict[str, TerraformObject] = {}
        self._providers: Dict[str, TerraformObject] = {}
        self._locals: Dict[str, TerraformObject] = {}
        self._terraform_blocks: Dict[str, TerraformObject] = {}

        # Additional data
        self.tfvars_files: Dict[str, Dict[str, Any]] = {}
        self.backend_config: Optional[Dict[str, Any]] = None

        # Metadata
        self.metadata = ProjectMetadata(project_path=project_path or str(Path.cwd()))

        # Cached statistics
        self._statistics: Optional[ProjectStatistics] = None

    # ============ Object Management ============

    def add_object(self, obj: TerraformObject) -> None:
        """
        Add a Terraform object to the project.

        Automatically indexes by type and invalidates statistics cache.
        """
        self._objects[obj.full_name] = obj

        # Index by type
        type_map = {
            ResourceType.RESOURCE: self._resources,
            ResourceType.DATA: self._data_sources,
            ResourceType.MODULE: self._modules,
            ResourceType.VARIABLE: self._variables,
            ResourceType.OUTPUT: self._outputs,
            ResourceType.PROVIDER: self._providers,
            ResourceType.LOCAL: self._locals,
            ResourceType.TERRAFORM: self._terraform_blocks,
        }

        if obj.type in type_map:
            type_map[obj.type][obj.full_name] = obj

        # Invalidate cache
        self._statistics = None

    def get_object(self, full_name: str) -> Optional[TerraformObject]:
        """Get an object by its full name."""
        return self._objects.get(full_name)

    def remove_object(self, full_name: str) -> bool:
        """
        Remove an object from the project.

        Returns True if object was removed, False if not found.
        """
        obj = self._objects.get(full_name)
        if not obj:
            return False

        # Remove from main dict
        del self._objects[full_name]

        # Remove from type index
        type_map = {
            ResourceType.RESOURCE: self._resources,
            ResourceType.DATA: self._data_sources,
            ResourceType.MODULE: self._modules,
            ResourceType.VARIABLE: self._variables,
            ResourceType.OUTPUT: self._outputs,
            ResourceType.PROVIDER: self._providers,
            ResourceType.LOCAL: self._locals,
            ResourceType.TERRAFORM: self._terraform_blocks,
        }

        if obj.type in type_map and full_name in type_map[obj.type]:
            del type_map[obj.type][full_name]

        # Invalidate cache
        self._statistics = None

        return True

    # ============ Querying ============

    @property
    def all_objects(self) -> Dict[str, TerraformObject]:
        """Get all objects."""
        return self._objects.copy()

    @property
    def resources(self) -> Dict[str, TerraformObject]:
        """Get all resources."""
        return self._resources.copy()

    @property
    def data_sources(self) -> Dict[str, TerraformObject]:
        """Get all data sources."""
        return self._data_sources.copy()

    @property
    def modules(self) -> Dict[str, TerraformObject]:
        """Get all modules."""
        return self._modules.copy()

    @property
    def variables(self) -> Dict[str, TerraformObject]:
        """Get all variables."""
        return self._variables.copy()

    @property
    def outputs(self) -> Dict[str, TerraformObject]:
        """Get all outputs."""
        return self._outputs.copy()

    @property
    def providers(self) -> Dict[str, TerraformObject]:
        """Get all providers."""
        return self._providers.copy()

    @property
    def locals(self) -> Dict[str, TerraformObject]:
        """Get all locals."""
        return self._locals.copy()

    @property
    def terraform_blocks(self) -> Dict[str, TerraformObject]:
        """Get all terraform blocks."""
        return self._terraform_blocks.copy()

    def get_objects_by_type(
        self, resource_type: ResourceType
    ) -> Dict[str, TerraformObject]:
        """Get all objects of a specific type."""
        type_map = {
            ResourceType.RESOURCE: self._resources,
            ResourceType.DATA: self._data_sources,
            ResourceType.MODULE: self._modules,
            ResourceType.VARIABLE: self._variables,
            ResourceType.OUTPUT: self._outputs,
            ResourceType.PROVIDER: self._providers,
            ResourceType.LOCAL: self._locals,
            ResourceType.TERRAFORM: self._terraform_blocks,
        }
        return type_map.get(resource_type, {}).copy()

    def get_objects_by_state(self, state: ObjectState) -> List[TerraformObject]:
        """Get all objects in a specific state."""
        return [obj for obj in self._objects.values() if obj.state == state]

    def get_objects_by_file(self, file_path: str) -> List[TerraformObject]:
        """Get all objects defined in a specific file."""
        return [
            obj for obj in self._objects.values() if obj.location.file_path == file_path
        ]

    def get_objects_by_provider(self, provider: str) -> List[TerraformObject]:
        """Get all objects using a specific provider."""
        return [
            obj
            for obj in self._objects.values()
            if obj.provider_info and obj.provider_info.provider_name == provider
        ]

    # ============ Dependency Analysis ============

    def build_dependency_graph(self) -> None:
        """
        Build the complete dependency graph.

        This populates the dependent_objects list for each object based on
        the dependencies of all other objects.
        """
        # Clear all dependent lists
        for obj in self._objects.values():
            obj.dependency_info.dependent_objects.clear()
            obj.invalidate_state()

        # Build reverse dependencies
        for obj in self._objects.values():
            for dep_name in obj.dependency_info.all_dependencies:
                dep_obj = self._objects.get(dep_name)
                if dep_obj:
                    if obj.full_name not in dep_obj.dependency_info.dependent_objects:
                        dep_obj.dependency_info.dependent_objects.append(obj.full_name)
                        dep_obj.invalidate_state()

        # Invalidate statistics cache
        self._statistics = None

    def get_dependency_chain(
        self, object_name: str, max_depth: int = 10
    ) -> List[List[str]]:
        """
        Get all dependency chains starting from an object.

        Args:
            object_name: Starting object name
            max_depth: Maximum chain depth to prevent infinite recursion

        Returns:
            List of dependency chains (each chain is a list of object names)
        """
        obj = self.get_object(object_name)
        if not obj:
            return []

        chains = []
        visited = set()

        def _build_chain(current_name: str, chain: List[str], depth: int) -> None:
            if depth > max_depth or current_name in visited:
                return

            visited.add(current_name)
            chain.append(current_name)

            current_obj = self.get_object(current_name)
            if not current_obj:
                chains.append(chain.copy())
                chain.pop()
                visited.remove(current_name)
                return

            deps = current_obj.dependency_info.all_dependencies
            if not deps:
                chains.append(chain.copy())
            else:
                for dep in deps:
                    _build_chain(dep, chain.copy(), depth + 1)

            chain.pop() if chain else None
            visited.remove(current_name)

        _build_chain(object_name, [], 0)
        return chains

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependency chains in the project."""
        cycles = []
        visited = set()
        rec_stack = []

        def _visit(node_name: str) -> None:
            if node_name in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(node_name)
                cycle = rec_stack[cycle_start:] + [node_name]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if node_name in visited:
                return

            visited.add(node_name)
            rec_stack.append(node_name)

            obj = self.get_object(node_name)
            if obj:
                for dep in obj.dependency_info.all_dependencies:
                    _visit(dep)

            rec_stack.pop()

        for obj_name in self._objects:
            if obj_name not in visited:
                _visit(obj_name)

        return cycles

    # ============ Statistics & Analysis ============

    def compute_statistics(self) -> ProjectStatistics:
        """
        Compute comprehensive project statistics.

        This is cached and only recomputed when the project changes.
        """
        if self._statistics is not None:
            return self._statistics

        stats = ProjectStatistics()

        # Count by type
        stats.resource_count = len(self._resources)
        stats.data_source_count = len(self._data_sources)
        stats.module_count = len(self._modules)
        stats.variable_count = len(self._variables)
        stats.output_count = len(self._outputs)
        stats.provider_count = len(self._providers)
        stats.local_count = len(self._locals)

        # State distribution
        state_dist = {}
        for obj in self._objects.values():
            state = obj.state.value
            state_dist[state] = state_dist.get(state, 0) + 1

            # Collect problematic objects
            if obj.state == ObjectState.UNUSED:
                stats.unused_objects.append(obj.full_name)
            elif obj.state == ObjectState.ORPHANED:
                stats.orphaned_objects.append(obj.full_name)
            elif obj.state == ObjectState.ISOLATED:
                stats.isolated_objects.append(obj.full_name)
            elif obj.state == ObjectState.INCOMPLETE:
                stats.incomplete_objects.append(obj.full_name)

        stats.state_distribution = state_dist

        # Providers
        providers = set()
        for obj in self._resources.values():
            if obj.provider_info:
                providers.add(obj.provider_info.provider_name)
        for obj in self._data_sources.values():
            if obj.provider_info:
                providers.add(obj.provider_info.provider_name)

        stats.providers_used = sorted(providers)

        # Resource types
        resource_types = {}
        for obj in self._resources.values():
            if obj.resource_type:
                resource_types[obj.resource_type] = (
                    resource_types.get(obj.resource_type, 0) + 1
                )

        stats.resource_counts_by_type = resource_types

        self._statistics = stats
        return stats

    def validate(self) -> List[str]:
        """
        Perform validation and return list of issues.

        Returns:
            List of validation error/warning messages
        """
        issues = []

        # Check for circular dependencies
        cycles = self.find_circular_dependencies()
        for cycle in cycles:
            issues.append(f"Circular dependency detected: {' -> '.join(cycle)}")

        # Check for undefined references
        all_names = set(self._objects.keys())
        for obj in self._objects.values():
            for dep in obj.dependency_info.all_dependencies:
                # Skip known external references
                if dep.startswith(("var.", "local.", "data.", "module.")):
                    continue
                if dep not in all_names:
                    issues.append(
                        f"Undefined reference: {dep} (used by {obj.full_name})"
                    )

        # Check for incomplete outputs
        for obj in self._outputs.values():
            if obj.state == ObjectState.INCOMPLETE:
                issues.append(f"Output has no value source: {obj.full_name}")

        return issues

    # ============ Serialization ============

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire project to dictionary."""
        stats = self.compute_statistics()

        return {
            "metadata": self.metadata.to_dict(),
            "objects": {
                "resources": {k: v.to_dict() for k, v in self._resources.items()},
                "data_sources": {k: v.to_dict() for k, v in self._data_sources.items()},
                "modules": {k: v.to_dict() for k, v in self._modules.items()},
                "variables": {k: v.to_dict() for k, v in self._variables.items()},
                "outputs": {k: v.to_dict() for k, v in self._outputs.items()},
                "providers": {k: v.to_dict() for k, v in self._providers.items()},
                "locals": {k: v.to_dict() for k, v in self._locals.items()},
                "terraform_blocks": {
                    k: v.to_dict() for k, v in self._terraform_blocks.items()
                },
            },
            "tfvars_files": self.tfvars_files,
            "backend_config": self.backend_config,
            "statistics": stats.to_dict(),
            "validation": self.validate(),
        }
