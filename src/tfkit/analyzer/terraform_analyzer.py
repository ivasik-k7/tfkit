"""Enhanced Terraform project analyzer with improved parsing and dependency extraction."""

import glob
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    Specialized class for extracting dependencies from Terraform configurations.

    Separates explicit dependencies (depends_on) from implicit dependencies
    (references in configuration).
    """

    # Patterns for finding Terraform references
    PATTERNS = [
        (r"\bvar\.([a-zA-Z_][a-zA-Z0-9_-]*)", "var.{}"),
        (r"\blocal\.([a-zA-Z_][a-zA-Z0-9_-]*)", "local.{}"),
        (r"\bmodule\.([a-zA-Z_][a-zA-Z0-9_-]+)", "module.{}"),
        (r"\bdata\.([a-zA-Z_][a-zA-Z0-9_-]+\.[a-zA-Z_][a-zA-Z0-9_-]*)", "data.{}"),
        (r"\b([a-zA-Z_][a-zA-Z0-9_-]*\.[a-zA-Z_][a-zA-Z0-9_-]*)\b", "{}"),
    ]

    @classmethod
    def extract(cls, config: Any) -> DependencyInfo:
        """
        Extract dependencies from a configuration block.

        Args:
            config: Configuration dictionary or value

        Returns:
            DependencyInfo with separated explicit and implicit dependencies
        """
        dep_info = DependencyInfo()

        if not config:
            return dep_info

        # Handle explicit depends_on
        if isinstance(config, dict):
            depends_on = config.get("depends_on", [])
            if depends_on:
                if isinstance(depends_on, list):
                    dep_info.explicit_dependencies = depends_on
                elif isinstance(depends_on, str):
                    dep_info.explicit_dependencies = [depends_on]

        # Extract implicit dependencies from config values
        config_str = (
            json.dumps(config) if isinstance(config, (dict, list)) else str(config)
        )

        found = set()
        for pattern, template in cls.PATTERNS:
            matches = re.findall(pattern, config_str)
            for match in matches:
                dep_name = template.format(match)
                # Avoid duplicates and self-references
                if dep_name not in found:
                    found.add(dep_name)

        # Remove explicit deps from implicit deps
        explicit_set = set(dep_info.explicit_dependencies)
        dep_info.implicit_dependencies = [d for d in found if d not in explicit_set]

        return dep_info


class FileParser:
    """
    Handles parsing of individual Terraform files.

    Separates file I/O and parsing logic from object creation.
    """

    def __init__(self):
        self._file_cache: Dict[str, List[str]] = {}

    def cache_file(self, file_path: str) -> None:
        """Cache file contents for line number lookups."""
        try:
            with open(file_path, encoding="utf-8") as f:
                self._file_cache[file_path] = f.readlines()
        except (OSError, UnicodeDecodeError):
            self._file_cache[file_path] = []

    def find_line_number(
        self, file_path: str, search_pattern: str, object_name: str
    ) -> int:
        """
        Find the line number where an object is defined.

        Args:
            file_path: Path to the file
            search_pattern: Pattern to search for (e.g., 'resource "aws_instance"')
            object_name: Name of the object

        Returns:
            Line number (1-indexed), or 1 if not found
        """
        if file_path not in self._file_cache:
            return 1

        lines = self._file_cache[file_path]

        # Try exact match first
        for i, line in enumerate(lines, 1):
            if object_name in line and search_pattern in line:
                return i

        # Fallback to pattern match
        for i, line in enumerate(lines, 1):
            if search_pattern in line:
                return i

        return 1

    def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Terraform file and return the parsed structure.

        Args:
            file_path: Path to the .tf or .tf.json file

        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if file_path.endswith(".tf.json"):
                return json.loads(content)
            else:
                return hcl2.loads(content)

        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None


class ObjectFactory:
    """
    Factory for creating TerraformObject instances from parsed HCL.

    Centralizes object creation logic with proper type handling.
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

        dep_info = DependencyExtractor.extract(config)

        # Extract provider
        provider = self._extract_provider_from_type(resource_type)
        provider_info = ProviderInfo(provider_name=provider) if provider else None

        return TerraformObject(
            type=ResourceType.RESOURCE,
            name=instance_name,
            full_name=full_name,
            location=location,
            dependency_info=dep_info,
            attributes=config or {},
            resource_type=resource_type,
            provider_info=provider_info,
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

        dep_info = DependencyExtractor.extract(config)

        provider = self._extract_provider_from_type(data_type)
        provider_info = ProviderInfo(provider_name=provider) if provider else None

        return TerraformObject(
            type=ResourceType.DATA,
            name=instance_name,
            full_name=full_name,
            location=location,
            dependency_info=dep_info,
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

        dep_info = DependencyExtractor.extract(config)

        return TerraformObject(
            type=ResourceType.MODULE,
            name=module_name,
            full_name=full_name,
            location=location,
            dependency_info=dep_info,
            attributes=config or {},
            source=config.get("source") if isinstance(config, dict) else None,
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

        if isinstance(config, dict):
            var_type = self._format_type(config.get("type"))
            default_val = config.get("default")
            description = config.get("description")

        return TerraformObject(
            type=ResourceType.VARIABLE,
            name=var_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),  # Variables have no dependencies
            attributes=config or {},
            variable_type=var_type,
            default_value=default_val,
            description=description,
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

        dep_info = DependencyExtractor.extract(config)

        sensitive = False
        description = None

        if isinstance(config, dict):
            sensitive = config.get("sensitive", False)
            description = config.get("description")

        return TerraformObject(
            type=ResourceType.OUTPUT,
            name=output_name,
            full_name=full_name,
            location=location,
            dependency_info=dep_info,
            attributes=config or {},
            sensitive=sensitive,
            description=description,
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
        if isinstance(config, dict):
            alias = config.get("alias")
            version = config.get("version")

        provider_info = ProviderInfo(
            provider_name=provider_name,
            provider_alias=alias,
            provider_version=version,
        )

        return TerraformObject(
            type=ResourceType.PROVIDER,
            name=provider_name,
            full_name=full_name,
            location=location,
            dependency_info=DependencyInfo(),  # Providers have no dependencies
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

        dep_info = DependencyExtractor.extract({"value": value})

        return TerraformObject(
            type=ResourceType.LOCAL,
            name=local_name,
            full_name=full_name,
            location=location,
            dependency_info=dep_info,
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
        """Extract provider prefix from resource type (e.g., 'aws' from 'aws_instance')."""
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

        # Handle complex types (lists, maps, objects)
        return str(type_value)


class TerraformAnalyzer:
    """
    Main analyzer for Terraform projects.

    Orchestrates parsing, object creation, and dependency graph building.
    """

    def __init__(self):
        self.project: Optional[TerraformProject] = None
        self.file_parser = FileParser()
        self.object_factory = ObjectFactory(self.file_parser)

    def analyze_project(self, project_path: str) -> TerraformProject:
        """
        Analyze a Terraform project and build complete object model.

        Args:
            project_path: Path to the Terraform project directory

        Returns:
            TerraformProject with all parsed objects and dependencies

        Raises:
            ImportError: If python-hcl2 is not installed
            ValueError: If project path is invalid or no Terraform files found
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

        tf_files = self._find_terraform_files(project_path)

        if not tf_files:
            raise ValueError(f"No Terraform files found in {project_path}")

        self.project.metadata.total_files = len(tf_files)

        for tf_file in tf_files:
            self.file_parser.cache_file(tf_file)

        for tf_file in tf_files:
            self._parse_terraform_file(tf_file)

        self._parse_tfvars_files(project_path)
        self._parse_backend_config(project_path)

        self.project.build_dependency_graph()

        return self.project

    def _find_terraform_files(self, project_path: Path) -> List[str]:
        """Find all Terraform files in the project."""
        patterns = [
            "**/*.tf",
            "**/*.tf.json",
            "**/*_override.tf",
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

        # Extract each type of object
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
                break  # Use first backend found
