import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from tfkit.parser.models import TerraformCatalog


class DependencyType(Enum):
    """Types of dependencies between Terraform objects"""

    DIRECT = "direct"  # Direct reference in attributes
    IMPLICIT = "implicit"  # Implicit dependency (e.g., provider)
    MODULE = "module"  # Module relationship
    PROVIDER = "provider"  # Provider configuration
    MOVED = "moved"  # Moved block reference


@dataclass
class TerraformDependency:
    """Represents a dependency between Terraform objects"""

    source_address: str
    target_address: str
    dependency_type: DependencyType
    attribute_path: Optional[str] = None  # Where the reference was found

    def __hash__(self):
        return hash((self.source_address, self.target_address, self.dependency_type))

    def __eq__(self, other):
        if not isinstance(other, TerraformDependency):
            return False
        return (
            self.source_address == other.source_address
            and self.target_address == other.target_address
            and self.dependency_type == other.dependency_type
        )


@dataclass
class ObjectDependencies:
    address: str
    depends_on: Set[TerraformDependency] = field(default_factory=set)
    referenced_by: Set[TerraformDependency] = field(default_factory=set)

    def add_dependency(self, dependency: TerraformDependency):
        self.depends_on.add(dependency)

    def add_reference(self, dependency: TerraformDependency):
        self.referenced_by.add(dependency)

    def get_all_dependencies(self) -> Set[str]:
        return {dep.target_address for dep in self.depends_on}

    def get_all_references(self) -> Set[str]:
        return {dep.source_address for dep in self.referenced_by}

    def get_dependencies_by_type(self, dep_type: DependencyType) -> Set[str]:
        return {
            dep.target_address
            for dep in self.depends_on
            if dep.dependency_type == dep_type
        }

    def get_references_by_type(self, dep_type: DependencyType) -> Set[str]:
        return {
            dep.source_address
            for dep in self.referenced_by
            if dep.dependency_type == dep_type
        }


class TerraformDependencyBuilder:
    """
    Service to build dependency relationships between Terraform objects.
    Analyzes attributes, raw_code, and other fields to find references.
    Handles implicit provider relationships based on resource types.
    Automatically detects provider prefixes from resources.
    """

    # Terraform interpolation patterns
    INTERPOLATION_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, catalog: "TerraformCatalog"):
        """
        Initialize the dependency builder with a catalog.

        Args:
            catalog: TerraformCatalog instance containing all objects
        """
        self.catalog = catalog
        self.dependencies: Dict[str, ObjectDependencies] = {}

        # Provider maps
        self._provider_map: Dict[str, str] = {}  # {provider_type: default_address}
        self._aliased_providers: Dict[str, List[str]] = defaultdict(
            list
        )  # {provider_type: [aliased_addresses]}

        # Auto-detected provider prefixes from resources
        self._provider_prefixes: Dict[str, List[str]] = defaultdict(
            list
        )  # {provider_type: [prefixes]}

    def build_dependencies(self) -> Dict[str, ObjectDependencies]:
        """
        Build complete dependency graph for all objects in the catalog.

        Returns:
            Dictionary mapping addresses to ObjectDependencies
        """
        self.dependencies = {}

        # Initialize dependencies for all objects
        for address in self.catalog.get_all_addresses():
            self.dependencies[address] = ObjectDependencies(address=address)

        # Build provider maps and auto-detect prefixes
        self._build_provider_maps()
        self._detect_provider_prefixes()

        # Build dependencies for each object
        all_objects = self.catalog.get_all_objects()

        for obj in all_objects:
            source_address = self.catalog._build_address(obj)
            if not source_address:
                continue

            # Extract explicit dependencies
            found_deps = self._extract_dependencies(obj, source_address)

            # Add provider dependencies (explicit and implicit)
            provider_deps = self._extract_provider_dependencies(obj, source_address)
            found_deps.extend(provider_deps)

            # Add to dependency graph
            for dep in found_deps:
                if dep.source_address in self.dependencies:
                    self.dependencies[dep.source_address].add_dependency(dep)

                if dep.target_address in self.dependencies:
                    self.dependencies[dep.target_address].add_reference(dep)

        return self.dependencies

    def _build_provider_maps(self):
        """Build internal maps of providers for quick lookup"""
        self._provider_map.clear()
        self._aliased_providers.clear()

        for provider in self.catalog.providers:
            provider_name = getattr(provider, "name", None)
            alias = getattr(provider, "alias", None)

            if not provider_name:
                continue

            # Build the address based on catalog's addressing scheme
            if alias:
                # Aliased provider: provider_name.alias
                address = f"{provider_name}.{alias}"
                self._aliased_providers[provider_name].append(address)
            else:
                # Default provider (no alias): just provider_name
                address = provider_name
                self._provider_map[provider_name] = address

    def _detect_provider_prefixes(self):
        """
        Auto-detect provider prefixes from existing resources and data sources.
        This builds a mapping of provider types to their resource prefixes.
        """
        self._provider_prefixes.clear()

        # Collect all resource and data source types
        resource_types = set()

        for resource in self.catalog.resources:
            resource_type = getattr(resource, "resource_type", None)
            if resource_type:
                resource_types.add(resource_type)

        for data_source in self.catalog.data_sources:
            data_type = getattr(data_source, "data_type", None)
            if data_type:
                resource_types.add(data_type)

        # Extract prefixes (everything before first underscore)
        prefix_counts = defaultdict(int)
        for resource_type in resource_types:
            parts = resource_type.split("_", 1)
            if len(parts) > 1:
                prefix = parts[0]
                prefix_counts[prefix] += 1

        # Map prefixes to known providers
        for prefix, _ in prefix_counts.items():
            # Check if this prefix matches a known provider
            if prefix in self._provider_map or prefix in self._aliased_providers:
                self._provider_prefixes[prefix].append(f"{prefix}_")

    def _get_provider_type_from_resource(self, resource_type: str) -> Optional[str]:
        """
        Determine provider type from resource type name.

        Args:
            resource_type: Resource type (e.g., 'aws_s3_bucket', 'google_compute_instance')

        Returns:
            Provider type or None
        """
        # Check auto-detected provider prefixes first
        for provider_type, prefixes in self._provider_prefixes.items():
            for prefix in prefixes:
                if resource_type.startswith(prefix):
                    return provider_type

        # Fallback: extract prefix before first underscore
        parts = resource_type.split("_", 1)
        if len(parts) > 1:
            potential_provider = parts[0]
            # Check if this provider exists in catalog
            if (
                potential_provider in self._provider_map
                or potential_provider in self._aliased_providers
            ):
                return potential_provider

        return None

    def _resolve_provider_reference(self, provider_ref: str) -> Optional[str]:
        """
        Resolve a provider reference to its catalog address.

        Handles various formats:
        - "aws" -> "aws" (default provider)
        - "aws.secondary" -> "aws.secondary" (aliased provider)

        Args:
            provider_ref: Provider reference string

        Returns:
            Resolved provider address or None
        """
        if not provider_ref:
            return None

        # Remove any interpolation syntax
        provider_ref = provider_ref.strip()
        provider_ref = re.sub(r"^\$\{|}$", "", provider_ref)

        # Check if it exists in catalog directly
        if self.catalog.has_address(provider_ref):
            return provider_ref

        # Parse provider.alias format
        parts = provider_ref.split(".")
        if len(parts) == 2:
            provider_type, alias = parts
            # Check if this aliased provider exists
            aliased_address = f"{provider_type}.{alias}"
            if self.catalog.has_address(aliased_address):
                return aliased_address
        elif len(parts) == 1:
            # Just provider type, no alias
            if provider_ref in self._provider_map:
                return self._provider_map[provider_ref]

        return None

    def _extract_provider_dependencies(
        self, obj: Any, source_address: str
    ) -> List[TerraformDependency]:
        """
        Extract implicit and explicit provider dependencies.

        Args:
            obj: The Terraform object
            source_address: Address of the source object

        Returns:
            List of provider dependencies
        """
        dependencies = []

        # Only resources and data sources have provider dependencies
        obj_type = getattr(obj, "object_type", None)
        if not obj_type or obj_type.value not in ("resource", "data"):
            return dependencies

        # Get resource/data type
        resource_type = getattr(obj, "resource_type", None) or getattr(
            obj, "data_type", None
        )

        if not resource_type:
            return dependencies

        # Check for explicit provider attribute
        explicit_provider = getattr(obj, "provider", None)

        if explicit_provider:
            # Explicit provider reference (e.g., "aws.secondary" or just "aws")
            provider_address = self._resolve_provider_reference(explicit_provider)

            if provider_address:
                dependencies.append(
                    TerraformDependency(
                        source_address=source_address,
                        target_address=provider_address,
                        dependency_type=DependencyType.PROVIDER,
                        attribute_path="provider",
                    )
                )
            else:
                # Log warning - provider reference not found
                error_msg = f"Provider reference '{explicit_provider}' not found in catalog for {source_address}"
                if error_msg not in self.catalog.errors:
                    self.catalog.errors.append(error_msg)
        else:
            # Implicit provider based on resource/data type
            provider_type = self._get_provider_type_from_resource(resource_type)

            if provider_type and provider_type in self._provider_map:
                # Use default provider
                provider_address = self._provider_map[provider_type]

                dependencies.append(
                    TerraformDependency(
                        source_address=source_address,
                        target_address=provider_address,
                        dependency_type=DependencyType.IMPLICIT,
                        attribute_path="provider (implicit)",
                    )
                )

        return dependencies

    def _extract_dependencies(
        self, obj: Any, source_address: str
    ) -> List[TerraformDependency]:
        """
        Extract all explicit dependencies from a Terraform object.

        Args:
            obj: The Terraform object to analyze
            source_address: The address of the source object

        Returns:
            List of TerraformDependency objects
        """
        dependencies = []

        # Extract from attributes (skip 'provider' attribute as it's handled separately)
        if hasattr(obj, "attributes") and obj.attributes:
            # Filter out provider attribute to avoid double-processing
            filtered_attrs = {
                k: v for k, v in obj.attributes.items() if k != "provider"
            }
            if filtered_attrs:
                deps = self._extract_from_dict(
                    filtered_attrs, source_address, "attributes"
                )
                dependencies.extend(deps)

        # Extract from raw_code
        if hasattr(obj, "raw_code") and obj.raw_code:
            deps = self._extract_from_string(obj.raw_code, source_address, "raw_code")
            dependencies.extend(deps)

        # Extract from moved blocks (from/to addresses)
        if hasattr(obj, "from_address") and obj.from_address:
            refs = self._parse_references_from_string(obj.from_address)
            for ref in refs:
                if self.catalog.has_address(ref):
                    dependencies.append(
                        TerraformDependency(
                            source_address=source_address,
                            target_address=ref,
                            dependency_type=DependencyType.MOVED,
                            attribute_path="from_address",
                        )
                    )

        if hasattr(obj, "to_address") and obj.to_address:
            refs = self._parse_references_from_string(obj.to_address)
            for ref in refs:
                if self.catalog.has_address(ref):
                    dependencies.append(
                        TerraformDependency(
                            source_address=source_address,
                            target_address=ref,
                            dependency_type=DependencyType.MOVED,
                            attribute_path="to_address",
                        )
                    )

        # Extract from depends_on (explicit dependencies)
        if hasattr(obj, "depends_on") and obj.depends_on:
            depends_list = (
                obj.depends_on if isinstance(obj.depends_on, list) else [obj.depends_on]
            )
            for dep_ref in depends_list:
                if isinstance(dep_ref, str):
                    refs = self._parse_references_from_string(dep_ref)
                    for ref in refs:
                        if self.catalog.has_address(ref):
                            dependencies.append(
                                TerraformDependency(
                                    source_address=source_address,
                                    target_address=ref,
                                    dependency_type=DependencyType.DIRECT,
                                    attribute_path="depends_on",
                                )
                            )

        # Extract from for_each and count expressions
        for attr_name in ["for_each", "count"]:
            if hasattr(obj, attr_name):
                attr_value = getattr(obj, attr_name)
                if attr_value:
                    if isinstance(attr_value, str):
                        deps = self._extract_from_string(
                            attr_value, source_address, attr_name
                        )
                        dependencies.extend(deps)
                    elif isinstance(attr_value, dict):
                        deps = self._extract_from_dict(
                            attr_value, source_address, attr_name
                        )
                        dependencies.extend(deps)

        # Extract from module source (for module blocks)
        if hasattr(obj, "source") and obj.source:
            source_value = getattr(obj, "source")  # noqa: B009
            if isinstance(source_value, str):
                # Module sources can reference local paths or registries
                # Only extract if it contains references
                deps = self._extract_from_string(source_value, source_address, "source")
                dependencies.extend(deps)

        # Extract from lifecycle blocks
        if hasattr(obj, "lifecycle") and obj.lifecycle:
            lifecycle = getattr(obj, "lifecycle")  # noqa: B009
            if isinstance(lifecycle, dict):
                # Check for replace_triggered_by, ignore_changes, etc.
                deps = self._extract_from_dict(lifecycle, source_address, "lifecycle")
                dependencies.extend(deps)

        # Extract from provisioner blocks (if present in attributes)
        if hasattr(obj, "provisioners") and obj.provisioners:
            provisioners = getattr(obj, "provisioners")  # noqa: B009
            if isinstance(provisioners, list):
                for idx, provisioner in enumerate(provisioners):
                    if isinstance(provisioner, dict):
                        deps = self._extract_from_dict(
                            provisioner, source_address, f"provisioner[{idx}]"
                        )
                        dependencies.extend(deps)

        # Remove duplicates
        return list(set(dependencies))

    def _extract_from_dict(
        self, data: Dict[str, Any], source_address: str, base_path: str = ""
    ) -> List[TerraformDependency]:
        """
        Recursively extract dependencies from a dictionary.

        Args:
            data: Dictionary to analyze
            source_address: Address of the source object
            base_path: Current path in the attribute tree

        Returns:
            List of found dependencies
        """
        dependencies = []

        for key, value in data.items():
            current_path = f"{base_path}.{key}" if base_path else key

            if isinstance(value, str):
                deps = self._extract_from_string(value, source_address, current_path)
                dependencies.extend(deps)

            elif isinstance(value, dict):
                deps = self._extract_from_dict(value, source_address, current_path)
                dependencies.extend(deps)

            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    item_path = f"{current_path}[{idx}]"
                    if isinstance(item, str):
                        deps = self._extract_from_string(
                            item, source_address, item_path
                        )
                        dependencies.extend(deps)
                    elif isinstance(item, dict):
                        deps = self._extract_from_dict(item, source_address, item_path)
                        dependencies.extend(deps)

        return dependencies

    def _extract_from_string(
        self, text: str, source_address: str, attribute_path: str = ""
    ) -> List[TerraformDependency]:
        """
        Extract dependencies from a string value.

        Args:
            text: String to analyze
            source_address: Address of the source object
            attribute_path: Path where this string was found

        Returns:
            List of found dependencies
        """
        dependencies = []

        # Parse all references from the string
        references = self._parse_references_from_string(text)

        # Validate and create dependencies
        for ref in references:
            # Check if reference exists in catalog
            if self.catalog.has_address(ref):
                dependencies.append(
                    TerraformDependency(
                        source_address=source_address,
                        target_address=ref,
                        dependency_type=DependencyType.DIRECT,
                        attribute_path=attribute_path,
                    )
                )

        return dependencies

    def _parse_references_from_string(self, text: str) -> Set[str]:
        """
        Parse all Terraform references from a string.

        Args:
            text: String to parse

        Returns:
            Set of found reference addresses
        """
        references = set()

        # Extract from interpolations ${...}
        interpolations = self.INTERPOLATION_PATTERN.findall(text)
        for interp in interpolations:
            refs = self._parse_terraform_expression(interp)
            references.update(refs)

        # Also check direct references (not in interpolations)
        refs = self._parse_terraform_expression(text)
        references.update(refs)

        return references

    def _parse_terraform_expression(self, expr: str) -> Set[str]:
        """
        Parse Terraform expression and extract references.

        Args:
            expr: Terraform expression string

        Returns:
            Set of reference addresses
        """
        references = set()

        # var.name
        var_matches = re.findall(r"\bvar\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for var_name in var_matches:
            references.add(f"var.{var_name}")

        # local.name (with nested property support)
        local_matches = re.findall(r"\blocal\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for local_name in local_matches:
            references.add(f"local.{local_name}")

        # module.name (ignore .output part for dependency purposes)
        module_matches = re.findall(r"\bmodule\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for module_name in module_matches:
            references.add(f"module.{module_name}")

        # data.type.name
        data_matches = re.findall(
            r"\bdata\.([a-zA-Z_][a-zA-Z0-9_-]*)\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr
        )
        for data_type, data_name in data_matches:
            references.add(f"data.{data_type}.{data_name}")

        # resource_type.name (excluding keywords)
        # Enhanced pattern to avoid false positives
        resource_matches = re.findall(
            r"\b(?!(?:var|local|module|data|provider|terraform|each|count|path|self|for|if|true|false|null)\b)([a-z][a-z0-9_]+)\.([a-zA-Z_][a-zA-Z0-9_-]*)",
            expr,
        )
        for resource_type, resource_name in resource_matches:
            # Validation: resource types must have underscores
            # and shouldn't be common keywords or functions
            if "_" in resource_type and not resource_type.startswith("_"):
                # Additional check: avoid Terraform built-in functions
                if resource_type not in {"try", "can", "merge", "concat", "lookup"}:
                    references.add(f"{resource_type}.{resource_name}")

        return references

    def get_dependencies(self, address: str) -> Optional[ObjectDependencies]:
        """
        Get dependencies for a specific object.

        Args:
            address: The Terraform address

        Returns:
            ObjectDependencies or None if not found
        """
        return self.dependencies.get(address)

    def get_dependency_chain(
        self, address: str, include_implicit: bool = True
    ) -> List[str]:
        """
        Get the full dependency chain for an object (depth-first).

        Args:
            address: The starting address
            include_implicit: Whether to include implicit dependencies (e.g., providers)

        Returns:
            List of addresses in dependency order
        """
        visited = set()
        chain = []

        def visit(addr: str):
            if addr in visited:
                return
            visited.add(addr)

            deps = self.dependencies.get(addr)
            if deps:
                for dep in deps.depends_on:
                    # Skip implicit dependencies if requested
                    if (
                        not include_implicit
                        and dep.dependency_type == DependencyType.IMPLICIT
                    ):
                        continue
                    visit(dep.target_address)

            chain.append(addr)

        visit(address)
        return chain

    def get_reverse_dependency_chain(
        self, address: str, include_implicit: bool = True
    ) -> List[str]:
        """
        Get all objects that depend on this object (reverse dependencies).

        Args:
            address: The target address
            include_implicit: Whether to include implicit dependencies

        Returns:
            List of addresses that reference this object
        """
        visited = set()
        chain = []

        def visit(addr: str):
            if addr in visited:
                return
            visited.add(addr)

            chain.append(addr)

            deps = self.dependencies.get(addr)
            if deps:
                for dep in deps.referenced_by:
                    if (
                        not include_implicit
                        and dep.dependency_type == DependencyType.IMPLICIT
                    ):
                        continue
                    visit(dep.source_address)

        visit(address)
        return chain

    def get_provider_resources(self, provider_address: str) -> List[str]:
        """
        Get all resources that use a specific provider.

        Args:
            provider_address: The provider address (e.g., 'aws' or 'aws.secondary')

        Returns:
            List of resource addresses
        """
        resources = []

        deps = self.dependencies.get(provider_address)
        if deps:
            # Get all objects that reference this provider
            for dep in deps.referenced_by:
                if dep.dependency_type in (
                    DependencyType.PROVIDER,
                    DependencyType.IMPLICIT,
                ):
                    resources.append(dep.source_address)

        return resources

    def detect_cycles(self, include_implicit: bool = False) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.

        Args:
            include_implicit: Whether to include implicit dependencies in cycle detection

        Returns:
            List of cycles (each cycle is a list of addresses)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def visit(addr: str, path: List[str]):
            if addr in rec_stack:
                # Found a cycle
                cycle_start = path.index(addr)
                cycle = path[cycle_start:] + [addr]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if addr in visited:
                return

            visited.add(addr)
            rec_stack.add(addr)
            path.append(addr)

            deps = self.dependencies.get(addr)
            if deps:
                for dep in deps.depends_on:
                    # Skip implicit dependencies if requested
                    if (
                        not include_implicit
                        and dep.dependency_type == DependencyType.IMPLICIT
                    ):
                        continue
                    visit(dep.target_address, path.copy())

            rec_stack.remove(addr)

        for address in self.dependencies.keys():
            if address not in visited:
                visit(address, [])

        return cycles

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert dependency graph to a serializable dictionary.

        Returns:
            Dictionary representation of all dependencies
        """
        result = {}

        for address, obj_deps in self.dependencies.items():
            result[address] = {
                "depends_on": [
                    {
                        "target": dep.target_address,
                        "type": dep.dependency_type.value,
                        "attribute_path": dep.attribute_path,
                    }
                    for dep in obj_deps.depends_on
                ],
                "referenced_by": [
                    {
                        "source": dep.source_address,
                        "type": dep.dependency_type.value,
                        "attribute_path": dep.attribute_path,
                    }
                    for dep in obj_deps.referenced_by
                ],
            }

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the dependency graph.

        Returns:
            Dictionary with graph statistics
        """
        total_objects = len(self.dependencies)
        total_dependencies = sum(
            len(deps.depends_on) for deps in self.dependencies.values()
        )

        dep_type_counts = {}
        for deps in self.dependencies.values():
            for dep in deps.depends_on:
                dep_type = dep.dependency_type.value
                dep_type_counts[dep_type] = dep_type_counts.get(dep_type, 0) + 1

        # Find objects with most dependencies
        most_dependent = sorted(
            self.dependencies.items(), key=lambda x: len(x[1].depends_on), reverse=True
        )[:5]

        # Find most referenced objects
        most_referenced = sorted(
            self.dependencies.items(),
            key=lambda x: len(x[1].referenced_by),
            reverse=True,
        )[:5]

        return {
            "total_objects": total_objects,
            "total_dependencies": total_dependencies,
            "dependencies_by_type": dep_type_counts,
            "auto_detected_providers": dict(self._provider_prefixes),
            "most_dependent_objects": [
                {"address": addr, "dependency_count": len(deps.depends_on)}
                for addr, deps in most_dependent
            ],
            "most_referenced_objects": [
                {"address": addr, "reference_count": len(deps.referenced_by)}
                for addr, deps in most_referenced
            ],
            "cycles_detected": len(self.detect_cycles()),
        }
