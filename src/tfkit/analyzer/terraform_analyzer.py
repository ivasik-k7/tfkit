import glob
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import hcl2
except ImportError:
    hcl2 = None

from .models import (
    DependencyInfo,
    LocationInfo,
    ProviderInfo,
    ResourceType,
    TerraformObject,
)
from .project import TerraformProject


class DependencyExtractor:
    """
    Enhanced dependency extractor with comprehensive dependency analysis.
    """

    # Enhanced patterns for finding Terraform references
    PATTERNS = [
        # Variables: var.name
        (r"\bvar\.([a-zA-Z_][a-zA-Z0-9_-]*)\b", "var.{}", 1),
        # Locals: local.name
        (r"\blocal\.([a-zA-Z_][a-zA-Z0-9_-]*)\b", "local.{}", 1),
        # Modules: module.name (any attribute)
        (r"\bmodule\.([a-zA-Z_][a-zA-Z0-9_-]*)\.", "module.{}", 1),
        # Data sources: data.type.name
        (
            r"\bdata\.([a-zA-Z_][a-zA-Z0-9_-]*)\.([a-zA-Z_][a-zA-Z0-9_-]*)\b",
            "data.{}.{}",
            2,
        ),
        # Resources: resource_type.name (must have at least one dot after name)
        (r"\b([a-z][a-z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_-]*)\.", "{}.{}", 2),
    ]

    def __init__(self, all_objects: Dict[str, TerraformObject]):
        self.all_objects = all_objects
        self.defined_names = set(all_objects.keys())

    def extract(self, config: Any, current_object_name: str = None) -> DependencyInfo:
        """
        Extract comprehensive dependency information from configuration.

        Args:
            config: The configuration to analyze (dict, list, or primitive)
            current_object_name: Name of the current object to avoid self-references

        Returns:
            DependencyInfo with all discovered dependencies
        """
        dep_info = DependencyInfo()

        if not config:
            return dep_info

        # Step 1: Handle explicit depends_on
        if isinstance(config, dict):
            depends_on = config.get("depends_on", [])
            if depends_on:
                if isinstance(depends_on, list):
                    dep_info.explicit_dependencies = [
                        self._normalize_reference(str(d)) for d in depends_on
                    ]
                elif isinstance(depends_on, str):
                    dep_info.explicit_dependencies = [
                        self._normalize_reference(depends_on)
                    ]

        # Step 2: Convert config to searchable string
        config_str = self._serialize_config(config)

        # Step 3: Find all references using patterns
        found_references = self._extract_references(config_str, current_object_name)

        # Step 4: Categorize dependencies
        explicit_set = set(dep_info.explicit_dependencies)

        for dep in found_references:
            # Skip if already in explicit dependencies
            if dep in explicit_set:
                continue

            # Check if dependency exists in project
            if dep in self.defined_names:
                dep_info.implicit_dependencies.append(dep)
            else:
                # Check if it's a partial reference that might match
                matching = self._find_matching_objects(dep)
                if matching:
                    dep_info.implicit_dependencies.extend(matching)
                else:
                    dep_info.missing_dependencies.append(dep)

        # Step 5: Remove duplicates while preserving order
        dep_info.implicit_dependencies = list(
            dict.fromkeys(dep_info.implicit_dependencies)
        )
        dep_info.missing_dependencies = list(
            dict.fromkeys(dep_info.missing_dependencies)
        )

        return dep_info

    def _serialize_config(self, config: Any) -> str:
        """Convert configuration to searchable string format."""
        if isinstance(config, dict):
            # Recursively process nested structures
            return json.dumps(config, default=str, indent=None)
        elif isinstance(config, list):
            return json.dumps(config, default=str, indent=None)
        else:
            return str(config)

    def _extract_references(
        self, config_str: str, current_object_name: Optional[str]
    ) -> Set[str]:
        """Extract all Terraform references from configuration string."""
        found_references = set()

        for pattern, template, group_count in self.PATTERNS:
            matches = re.finditer(pattern, config_str)

            for match in matches:
                try:
                    if group_count == 1:
                        dep_name = template.format(match.group(1))
                    elif group_count == 2:
                        dep_name = template.format(match.group(1), match.group(2))
                    else:
                        continue

                    # Normalize and validate
                    dep_name = self._normalize_reference(dep_name)

                    # Skip self-references
                    if dep_name == current_object_name:
                        continue

                    # Skip if it's clearly not a valid reference
                    if not self._is_valid_reference(dep_name):
                        continue

                    found_references.add(dep_name)

                except (IndexError, ValueError):
                    continue

        return found_references

    def _normalize_reference(self, ref: str) -> str:
        """Normalize a reference string."""
        # Remove quotes and whitespace
        ref = ref.strip().strip('"').strip("'").strip()

        # Remove trailing dots
        ref = ref.rstrip(".")

        return ref

    def _is_valid_reference(self, ref: str) -> bool:
        """Check if a reference looks valid."""
        if not ref:
            return False

        # Must not contain invalid characters
        if any(char in ref for char in [" ", "\n", "\t", '"', "'", "{", "}", "[", "]"]):
            return False

        # Must have valid structure
        parts = ref.split(".")
        if len(parts) < 2:
            return False

        # First part should be a valid prefix
        valid_prefixes = {
            "var",
            "local",
            "module",
            "data",
            "output",
            "provider",
            "terraform",
        }

        # Check if it's a prefixed reference or a resource reference
        if parts[0] in valid_prefixes:
            return True

        # For resource references (type.name), check if type looks like a resource type
        if len(parts) >= 2 and "_" in parts[0]:
            return True

        return False

    def _find_matching_objects(self, partial_ref: str) -> List[str]:
        """Find objects that match a partial reference."""
        matches = []

        for obj_name in self.defined_names:
            if obj_name.startswith(partial_ref):
                matches.append(obj_name)

        return matches

    def detect_circular_dependencies(self) -> Dict[str, List[str]]:
        """
        Detect circular dependencies across all objects.

        Returns:
            Dictionary mapping object names to their circular dependency paths
        """
        circular_deps = {}
        visited = set()
        rec_stack = set()

        def visit(obj_name: str, path: List[str]) -> Optional[List[str]]:
            """DFS to detect cycles."""
            if obj_name in rec_stack:
                # Found a cycle
                cycle_start = path.index(obj_name)
                return path[cycle_start:] + [obj_name]

            if obj_name in visited:
                return None

            visited.add(obj_name)
            rec_stack.add(obj_name)
            path.append(obj_name)

            if obj_name in self.all_objects:
                obj = self.all_objects[obj_name]
                for dep in obj.dependency_info.all_dependencies:
                    if dep in self.all_objects:
                        cycle = visit(dep, path.copy())
                        if cycle:
                            return cycle

            rec_stack.remove(obj_name)
            return None

        # Check each object
        for obj_name in self.all_objects:
            if obj_name not in visited:
                cycle = visit(obj_name, [])
                if cycle:
                    # Record cycle for all objects in it
                    for cycle_obj in cycle[:-1]:  # Exclude duplicate last element
                        if cycle_obj not in circular_deps:
                            circular_deps[cycle_obj] = cycle

        return circular_deps


class FileParser:
    """
    Handles parsing of individual Terraform files.
    """

    def __init__(self):
        self._file_cache: Dict[str, List[str]] = {}

    def cache_file(self, file_path: str) -> None:
        """Cache file contents for line number lookups."""
        try:
            with open(file_path, encoding="utf-8") as f:
                self._file_cache[file_path] = f.readlines()
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not cache file {file_path}: {e}")
            self._file_cache[file_path] = []

    def find_line_number(
        self, file_path: str, search_pattern: str, object_name: str
    ) -> int:
        """
        Find the line number where an object is defined.
        """
        if file_path not in self._file_cache:
            return 1

        lines = self._file_cache[file_path]

        # Try to find the exact object definition
        for i, line in enumerate(lines, 1):
            if search_pattern in line and f'"{object_name}"' in line:
                return i

        # Fallback: find just the pattern
        for i, line in enumerate(lines, 1):
            if search_pattern in line:
                return i

        return 1

    def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Terraform file and return the parsed structure.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if file_path.endswith(".tf.json"):
                return json.loads(content)
            else:
                if hcl2 is None:
                    raise ImportError("python-hcl2 is required for parsing .tf files")
                return hcl2.loads(content)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None


class ObjectFactory:
    """
    Factory for creating TerraformObject instances from parsed HCL.
    Creates objects without dependencies initially.
    """

    def __init__(self, file_parser: FileParser):
        self.file_parser = file_parser

    def create_resource(
        self,
        resource_type: str,
        instance_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a resource object."""
        full_name = f"{resource_type}.{instance_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, f'resource "{resource_type}"', instance_name
            ),
        )

        # Extract provider
        provider = self._extract_provider_from_type(resource_type)
        provider_info = ProviderInfo(provider_name=provider) if provider else None

        # Extract metadata
        tags = config.get("tags", {}) if isinstance(config, dict) else {}
        description = config.get("description") if isinstance(config, dict) else None

        return TerraformObject(
            type=ResourceType.RESOURCE,
            name=instance_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),  # Empty initially
            attributes=config or {},
            resource_type=resource_type,
            provider_info=provider_info,
            tags=tags,
            description=description,
        )

    def create_data_source(
        self,
        data_type: str,
        instance_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a data source object."""
        full_name = f"data.{data_type}.{instance_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, f'data "{data_type}"', instance_name
            ),
        )

        provider = self._extract_provider_from_type(data_type)
        provider_info = ProviderInfo(provider_name=provider) if provider else None

        return TerraformObject(
            type=ResourceType.DATA,
            name=instance_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
            resource_type=data_type,
            provider_info=provider_info,
        )

    def create_module(
        self,
        module_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a module object."""
        full_name = f"module.{module_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, 'module "', module_name
            ),
        )

        source = config.get("source") if isinstance(config, dict) else None
        version = config.get("version") if isinstance(config, dict) else None

        return TerraformObject(
            type=ResourceType.MODULE,
            name=module_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
            source=source,
            module_version=version,
        )

    def create_variable(
        self,
        var_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a variable object."""
        full_name = f"var.{var_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, 'variable "', var_name
            ),
        )

        var_type = None
        default_val = None
        description = None
        nullable = True
        sensitive = False

        if isinstance(config, dict):
            var_type = self._format_type(config.get("type"))
            default_val = config.get("default")
            description = config.get("description")
            nullable = config.get("nullable", True)
            sensitive = config.get("sensitive", False)

        return TerraformObject(
            type=ResourceType.VARIABLE,
            name=var_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
            variable_type=var_type,
            default_value=default_val,
            description=description,
            nullable=nullable,
            sensitive=sensitive,
        )

    def create_output(
        self,
        output_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create an output object."""
        full_name = f"output.{output_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, 'output "', output_name
            ),
        )

        sensitive = False
        description = None
        output_value = None

        if isinstance(config, dict):
            sensitive = config.get("sensitive", False)
            description = config.get("description")
            output_value = config.get("value")

        return TerraformObject(
            type=ResourceType.OUTPUT,
            name=output_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
            sensitive=sensitive,
            description=description,
            output_value=output_value,
        )

    def create_provider(
        self,
        provider_name: str,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a provider object."""
        full_name = f"provider.{provider_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, 'provider "', provider_name
            ),
        )

        alias = None
        version = None
        provider_config = {}
        if isinstance(config, dict):
            alias = config.get("alias")
            version = config.get("version")
            provider_config = {
                k: v for k, v in config.items() if k not in ["alias", "version"]
            }

        provider_info = ProviderInfo(
            provider_name=provider_name,
            provider_alias=alias,
            provider_version=version,
            provider_config=provider_config,
        )

        return TerraformObject(
            type=ResourceType.PROVIDER,
            name=provider_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
            provider_info=provider_info,
        )

    def create_local(
        self,
        local_name: str,
        value: Any,
        file_path: str,
    ) -> TerraformObject:
        """Create a local value object."""
        full_name = f"local.{local_name}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(
                file_path, "locals", local_name
            ),
        )

        return TerraformObject(
            type=ResourceType.LOCAL,
            name=local_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes={"value": value},
        )

    def create_terraform_block(
        self,
        block_index: int,
        config: Dict[str, Any],
        file_path: str,
    ) -> TerraformObject:
        """Create a terraform configuration block object."""
        full_name = f"terraform.block_{block_index}"

        location = LocationInfo(
            file_path=file_path,
            line_number=self.file_parser.find_line_number(file_path, "terraform", ""),
        )

        return TerraformObject(
            type=ResourceType.TERRAFORM,
            name=f"block_{block_index}",
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),
            attributes=config or {},
        )

    def _extract_provider_from_type(self, resource_type: str) -> Optional[str]:
        """Extract provider prefix from resource type."""
        if not resource_type or not isinstance(resource_type, str):
            return None

        parts = resource_type.split("_", 1)
        return parts[0] if parts else None

    def _format_type(self, type_value: Any) -> Optional[str]:
        """Format a Terraform type value into a readable string."""
        if type_value is None:
            return None

        if isinstance(type_value, str):
            return type_value

        return str(type_value)


class TerraformAnalyzer:
    """
    Robust Terraform project analyzer with proper three-phase analysis.

    Phase 1: Parse and create all objects (no dependencies)
    Phase 2: Extract and build all dependencies
    Phase 3: Compute states and detect circular dependencies
    """

    def __init__(self):
        self.project: Optional[TerraformProject] = None
        self.file_parser = FileParser()
        self.object_factory = ObjectFactory(self.file_parser)

    def analyze_project(self, project_path: str) -> TerraformProject:
        """
        Analyze a Terraform project with proper three-phase approach.
        """
        if hcl2 is None:
            raise ImportError(
                "python-hcl2 is required for Terraform analysis. "
                "Install with: pip install python-hcl2"
            )

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        self.project = TerraformProject(project_path=str(project_path))

        # Find all Terraform files
        tf_files = self._find_terraform_files(project_path)

        if not tf_files:
            raise ValueError(f"No Terraform files found in {project_path}")

        self.project.metadata.total_files = len(tf_files)

        # Cache all files for line number lookups
        for tf_file in tf_files:
            self.file_parser.cache_file(tf_file)

        # ===== PHASE 1: Parse and create all objects =====
        for tf_file in tf_files:
            self._parse_terraform_file(tf_file)

        # ===== PHASE 2: Extract and build dependencies =====
        self._build_all_dependencies()

        # ===== PHASE 3: Detect circular dependencies and compute states =====
        self._detect_all_circular_dependencies()

        self._compute_all_states()

        # Parse additional files
        self._parse_tfvars_files(project_path)
        self._parse_backend_config(project_path)

        return self.project

    def _build_all_dependencies(self) -> None:
        """
        Build dependencies for all objects in a single pass.
        """
        if not self.project:
            return

        # Create dependency extractor with all objects
        extractor = DependencyExtractor(self.project.all_objects)

        for obj_name, obj in self.project.all_objects.items():
            if obj.type in [
                ResourceType.VARIABLE,
                ResourceType.PROVIDER,
                ResourceType.TERRAFORM,
            ]:
                continue

            dep_info = extractor.extract(obj.attributes, obj_name)
            obj.dependency_info = dep_info

        for obj_name, obj in self.project.all_objects.items():
            for dep in obj.dependency_info.all_dependencies:
                if dep in self.project.all_objects:
                    dep_obj = self.project.all_objects[dep]
                    if obj_name not in dep_obj.dependency_info.dependent_objects:
                        dep_obj.dependency_info.dependent_objects.append(obj_name)

        self._build_provider_relationships()

    def _detect_all_circular_dependencies(self) -> None:
        """
        Detect circular dependencies across all objects.
        """
        if not self.project:
            return

        extractor = DependencyExtractor(self.project.all_objects)
        circular_deps = extractor.detect_circular_dependencies()

        # Update each object with its circular dependency information
        for obj_name, cycle in circular_deps.items():
            if obj_name in self.project.all_objects:
                obj = self.project.all_objects[obj_name]
                obj.dependency_info.circular_dependencies = cycle

    def _compute_all_states(self) -> None:
        """
        Compute states for all objects after dependencies are built.
        """
        if not self.project:
            return

        # Set all_objects cache for each object (needed for provider state computation)
        for obj in self.project.all_objects.values():
            obj.set_all_objects_cache(self.project.all_objects)

        # Invalidate any cached states
        for obj in self.project.all_objects.values():
            obj.invalidate_state()

        # States will be computed lazily when accessed via the state property

    def _find_terraform_files(self, project_path: Path) -> List[str]:
        """Find all Terraform files in the project."""
        patterns = [
            "**/*.tf",
            "**/*.tf.json",
        ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(str(project_path / pattern), recursive=True))

        return sorted(set(files))

    def _parse_terraform_file(self, file_path: str) -> None:
        """Parse a single Terraform file and add objects to project."""
        parsed = self.file_parser.parse_file(file_path)
        if not parsed:
            return

        # Extract each type of object (without dependencies)
        self._extract_resources(parsed.get("resource", []), file_path)
        self._extract_data_sources(parsed.get("data", []), file_path)
        self._extract_modules(parsed.get("module", []), file_path)
        self._extract_variables(parsed.get("variable", []), file_path)
        self._extract_outputs(parsed.get("output", []), file_path)
        self._extract_providers(parsed.get("provider", []), file_path)
        self._extract_terraform_blocks(parsed.get("terraform", []), file_path)
        self._extract_locals(parsed.get("locals", []), file_path)

    def _extract_resources(self, resources: List[Dict], file_path: str) -> None:
        """Extract resources from parsed HCL."""
        for resource_block in resources:
            for resource_type, instances in resource_block.items():
                for instance_name, config in instances.items():
                    obj = self.object_factory.create_resource(
                        resource_type, instance_name, config, file_path
                    )
                    self.project.add_object(obj)

    def _extract_data_sources(self, data_sources: List[Dict], file_path: str) -> None:
        """Extract data sources from parsed HCL."""
        for data_block in data_sources:
            for data_type, instances in data_block.items():
                for instance_name, config in instances.items():
                    obj = self.object_factory.create_data_source(
                        data_type, instance_name, config, file_path
                    )
                    self.project.add_object(obj)

    def _extract_modules(self, modules: List[Dict], file_path: str) -> None:
        """Extract modules from parsed HCL."""
        for module_block in modules:
            for module_name, config in module_block.items():
                obj = self.object_factory.create_module(module_name, config, file_path)
                self.project.add_object(obj)

    def _extract_variables(self, variables: List[Dict], file_path: str) -> None:
        """Extract variables from parsed HCL."""
        for var_block in variables:
            for var_name, config in var_block.items():
                obj = self.object_factory.create_variable(var_name, config, file_path)
                self.project.add_object(obj)

    def _extract_outputs(self, outputs: List[Dict], file_path: str) -> None:
        """Extract outputs from parsed HCL."""
        for output_block in outputs:
            for output_name, config in output_block.items():
                obj = self.object_factory.create_output(output_name, config, file_path)
                self.project.add_object(obj)

    def _extract_providers(self, providers: List[Dict], file_path: str) -> None:
        """Extract providers from parsed HCL."""
        for provider_block in providers:
            for provider_name, config in provider_block.items():
                obj = self.object_factory.create_provider(
                    provider_name, config, file_path
                )
                self.project.add_object(obj)

    def _extract_terraform_blocks(
        self, terraform_blocks: List[Dict], file_path: str
    ) -> None:
        """Extract terraform configuration blocks."""
        for i, terraform_block in enumerate(terraform_blocks):
            obj = self.object_factory.create_terraform_block(
                i, terraform_block, file_path
            )
            self.project.add_object(obj)

    def _extract_locals(self, locals_blocks: List[Dict], file_path: str) -> None:
        """Extract local values from parsed HCL."""
        for locals_block in locals_blocks:
            for local_name, value in locals_block.items():
                obj = self.object_factory.create_local(local_name, value, file_path)
                self.project.add_object(obj)

    def _parse_tfvars_files(self, project_path: Path) -> None:
        """Parse .tfvars files for variable values."""
        patterns = ["**/*.tfvars", "**/*.tfvars.json"]

        tfvars_files = []
        for pattern in patterns:
            tfvars_files.extend(glob.glob(str(project_path / pattern), recursive=True))

        for tfvars_file in tfvars_files:
            try:
                with open(tfvars_file, encoding="utf-8") as f:
                    if tfvars_file.endswith(".json"):
                        variables = json.load(f)
                    else:
                        variables = hcl2.load(f)

                self.project.tfvars_files[tfvars_file] = variables

            except Exception as e:
                print(f"Warning: Could not parse tfvars file {tfvars_file}: {e}")

    def _parse_backend_config(self, project_path: Path) -> None:
        """Extract backend configuration from terraform blocks."""
        for obj in self.project.terraform_blocks.values():
            if "backend" in obj.attributes:
                self.project.backend_config = obj.attributes["backend"]
                break

    def _build_provider_relationships(self) -> None:
        """
        Build implicit provider relationships based on resource types.
        Resources implicitly depend on their providers.
        """
        if not self.project:
            return

        providers = {}
        for obj_name, obj in self.project.all_objects.items():
            if obj.type == ResourceType.PROVIDER:
                provider_name = obj.name
                provider_alias = (
                    obj.provider_info.provider_alias if obj.provider_info else None
                )

                if provider_alias:
                    providers[f"{provider_name}.{provider_alias}"] = obj_name
                else:
                    providers[provider_name] = obj_name

        relationships_built = 0
        for obj_name, obj in self.project.all_objects.items():
            if obj.type not in [ResourceType.RESOURCE, ResourceType.DATA]:
                continue

            provider_prefix = obj.provider_prefix
            if not provider_prefix:
                continue

            explicit_provider = None
            if isinstance(obj.attributes, dict):
                explicit_provider = obj.attributes.get("provider")

            provider_obj_name = None
            if explicit_provider:
                if explicit_provider in providers:
                    provider_obj_name = providers[explicit_provider]
            elif provider_prefix in providers:
                provider_obj_name = providers[provider_prefix]

            if provider_obj_name:
                if provider_obj_name not in obj.dependency_info.implicit_dependencies:
                    obj.dependency_info.implicit_dependencies.append(provider_obj_name)
                    relationships_built += 1

                if provider_obj_name in self.project.all_objects:
                    provider_obj = self.project.all_objects[provider_obj_name]
                    if obj_name not in provider_obj.dependency_info.dependent_objects:
                        provider_obj.dependency_info.dependent_objects.append(obj_name)
