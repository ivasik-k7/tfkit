import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from tfkit.dependency.models import (
    DependencyType,
    ObjectDependencies,
    TerraformDependency,
)
from tfkit.parser.models import TerraformCatalog


class TerraformDependencyBuilder:
    INTERPOLATION_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, catalog: "TerraformCatalog"):
        self.catalog = catalog
        self.dependencies: Dict[str, ObjectDependencies] = {}
        self._provider_map: Dict[str, str] = {}
        self._aliased_providers: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._provider_prefixes: Dict[str, List[str]] = defaultdict(list)
        self._terraform_block_address = "terraform"

    def build_dependencies(self) -> Dict[str, ObjectDependencies]:
        self.dependencies = {}

        for address in self.catalog.get_all_addresses():
            self.dependencies[address] = ObjectDependencies(address=address)

        if self._terraform_block_address not in self.dependencies:
            self.dependencies[self._terraform_block_address] = ObjectDependencies(
                address=self._terraform_block_address
            )

        self._build_provider_maps()
        self._detect_provider_prefixes()
        self._build_terraform_block_dependencies()
        self._build_provider_dependencies()

        all_objects = self.catalog.get_all_objects()

        for obj in all_objects:
            source_address = self.catalog._build_address(obj)
            if not source_address:
                continue

            found_deps = self._extract_dependencies(obj, source_address)
            provider_deps = self._extract_provider_dependencies(obj, source_address)
            output_deps = self._extract_output_dependencies(obj, source_address)

            found_deps.extend(provider_deps)
            found_deps.extend(output_deps)

            for dep in found_deps:
                if dep.source_address in self.dependencies:
                    self.dependencies[dep.source_address].add_dependency(dep)

                if dep.target_address in self.dependencies:
                    self.dependencies[dep.target_address].add_reference(dep)

        return self.dependencies

    def _build_provider_maps(self):
        self._provider_map.clear()
        self._aliased_providers.clear()

        for provider in self.catalog.providers:
            provider_name = getattr(provider, "name", None)
            alias = getattr(provider, "alias", None)

            if not provider_name:
                continue

            if alias:
                address = f"provider.{provider_name}.{alias}"
                self._aliased_providers[provider_name][alias] = address
            else:
                address = f"{provider_name}"
                self._provider_map[provider_name] = address

    def _detect_provider_prefixes(self):
        self._provider_prefixes.clear()
        resource_types = set()

        for resource in self.catalog.resources:
            resource_type = getattr(resource, "resource_type", None)
            if resource_type:
                resource_types.add(resource_type)

        for data_source in self.catalog.data_sources:
            data_type = getattr(data_source, "data_type", None)
            if data_type:
                resource_types.add(data_type)

        prefix_counts = defaultdict(int)
        for resource_type in resource_types:
            parts = resource_type.split("_", 1)
            if len(parts) > 1:
                prefix = parts[0]
                prefix_counts[prefix] += 1

        for prefix, _ in prefix_counts.items():
            if prefix in self._provider_map or prefix in self._aliased_providers:
                self._provider_prefixes[prefix].append(f"{prefix}_")

    def _build_terraform_block_dependencies(self):
        terraform_blocks = [
            obj
            for obj in self.catalog.get_all_objects()
            if getattr(obj, "object_type", None)
            and obj.object_type.value == "terraform"
        ]

        for _provider_name, provider_address in self._provider_map.items():
            dep = TerraformDependency(
                source_address=self._terraform_block_address,
                target_address=provider_address,
                dependency_type=DependencyType.TERRAFORM_BLOCK,
                attribute_path="required_providers",
            )
            self.dependencies[self._terraform_block_address].add_dependency(dep)
            if provider_address in self.dependencies:
                self.dependencies[provider_address].add_reference(dep)

        for provider_name, aliases in self._aliased_providers.items():
            for alias, provider_address in aliases.items():
                dep = TerraformDependency(
                    source_address=self._terraform_block_address,
                    target_address=provider_address,
                    dependency_type=DependencyType.TERRAFORM_BLOCK,
                    attribute_path=f"required_providers.{provider_name}.{alias}",
                )
                self.dependencies[self._terraform_block_address].add_dependency(dep)
                if provider_address in self.dependencies:
                    self.dependencies[provider_address].add_reference(dep)

        for terraform_block in terraform_blocks:
            if hasattr(terraform_block, "attributes") and terraform_block.attributes:
                deps = self._extract_from_dict(
                    terraform_block.attributes,
                    self._terraform_block_address,
                    "terraform",
                )
                for dep in deps:
                    self.dependencies[self._terraform_block_address].add_dependency(dep)
                    if dep.target_address in self.dependencies:
                        self.dependencies[dep.target_address].add_reference(dep)

    def _build_provider_dependencies(self):
        for provider in self.catalog.providers:
            provider_name = getattr(provider, "name", None)
            alias = getattr(provider, "alias", None)

            if not provider_name:
                continue

            if alias:
                provider_address = f"provider.{provider_name}.{alias}"
            else:
                provider_address = f"provider.{provider_name}"

            if provider_address not in self.dependencies:
                continue

            if hasattr(provider, "attributes") and provider.attributes:
                deps = self._extract_from_dict(
                    provider.attributes, provider_address, "provider_config"
                )

                for dep in deps:
                    enhanced_dep = TerraformDependency(
                        source_address=dep.source_address,
                        target_address=dep.target_address,
                        dependency_type=DependencyType.PROVIDER_CONFIG,
                        attribute_path=dep.attribute_path,
                    )
                    self.dependencies[provider_address].add_dependency(enhanced_dep)
                    if dep.target_address in self.dependencies:
                        self.dependencies[dep.target_address].add_reference(
                            enhanced_dep
                        )

            if hasattr(provider, "raw_code") and provider.raw_code:
                deps = self._extract_from_string(
                    provider.raw_code, provider_address, "raw_code"
                )
                for dep in deps:
                    enhanced_dep = TerraformDependency(
                        source_address=dep.source_address,
                        target_address=dep.target_address,
                        dependency_type=DependencyType.PROVIDER_CONFIG,
                        attribute_path=dep.attribute_path,
                    )
                    self.dependencies[provider_address].add_dependency(enhanced_dep)
                    if dep.target_address in self.dependencies:
                        self.dependencies[dep.target_address].add_reference(
                            enhanced_dep
                        )

    def _get_provider_type_from_resource(self, resource_type: str) -> Optional[str]:
        for provider_type, prefixes in self._provider_prefixes.items():
            for prefix in prefixes:
                if resource_type.startswith(prefix):
                    return provider_type

        parts = resource_type.split("_", 1)
        if len(parts) > 1:
            potential_provider = parts[0]
            if (
                potential_provider in self._provider_map
                or potential_provider in self._aliased_providers
            ):
                return potential_provider

        return None

    def _resolve_provider_reference(self, provider_ref: str) -> Optional[str]:
        if not provider_ref:
            return None

        provider_ref = provider_ref.strip()
        provider_ref = re.sub(r"^\$\{|}$", "", provider_ref)

        parts = provider_ref.split(".")

        if len(parts) >= 2 and parts[0] == "provider":
            if len(parts) == 3:
                provider_type, alias = parts[1], parts[2]
                if (
                    provider_type in self._aliased_providers
                    and alias in self._aliased_providers[provider_type]
                ):
                    return self._aliased_providers[provider_type][alias]
            elif len(parts) == 2:
                provider_type = parts[1]
                if provider_type in self._provider_map:
                    return self._provider_map[provider_type]

        if len(parts) == 2:
            provider_type, alias = parts
            if (
                provider_type in self._aliased_providers
                and alias in self._aliased_providers[provider_type]
            ):
                return self._aliased_providers[provider_type][alias]
        elif len(parts) == 1:
            if provider_ref in self._provider_map:
                return self._provider_map[provider_ref]

        for address in self.dependencies.keys():
            if address.endswith(f".{provider_ref}") or address == provider_ref:
                return address

        return None

    def _extract_provider_dependencies(
        self, obj: Any, source_address: str
    ) -> List[TerraformDependency]:
        dependencies = []

        obj_type = getattr(obj, "object_type", None)
        if not obj_type or obj_type.value not in ("resource", "data"):
            return dependencies

        resource_type = getattr(obj, "resource_type", None) or getattr(
            obj, "data_type", None
        )

        if not resource_type:
            return dependencies

        explicit_provider = getattr(obj, "provider", None)

        if explicit_provider:
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
            provider_type = self._get_provider_type_from_resource(resource_type)

            if provider_type and provider_type in self._provider_map:
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

    def _extract_output_dependencies(
        self, obj: Any, source_address: str
    ) -> List[TerraformDependency]:
        dependencies = []

        obj_type = getattr(obj, "object_type", None)
        if not obj_type or obj_type.value != "output":
            return dependencies

        if hasattr(obj, "value") and obj.value:
            value = obj.value
            if isinstance(value, str):
                deps = self._extract_from_string(value, source_address, "value")
                for dep in deps:
                    output_dep = TerraformDependency(
                        source_address=dep.source_address,
                        target_address=dep.target_address,
                        dependency_type=DependencyType.OUTPUT,
                        attribute_path=dep.attribute_path,
                    )
                    dependencies.append(output_dep)
            elif isinstance(value, dict):
                deps = self._extract_from_dict(value, source_address, "value")
                for dep in deps:
                    output_dep = TerraformDependency(
                        source_address=dep.source_address,
                        target_address=dep.target_address,
                        dependency_type=DependencyType.OUTPUT,
                        attribute_path=dep.attribute_path,
                    )
                    dependencies.append(output_dep)

        return dependencies

    def _extract_dependencies(
        self, obj: Any, source_address: str
    ) -> List[TerraformDependency]:
        dependencies = []

        if hasattr(obj, "attributes") and obj.attributes:
            filtered_attrs = {
                k: v for k, v in obj.attributes.items() if k != "provider"
            }
            if filtered_attrs:
                deps = self._extract_from_dict(
                    filtered_attrs, source_address, "attributes"
                )
                dependencies.extend(deps)

        if hasattr(obj, "raw_code") and obj.raw_code:
            deps = self._extract_from_string(obj.raw_code, source_address, "raw_code")
            dependencies.extend(deps)

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
                                    dependency_type=DependencyType.EXPLICIT,
                                    attribute_path="depends_on",
                                )
                            )

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

        if hasattr(obj, "source") and obj.source:
            source_value = getattr(obj, "source")  # noqa
            if isinstance(source_value, str):
                deps = self._extract_from_string(source_value, source_address, "source")
                dependencies.extend(deps)

        if hasattr(obj, "lifecycle") and obj.lifecycle:
            lifecycle = getattr(obj, "lifecycle")  # noqa
            if isinstance(lifecycle, dict):
                deps = self._extract_from_dict(lifecycle, source_address, "lifecycle")
                dependencies.extend(deps)

        if hasattr(obj, "provisioners") and obj.provisioners:
            provisioners = getattr(obj, "provisioners")  # noqa
            if isinstance(provisioners, list):
                for idx, provisioner in enumerate(provisioners):
                    if isinstance(provisioner, dict):
                        deps = self._extract_from_dict(
                            provisioner, source_address, f"provisioner[{idx}]"
                        )
                        dependencies.extend(deps)

        return list(set(dependencies))

    def _extract_from_dict(
        self, data: Dict[str, Any], source_address: str, base_path: str = ""
    ) -> List[TerraformDependency]:
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
        dependencies = []
        references = self._parse_references_from_string(text)

        for ref in references:
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
        references = set()

        interpolations = self.INTERPOLATION_PATTERN.findall(text)
        for interp in interpolations:
            refs = self._parse_terraform_expression(interp)
            references.update(refs)

        refs = self._parse_terraform_expression(text)
        references.update(refs)

        return references

    def _parse_terraform_expression(self, expr: str) -> Set[str]:
        references = set()

        var_matches = re.findall(r"\bvar\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for var_name in var_matches:
            references.add(f"var.{var_name}")

        local_matches = re.findall(r"\blocal\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for local_name in local_matches:
            references.add(f"local.{local_name}")

        module_matches = re.findall(r"\bmodule\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr)
        for module_name in module_matches:
            references.add(f"module.{module_name}")

        data_matches = re.findall(
            r"\bdata\.([a-zA-Z_][a-zA-Z0-9_-]*)\.([a-zA-Z_][a-zA-Z0-9_-]*)", expr
        )
        for data_type, data_name in data_matches:
            references.add(f"data.{data_type}.{data_name}")

        provider_matches = re.findall(
            r"\bprovider\.([a-zA-Z_][a-zA-Z0-9_-]*)(?:\.([a-zA-Z_][a-zA-Z0-9_-]*))?",
            expr,
        )
        for provider_type, alias in provider_matches:
            if alias:
                references.add(f"provider.{provider_type}.{alias}")
            else:
                references.add(f"provider.{provider_type}")

        resource_matches = re.findall(
            r"\b(?!(?:var|local|module|data|provider|terraform|each|count|path|self|for|if|true|false|null)\b)([a-z][a-z0-9_]+)\.([a-zA-Z_][a-zA-Z0-9_-]*)",
            expr,
        )
        for resource_type, resource_name in resource_matches:
            if "_" in resource_type and not resource_type.startswith("_"):
                if resource_type not in {"try", "can", "merge", "concat", "lookup"}:
                    references.add(f"{resource_type}.{resource_name}")

        return references

    def get_dependencies(self, address: str) -> Optional[ObjectDependencies]:
        return self.dependencies.get(address)

    def get_dependency_chain(
        self, address: str, include_implicit: bool = True
    ) -> List[str]:
        visited = set()
        chain = []

        def visit(addr: str):
            if addr in visited:
                return
            visited.add(addr)

            deps = self.dependencies.get(addr)
            if deps:
                for dep in deps.depends_on:
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
        resources = []

        deps = self.dependencies.get(provider_address)
        if deps:
            for dep in deps.referenced_by:
                if dep.dependency_type in (
                    DependencyType.PROVIDER,
                    DependencyType.IMPLICIT,
                ):
                    resources.append(dep.source_address)

        return resources

    def detect_cycles(self, include_implicit: bool = False) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()

        def visit(addr: str, path: List[str]):
            if addr in rec_stack:
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
