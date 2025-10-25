"""Terraform project analyzer."""

import glob
import os
import re
from pathlib import Path
from typing import Dict, List

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
        )

    def analyze_project(self, project_path: str) -> TerraformProject:
        """Analyze Terraform project and build object map"""
        if hcl2 is None:
            raise ImportError(
                "python-hcl2 is required for Terraform analysis. Install with: pip install python-hcl2"
            )

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Find all .tf files
        tf_files = glob.glob(str(project_path / "**" / "*.tf"), recursive=True)

        if not tf_files:
            raise ValueError(f"No .tf files found in {project_path}")

        for tf_file in tf_files:
            self._parse_tf_file(tf_file)

        self._build_dependencies()
        return self.project

    def _parse_tf_file(self, file_path: str):
        """Parse a single Terraform file"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            parsed = hcl2.loads(content)

            # Extract different resource types
            self._extract_resources(parsed.get("resource", []), file_path)
            self._extract_data_sources(parsed.get("data", []), file_path)
            self._extract_modules(parsed.get("module", []), file_path)
            self._extract_variables(parsed.get("variable", []), file_path)
            self._extract_outputs(parsed.get("output", []), file_path)
            self._extract_providers(parsed.get("provider", []), file_path)
            self._extract_terraform_block(parsed.get("terraform", []), file_path)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

    def _extract_resources(self, resources: List, file_path: str):
        """Extract resources from parsed HCL"""
        for resource_block in resources:
            for resource_type, resource_instances in resource_block.items():
                for instance_name, config in resource_instances.items():
                    full_name = f"{resource_type}.{instance_name}"
                    self.project.resources[full_name] = TerraformObject(
                        type=ResourceType.RESOURCE,
                        name=instance_name,
                        full_name=full_name,
                        attributes=config or {},
                        dependencies=self._find_dependencies(config),
                        file_path=file_path,
                        line_number=1,  # Simplified - could be enhanced with exact line numbers
                    )

    def _extract_data_sources(self, data_sources: List, file_path: str):
        """Extract data sources from parsed HCL"""
        for data_block in data_sources:
            for data_type, data_instances in data_block.items():
                for instance_name, config in data_instances.items():
                    full_name = f"data.{data_type}.{instance_name}"
                    self.project.data_sources[full_name] = TerraformObject(
                        type=ResourceType.DATA,
                        name=instance_name,
                        full_name=full_name,
                        attributes=config or {},
                        dependencies=self._find_dependencies(config),
                        file_path=file_path,
                        line_number=1,
                    )

    def _extract_modules(self, modules: List, file_path: str):
        """Extract modules from parsed HCL"""
        for module_block in modules:
            for module_name, config in module_block.items():
                full_name = f"module.{module_name}"
                self.project.modules[full_name] = TerraformObject(
                    type=ResourceType.MODULE,
                    name=module_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=self._find_dependencies(config),
                    file_path=file_path,
                    line_number=1,
                )

    def _extract_variables(self, variables: List, file_path: str):
        """Extract variables from parsed HCL"""
        for var_block in variables:
            for var_name, config in var_block.items():
                full_name = f"var.{var_name}"
                self.project.variables[full_name] = TerraformObject(
                    type=ResourceType.VARIABLE,
                    name=var_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=[],
                    file_path=file_path,
                    line_number=1,
                )

    def _extract_outputs(self, outputs: List, file_path: str):
        """Extract outputs from parsed HCL"""
        for output_block in outputs:
            for output_name, config in output_block.items():
                full_name = f"output.{output_name}"
                self.project.outputs[full_name] = TerraformObject(
                    type=ResourceType.OUTPUT,
                    name=output_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=self._find_dependencies(config),
                    file_path=file_path,
                    line_number=1,
                )

    def _extract_providers(self, providers: List, file_path: str):
        """Extract providers from parsed HCL"""
        for provider_block in providers:
            for provider_name, config in provider_block.items():
                full_name = f"provider.{provider_name}"
                self.project.providers[full_name] = TerraformObject(
                    type=ResourceType.PROVIDER,
                    name=provider_name,
                    full_name=full_name,
                    attributes=config or {},
                    dependencies=[],
                    file_path=file_path,
                    line_number=1,
                )

    def _extract_terraform_block(self, terraform_blocks: List, file_path: str):
        """Extract terraform configuration blocks"""
        for terraform_block in terraform_blocks:
            full_name = "terraform.config"
            self.project.providers[full_name] = TerraformObject(
                type=ResourceType.TERRAFORM,
                name="config",
                full_name=full_name,
                attributes=terraform_block or {},
                dependencies=[],
                file_path=file_path,
                line_number=1,
            )

    def _find_dependencies(self, config: Dict) -> List[str]:
        """Find dependencies in configuration"""
        if not config:
            return []

        dependencies = []
        config_str = str(config)

        # Look for variable references
        if "var." in config_str:
            var_refs = re.findall(r"var\.([a-zA-Z_][a-zA-Z0-9_-]*)", config_str)
            dependencies.extend([f"var.{var}" for var in var_refs])

        # Look for resource references
        resource_refs = re.findall(
            r"([a-zA-Z_][a-zA-Z0-9_-]*\.[a-zA-Z_][a-zA-Z0-9_-]*)", config_str
        )
        dependencies.extend(resource_refs)

        # Look for module outputs
        module_refs = re.findall(r"module\.([a-zA-Z_][a-zA-Z0-9_-]*)", config_str)
        dependencies.extend([f"module.{module}" for module in module_refs])

        return list(set(dependencies))

    def _build_dependencies(self):
        """Build dependency relationships between objects"""
        # This can be enhanced to build a proper dependency graph
        pass
