"""Data models for Terraform analysis."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ResourceType(Enum):
    RESOURCE = "resource"
    DATA = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    TERRAFORM = "terraform"
    LOCAL = "local"


@dataclass
class TerraformObject:
    type: ResourceType
    name: str
    full_name: str
    attributes: Dict[str, Any]
    dependencies: List[str]
    file_path: str
    line_number: int

    resource_type: Optional[str] = None
    provider: Optional[str] = None
    source: Optional[str] = None
    variable_type: Optional[str] = None
    default_value: Optional[Any] = None
    description: Optional[str] = None
    sensitive: bool = False
    alias: Optional[str] = None


@dataclass
class TerraformProject:
    resources: Dict[str, TerraformObject] = field(default_factory=dict)
    data_sources: Dict[str, TerraformObject] = field(default_factory=dict)
    modules: Dict[str, TerraformObject] = field(default_factory=dict)
    variables: Dict[str, TerraformObject] = field(default_factory=dict)
    outputs: Dict[str, TerraformObject] = field(default_factory=dict)
    providers: Dict[str, TerraformObject] = field(default_factory=dict)
    terraform_blocks: Dict[str, TerraformObject] = field(default_factory=dict)
    locals: Dict[str, TerraformObject] = field(default_factory=dict)

    tfvars_files: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    backend_config: Optional[Dict[str, Any]] = None
    dependency_graph: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary with all enhanced fields."""
        return {
            "resources": {k: asdict(v) for k, v in self.resources.items()},
            "data_sources": {k: asdict(v) for k, v in self.data_sources.items()},
            "modules": {k: asdict(v) for k, v in self.modules.items()},
            "variables": {k: asdict(v) for k, v in self.variables.items()},
            "outputs": {k: asdict(v) for k, v in self.outputs.items()},
            "providers": {k: asdict(v) for k, v in self.providers.items()},
            "terraform_blocks": {
                k: asdict(v) for k, v in self.terraform_blocks.items()
            },
            "locals": {k: asdict(v) for k, v in self.locals.items()},
            "tfvars_files": self.tfvars_files,
            "backend_config": self.backend_config,
            "metadata": self.metadata,
            "dependency_graph": self.dependency_graph,
        }

    @property
    def total_resources(self) -> int:
        """Total number of resources in the project."""
        return len(self.resources)

    @property
    def total_data_sources(self) -> int:
        """Total number of data sources in the project."""
        return len(self.data_sources)

    @property
    def total_modules(self) -> int:
        """Total number of modules in the project."""
        return len(self.modules)

    @property
    def total_variables(self) -> int:
        """Total number of variables in the project."""
        return len(self.variables)

    @property
    def total_outputs(self) -> int:
        """Total number of outputs in the project."""
        return len(self.outputs)

    @property
    def total_providers(self) -> int:
        """Total number of provider configurations in the project."""
        return len(self.providers)

    @property
    def total_locals(self) -> int:
        """Total number of local values in the project."""
        return len(self.locals)

    @property
    def all_objects(self) -> Dict[str, TerraformObject]:
        """Get all Terraform objects in a single dictionary."""
        all_objs = {}
        all_objs.update(self.resources)
        all_objs.update(self.data_sources)
        all_objs.update(self.modules)
        all_objs.update(self.variables)
        all_objs.update(self.outputs)
        all_objs.update(self.providers)
        all_objs.update(self.terraform_blocks)
        all_objs.update(self.locals)
        return all_objs

    def get_objects_by_type(
        self, resource_type: ResourceType
    ) -> Dict[str, TerraformObject]:
        """Get all objects of a specific type."""
        type_map = {
            ResourceType.RESOURCE: self.resources,
            ResourceType.DATA: self.data_sources,
            ResourceType.MODULE: self.modules,
            ResourceType.VARIABLE: self.variables,
            ResourceType.OUTPUT: self.outputs,
            ResourceType.PROVIDER: self.providers,
            ResourceType.TERRAFORM: self.terraform_blocks,
            ResourceType.LOCAL: self.locals,
        }
        return type_map.get(resource_type, {})

    def get_objects_by_file(self, file_path: str) -> Dict[str, TerraformObject]:
        """Get all objects defined in a specific file."""
        return {
            name: obj
            for name, obj in self.all_objects.items()
            if obj.file_path == file_path
        }

    def find_object(self, full_name: str) -> Optional[TerraformObject]:
        """Find an object by its full name."""
        return self.all_objects.get(full_name)

    def get_providers_used(self) -> List[str]:
        """Get list of all providers used in the project."""
        providers = set()

        for resource in self.resources.values():
            if resource.provider:
                providers.add(resource.provider)

        for data_source in self.data_sources.values():
            if data_source.provider:
                providers.add(data_source.provider)

        for provider in self.providers.values():
            providers.add(provider.name)

        return sorted(providers)

    def get_resource_counts_by_type(self) -> Dict[str, int]:
        """Get counts of resources by type."""
        counts = {}
        for resource in self.resources.values():
            if resource.resource_type:
                counts[resource.resource_type] = (
                    counts.get(resource.resource_type, 0) + 1
                )
        return counts

    def get_circular_dependencies(self) -> List[List[str]]:
        """Get circular dependencies from the dependency graph."""
        if not self.dependency_graph:
            return []

        circular = []
        visited = set()
        path = set()

        def _visit(node: str):
            if node in path:
                cycle_start = list(path).index(node)
                cycle = list(path)[cycle_start:]
                if cycle not in circular:
                    circular.append(cycle)
                return
            if node in visited:
                return

            visited.add(node)
            path.add(node)

            if node in self.dependency_graph:
                for dep in self.dependency_graph[node].get("dependencies", []):
                    if dep in self.dependency_graph:
                        _visit(dep)

            path.remove(node)

        for node in self.dependency_graph:
            if node not in visited:
                _visit(node)

        return circular

    def get_dependents(self, object_name: str) -> List[str]:
        """Get all objects that depend on the specified object."""
        if not self.dependency_graph or object_name not in self.dependency_graph:
            return []
        return self.dependency_graph[object_name].get("dependents", [])

    def validate(self) -> List[str]:
        """Perform basic validation on the project structure."""
        issues = []

        # Check for undefined references in dependencies
        all_object_names = set(self.all_objects.keys())

        for obj_name, obj in self.all_objects.items():
            for dep in obj.dependencies:
                if dep not in all_object_names and not dep.startswith(
                    ("var.", "local.")
                ):
                    # This might be a cross-module reference or external dependency
                    # We'll just warn about potentially undefined references
                    if not any(
                        dep.startswith(prefix) for prefix in ["data.", "module."]
                    ):
                        issues.append(
                            f"Potential undefined reference: {dep} in {obj_name}"
                        )

        return issues
