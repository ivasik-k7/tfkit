"""Terraform project analyzer."""

import glob
import json
import os
import re
from pathlib import Path
from typing import Any, List, Optional

try:
    import hcl2
except ImportError:
    hcl2 = None

from .models import ResourceType, TerraformObject, TerraformProject


class TerraformAnalyzer:
    def __init__(self):
        self.project = TerraformProject(
            resources={},
            data_sources={},
            modules={},
            variables={},
            outputs={},
            providers={},
            terraform_blocks={},
            locals={},
        )
        self._file_line_cache = {}
        self._dependency_graph = {}

    def analyze_project(self, project_path: str) -> TerraformProject:
        """Analyze Terraform project and build object map"""
        if hcl2 is None:
            raise ImportError(
                "python-hcl2 is required for Terraform analysis. Install with: pip install python-hcl2"
            )

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        self._reset_analysis_state()

        tf_files = self._find_terraform_files(project_path)

        if not tf_files:
            raise ValueError(f"No Terraform files found in {project_path}")

        self._build_file_cache(tf_files)

        # Parse all files
        for tf_file in tf_files:
            self._parse_tf_file(tf_file)

        # Parse additional file types
        self._parse_tfvars_files(project_path)
        self._parse_backend_files(project_path)

        # Build enhanced dependency graph
        self._build_dependency_graph()

        # Analyze project structure
        self._analyze_project_structure(project_path)

        return self.project

    def _reset_analysis_state(self):
        """Reset analysis state for new analysis"""
        self.project = TerraformProject(
            resources={},
            data_sources={},
            modules={},
            variables={},
            outputs={},
            providers={},
            terraform_blocks={},
            locals={},
        )
        self._file_line_cache = {}
        self._dependency_graph = {}

    def _find_terraform_files(self, project_path: Path) -> List[str]:
        """Find all Terraform-related files in the project"""
        tf_files = []

        # Main .tf files
        tf_files.extend(glob.glob(str(project_path / "**" / "*.tf"), recursive=True))

        # JSON .tf files
        tf_files.extend(
            glob.glob(str(project_path / "**" / "*.tf.json"), recursive=True)
        )

        # Override files
        tf_files.extend(
            glob.glob(str(project_path / "**" / "*_override.tf"), recursive=True)
        )

        return sorted(tf_files)

    def _build_file_cache(self, tf_files: List[str]):
        """Build cache of file contents for line number resolution"""
        for file_path in tf_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._file_line_cache[file_path] = f.readlines()
            except (UnicodeDecodeError, IOError):
                # Fallback for binary files or read errors
                self._file_line_cache[file_path] = []

    def _find_line_number(
        self, file_path: str, search_text: str, object_name: str
    ) -> int:
        """Find the line number where an object is defined"""
        if file_path not in self._file_line_cache:
            return 1

        lines = self._file_line_cache[file_path]

        # Try exact pattern matching first
        for i, line in enumerate(lines, 1):
            if object_name in line and search_text in line:
                return i

        # Fallback: find resource type definition
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i

        return 1

    def _parse_tf_file(self, file_path: str):
        """Parse a single Terraform file with enhanced error handling"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Handle JSON format Terraform files
            if file_path.endswith(".tf.json"):
                parsed = json.loads(content)
            else:
                parsed = hcl2.loads(content)

            # Extract different resource types with enhanced parsing
            self._extract_resources(parsed.get("resource", []), file_path)
            self._extract_data_sources(parsed.get("data", []), file_path)
            self._extract_modules(parsed.get("module", []), file_path)
            self._extract_variables(parsed.get("variable", []), file_path)
            self._extract_outputs(parsed.get("output", []), file_path)
            self._extract_providers(parsed.get("provider", []), file_path)
            self._extract_terraform_blocks(parsed.get("terraform", []), file_path)
            self._extract_locals(parsed.get("local", []), file_path)

        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

    def _parse_tfvars_files(self, project_path: Path):
        """Parse .tfvars files for variable values"""
        tfvars_files = glob.glob(str(project_path / "**" / "*.tfvars"), recursive=True)
        tfvars_files.extend(
            glob.glob(str(project_path / "**" / "*.tfvars.json"), recursive=True)
        )

        for tfvars_file in tfvars_files:
            try:
                with open(tfvars_file, "r", encoding="utf-8") as f:
                    if tfvars_file.endswith(".json"):
                        variables = json.load(f)
                    else:
                        variables = hcl2.load(f)

                # Store tfvars data for reference
                self.project.tfvars_files[tfvars_file] = variables

            except Exception as e:
                print(f"Warning: Could not parse tfvars file {tfvars_file}: {e}")

    def _parse_backend_files(self, project_path: Path):
        """Parse backend configuration files"""
        backend_files = glob.glob(
            str(project_path / "**" / ".terraform" / "**" / "*"), recursive=True
        )

        # Extract backend configuration from terraform blocks
        for terraform_block in self.project.terraform_blocks.values():
            if "backend" in terraform_block.attributes:
                self.project.backend_config = terraform_block.attributes["backend"]

    def _extract_resources(self, resources: List, file_path: str):
        """Extract resources from parsed HCL with enhanced metadata"""
        for resource_block in resources:
            for resource_type, resource_instances in resource_block.items():
                for instance_name, config in resource_instances.items():
                    full_name = f"{resource_type}.{instance_name}"

                    # Find exact line number
                    line_number = self._find_line_number(
                        file_path, f'resource "{resource_type}"', instance_name
                    )

                    self.project.resources[full_name] = TerraformObject(
                        type=ResourceType.RESOURCE,
                        name=instance_name,
                        full_name=full_name,
                        attributes=config or {},
                        dependencies=self._find_enhanced_dependencies(config),
                        file_path=file_path,
                        line_number=line_number,
                        resource_type=resource_type,
                        provider=self._extract_provider_from_resource(resource_type),
                    )

    def _extract_data_sources(self, data_sources: List, file_path: str):
        """Extract data sources from parsed HCL with enhanced metadata"""
        for data_block in data_sources:
            for data_type, data_instances in data_block.items():
                for instance_name, config in data_instances.items():
                    full_name = f"data.{data_type}.{instance_name}"

                    line_number = self._find_line_number(
                        file_path, f'data "{data_type}"', instance_name
                    )

                    self.project.data_sources[full_name] = TerraformObject(
                        type=ResourceType.DATA,
                        name=instance_name,
                        full_name=full_name,
                        attributes=config or {},
                        dependencies=self._find_enhanced_dependencies(config),
                        file_path=file_path,
                        line_number=line_number,
                        resource_type=data_type,
                        provider=self._extract_provider_from_data_source(data_type),
                    )

    def _extract_modules(self, modules: List, file_path: str):
        """Extract modules from parsed HCL with enhanced metadata"""
        for module_block in modules:
            for module_name, config in module_block.items():
                full_name = f"module.{module_name}"

                line_number = self._find_line_number(file_path, 'module "', module_name)

                self.project.modules[full_name] = TerraformObject(
                    type=ResourceType.MODULE,
                    name=module_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=self._find_enhanced_dependencies(config),
                    file_path=file_path,
                    line_number=line_number,
                    source=config.get("source") if isinstance(config, dict) else None,
                )

    def _extract_variables(self, variables: List, file_path: str):
        """Extract variables from parsed HCL with enhanced metadata"""
        for var_block in variables:
            for var_name, config in var_block.items():
                full_name = f"var.{var_name}"

                line_number = self._find_line_number(file_path, 'variable "', var_name)

                self.project.variables[full_name] = TerraformObject(
                    type=ResourceType.VARIABLE,
                    name=var_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=[],
                    file_path=file_path,
                    line_number=line_number,
                    variable_type=config.get("type")
                    if isinstance(config, dict)
                    else None,
                    default_value=config.get("default")
                    if isinstance(config, dict)
                    else None,
                )

    def _extract_outputs(self, outputs: List, file_path: str):
        """Extract outputs from parsed HCL with enhanced metadata"""
        for output_block in outputs:
            for output_name, config in output_block.items():
                full_name = f"output.{output_name}"

                line_number = self._find_line_number(file_path, 'output "', output_name)

                self.project.outputs[full_name] = TerraformObject(
                    type=ResourceType.OUTPUT,
                    name=output_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=self._find_enhanced_dependencies(config),
                    file_path=file_path,
                    line_number=line_number,
                    description=config.get("description")
                    if isinstance(config, dict)
                    else None,
                    sensitive=config.get("sensitive")
                    if isinstance(config, dict)
                    else False,
                )

    def _extract_providers(self, providers: List, file_path: str):
        """Extract providers from parsed HCL with enhanced metadata"""
        for provider_block in providers:
            for provider_name, config in provider_block.items():
                full_name = f"provider.{provider_name}"

                line_number = self._find_line_number(
                    file_path, 'provider "', provider_name
                )

                self.project.providers[full_name] = TerraformObject(
                    type=ResourceType.PROVIDER,
                    name=provider_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=[],
                    file_path=file_path,
                    line_number=line_number,
                    alias=config.get("alias") if isinstance(config, dict) else None,
                )

    def _extract_terraform_blocks(self, terraform_blocks: List, file_path: str):
        """Extract terraform configuration blocks with enhanced metadata"""
        for i, terraform_block in enumerate(terraform_blocks):
            full_name = f"terraform.block_{i}"

            line_number = self._find_line_number(file_path, "terraform", "")

            self.project.terraform_blocks[full_name] = TerraformObject(
                type=ResourceType.TERRAFORM,
                name=f"block_{i}",
                full_name=full_name,
                attributes=terraform_block or {},
                dependencies=[],
                file_path=file_path,
                line_number=line_number,
            )

    def _extract_locals(self, locals_blocks: List, file_path: str):
        """Extract local values from parsed HCL"""
        for locals_block in locals_blocks:
            for local_name, value in locals_block.items():
                full_name = f"local.{local_name}"

                line_number = self._find_line_number(file_path, "locals", local_name)

                self.project.locals[full_name] = TerraformObject(
                    type=ResourceType.LOCAL,
                    name=local_name,
                    full_name=full_name,
                    attributes={"value": value},
                    dependencies=self._find_enhanced_dependencies({"value": value}),
                    file_path=file_path,
                    line_number=line_number,
                )

    def _extract_provider_from_resource(self, resource_type: str) -> Optional[str]:
        """Extract provider name from resource type"""
        if "." in resource_type:
            return resource_type.split("_")[0]
        return None

    def _extract_provider_from_data_source(self, data_type: str) -> Optional[str]:
        """Extract provider name from data source type"""
        if "." in data_type:
            return data_type.split("_")[0]
        return None

    def _find_enhanced_dependencies(self, config: Any) -> List[str]:
        """Find dependencies in configuration with enhanced pattern matching"""
        if not config:
            return []

        dependencies = []
        config_str = (
            json.dumps(config) if isinstance(config, (dict, list)) else str(config)
        )

        # Enhanced pattern matching for Terraform references
        patterns = [
            (r"var\.([a-zA-Z_][a-zA-Z0-9_-]*)", "var.{}"),  # Variables
            (r"([a-zA-Z_][a-zA-Z0-9_-]*\.[a-zA-Z_][a-zA-Z0-9_-]*)", "{}"),  # Resources
            (r"module\.([a-zA-Z_][a-zA-Z0-9_-]*)", "module.{}"),  # Modules
            (
                r"data\.([a-zA-Z_][a-zA-Z0-9_-]*\.[a-zA-Z_][a-zA-Z0-9_-]*)",
                "data.{}",
            ),  # Data sources
            (r"local\.([a-zA-Z_][a-zA-Z0-9_-]*)", "local.{}"),  # Local values
        ]

        for pattern, template in patterns:
            matches = re.findall(pattern, config_str)
            dependencies.extend([template.format(match) for match in matches])

        return list(set(dependencies))

    def _build_dependency_graph(self):
        """Build comprehensive dependency graph"""
        all_objects = {}
        all_objects.update(self.project.resources)
        all_objects.update(self.project.data_sources)
        all_objects.update(self.project.modules)
        all_objects.update(self.project.outputs)
        all_objects.update(self.project.locals)

        for obj_name, obj in all_objects.items():
            self._dependency_graph[obj_name] = {
                "object": obj,
                "dependencies": obj.dependencies,
                "dependents": [],
            }

        # Build reverse dependency graph (dependents)
        for obj_name, obj_info in self._dependency_graph.items():
            for dep in obj_info["dependencies"]:
                if dep in self._dependency_graph:
                    self._dependency_graph[dep]["dependents"].append(obj_name)

        # Store in project for easy access
        self.project.dependency_graph = self._dependency_graph

    def _analyze_project_structure(self, project_path: Path):
        """Analyze project structure and metadata"""
        self.project.metadata = {
            "total_files": len(self._file_line_cache),
            "total_resources": len(self.project.resources),
            "total_data_sources": len(self.project.data_sources),
            "total_modules": len(self.project.modules),
            "total_variables": len(self.project.variables),
            "total_outputs": len(self.project.outputs),
            "project_path": str(project_path),
            "analysis_timestamp": str(os.path.getmtime(project_path)),
        }

        providers = set()
        for resource in self.project.resources.values():
            if hasattr(resource, "provider") and resource.provider:
                providers.add(resource.provider)

        self.project.metadata["providers_used"] = list(providers)

    def get_dependents(self, object_name: str) -> List[str]:
        """Get all objects that depend on the specified object"""
        if object_name in self._dependency_graph:
            return self._dependency_graph[object_name]["dependents"]
        return []

    def get_dependency_chain(self, object_name: str) -> List[List[str]]:
        """Get the complete dependency chain for an object"""
        if object_name not in self._dependency_graph:
            return []

        visited = set()
        chains = []

        def _build_chain(current: str, chain: List[str]):
            if current in visited:
                return
            visited.add(current)

            chain.append(current)
            chains.append(chain.copy())

            for dep in self._dependency_graph[current]["dependencies"]:
                if dep in self._dependency_graph:
                    _build_chain(dep, chain.copy())

        _build_chain(object_name, [])
        return chains

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the project"""
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

            if node in self._dependency_graph:
                for dep in self._dependency_graph[node]["dependencies"]:
                    if dep in self._dependency_graph:
                        _visit(dep)

            path.remove(node)

        for node in self._dependency_graph:
            if node not in visited:
                _visit(node)

        return circular
