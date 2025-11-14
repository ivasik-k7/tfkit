from typing import Dict, Optional, Set, Tuple

from tfkit.dependency.models import (
    DependencyType,
    ObjectDependencies,
    TerraformDependency,
)
from tfkit.graph.models import (
    GraphData,
    Link,
    LinkType,
    Node,
    NodeData,
    NodeState,
    NodeType,
)
from tfkit.parser.models import (
    BaseTerraformObject,
    TerraformCatalog,
    TerraformDataSource,
    TerraformLocal,
    TerraformModule,
    TerraformMoved,
    TerraformObjectType,
    TerraformOutput,
    TerraformProvider,
    TerraformResource,
    TerraformRootConfig,
    TerraformVariable,
)


class TerraformGraphBuilder:
    DEPENDENCY_TYPE_TO_LINK_TYPE: Dict[DependencyType, LinkType] = {
        DependencyType.DIRECT: LinkType.DIRECT,
        DependencyType.IMPLICIT: LinkType.IMPLICIT,
        DependencyType.EXPLICIT: LinkType.EXPLICIT,
        DependencyType.PROVIDER: LinkType.PROVIDER_RELATIONSHIP,
        DependencyType.PROVIDER_CONFIG: LinkType.PROVIDER_CONFIG,
        DependencyType.MODULE: LinkType.MODULE_CALL,
        DependencyType.CONFIGURATION: LinkType.CONFIGURATION,
        DependencyType.OUTPUT: LinkType.EXPORT,
        DependencyType.DATA_REFERENCE: LinkType.DATA_REFERENCE,
        DependencyType.TERRAFORM_BLOCK: LinkType.CONFIGURATION,
        DependencyType.MOVED: LinkType.LIFECYCLE,
    }

    OBJECT_TYPE_TO_NODE_TYPE: Dict[TerraformObjectType, NodeType] = {
        TerraformObjectType.RESOURCE: NodeType.RESOURCE,
        TerraformObjectType.DATA_SOURCE: NodeType.DATA,
        TerraformObjectType.MODULE: NodeType.MODULE,
        TerraformObjectType.VARIABLE: NodeType.VARIABLE,
        TerraformObjectType.OUTPUT: NodeType.OUTPUT,
        TerraformObjectType.PROVIDER: NodeType.PROVIDER,
        TerraformObjectType.LOCAL: NodeType.LOCAL,
        TerraformObjectType.TERRAFORM_BLOCK: NodeType.TERRAFORM,
        TerraformObjectType.MOVED: NodeType.RESOURCE,
    }

    def __init__(self, catalog: TerraformCatalog):
        self.catalog = catalog
        self.graph_data = GraphData()

    def build_graph(self, dependency_map: Dict[str, ObjectDependencies]) -> GraphData:
        self._create_nodes(dependency_map)
        self._create_links(dependency_map)
        self._calculate_connectivity_metrics()
        self._determine_node_states()
        self._assign_visibility()
        self._assign_groups()

        return self.graph_data

    def _create_nodes(self, dependency_map: Dict[str, ObjectDependencies]) -> None:
        for address, obj_deps in dependency_map.items():
            tf_obj = self.catalog.get_by_address(address)

            if tf_obj is None and not self._is_synthetic_node(address):
                continue

            node = self._build_node(address, tf_obj, obj_deps)
            if node:
                self.graph_data.add_node(node)

    def _build_node(
        self,
        address: str,
        tf_obj: Optional[BaseTerraformObject],
        obj_deps: ObjectDependencies,
    ) -> Optional[Node]:
        node_type = self._determine_node_type(address, tf_obj)
        node_data = self._build_node_data(address, tf_obj, obj_deps)
        name = self._generate_node_name(address, tf_obj, node_type)
        weight = self._calculate_base_weight(node_type, obj_deps)

        return Node(
            id=address,
            name=name,
            type=node_type,
            data=node_data,
            weight=weight,
            visibility=True,
        )

    def _build_node_data(
        self,
        address: str,
        tf_obj: Optional[BaseTerraformObject],
        obj_deps: ObjectDependencies,
    ) -> NodeData:
        node_data = NodeData(
            dependency_count=len(obj_deps.depends_on),
            reference_count=len(obj_deps.referenced_by),
            state=NodeState.UNKNOWN,
        )

        if tf_obj is None:
            return self._populate_synthetic_node_data(address, node_data)

        self._populate_source_info(node_data, tf_obj)
        self._populate_meta_arguments(node_data, tf_obj)
        self._populate_type_specific_data(node_data, tf_obj, address)

        return node_data

    def _populate_source_info(
        self, node_data: NodeData, tf_obj: BaseTerraformObject
    ) -> None:
        if hasattr(tf_obj, "source_location") and tf_obj.source_location:
            node_data.source_file = str(tf_obj.source_location.file_path)
            node_data.line_number = tf_obj.source_location.start_line

    def _populate_meta_arguments(
        self, node_data: NodeData, tf_obj: BaseTerraformObject
    ) -> None:
        if hasattr(tf_obj, "depends_on"):
            deps = getattr(tf_obj, "depends_on", [])
            node_data.depends_on = deps if isinstance(deps, list) else []

        if hasattr(tf_obj, "count"):
            node_data.count = getattr(tf_obj, "count", None)

        if hasattr(tf_obj, "for_each"):
            node_data.for_each = getattr(tf_obj, "for_each", None)

        if hasattr(tf_obj, "lifecycle"):
            node_data.lifecycle_rules = getattr(tf_obj, "lifecycle", None)

    def _populate_type_specific_data(
        self, node_data: NodeData, tf_obj: BaseTerraformObject, address: str
    ) -> None:
        if isinstance(tf_obj, TerraformResource):
            self._populate_resource_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformDataSource):
            self._populate_data_source_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformModule):
            self._populate_module_data(node_data, tf_obj, address)
        elif isinstance(tf_obj, TerraformVariable):
            self._populate_variable_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformLocal):
            self._populate_local_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformOutput):
            self._populate_output_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformProvider):
            self._populate_provider_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformRootConfig):
            self._populate_terraform_block_data(node_data, tf_obj)
        elif isinstance(tf_obj, TerraformMoved):
            self._populate_moved_block_data(node_data, tf_obj)

    def _populate_resource_data(
        self, node_data: NodeData, resource: TerraformResource
    ) -> None:
        node_data.resource_type = resource.resource_type
        node_data.provider = resource.provider

        if hasattr(resource, "attributes") and isinstance(resource.attributes, dict):
            tags = resource.attributes.get("tags", {})
            if isinstance(tags, dict):
                node_data.tags = tags

            node_data.attributes.update(resource.attributes)

    def _populate_data_source_data(
        self, node_data: NodeData, data_source: TerraformDataSource
    ) -> None:
        node_data.resource_type = data_source.data_type
        node_data.provider = data_source.provider

        if hasattr(data_source, "attributes") and isinstance(
            data_source.attributes, dict
        ):
            node_data.attributes.update(data_source.attributes)

    def _populate_module_data(
        self, node_data: NodeData, module: TerraformModule, address: str
    ) -> None:
        address_parts = address.split(".")
        if address_parts[0] == "module":
            node_data.module_path = address_parts[1:]

        node_data.attributes["module_source"] = module.source
        node_data.attributes["module_version"] = module.version
        node_data.attributes["source_type"] = module.source_type.value

        if module.namespace:
            node_data.attributes["namespace"] = module.namespace
        if module.provider_name:
            node_data.provider = module.provider_name
        if module.module_name:
            node_data.attributes["module_name"] = module.module_name

        if module.providers:
            node_data.attributes["provider_mappings"] = module.providers

    def _populate_variable_data(
        self, node_data: NodeData, variable: TerraformVariable
    ) -> None:
        node_data.attributes["variable_type"] = variable.variable_type
        node_data.attributes["default"] = variable.default
        node_data.attributes["description"] = variable.description
        node_data.attributes["sensitive"] = variable.sensitive
        node_data.attributes["nullable"] = variable.nullable

        if variable.validation:
            node_data.attributes["validation_rules"] = variable.validation

    def _populate_local_data(self, node_data: NodeData, local: TerraformLocal) -> None:
        node_data.attributes["value"] = local.value

    def _populate_output_data(
        self, node_data: NodeData, output: TerraformOutput
    ) -> None:
        node_data.attributes["value"] = output.value
        node_data.attributes["description"] = output.description
        node_data.attributes["sensitive"] = output.sensitive

    def _populate_provider_data(
        self, node_data: NodeData, provider: TerraformProvider
    ) -> None:
        node_data.provider = getattr(provider, "provider_name", None)
        node_data.attributes["provider_alias"] = provider.alias
        node_data.attributes["provider_version"] = provider.version

        if hasattr(provider, "attributes") and isinstance(provider.attributes, dict):
            for key, value in provider.attributes.items():
                if key not in node_data.attributes:
                    node_data.attributes[key] = value

    def _populate_terraform_block_data(
        self, node_data: NodeData, terraform_block: TerraformRootConfig
    ) -> None:
        node_data.attributes["required_version"] = terraform_block.required_version
        node_data.attributes["required_providers"] = terraform_block.required_providers

        if terraform_block.backend:
            node_data.attributes["backend"] = terraform_block.backend
        if terraform_block.cloud:
            node_data.attributes["cloud"] = terraform_block.cloud
        if terraform_block.experiments:
            node_data.attributes["experiments"] = terraform_block.experiments

    def _populate_moved_block_data(
        self, node_data: NodeData, moved: TerraformMoved
    ) -> None:
        node_data.attributes["from_address"] = moved.from_address
        node_data.attributes["to_address"] = moved.to_address

    def _populate_synthetic_node_data(
        self, address: str, node_data: NodeData
    ) -> NodeData:
        if address == "terraform":
            node_data.state = NodeState.CONFIGURATION
        elif address.startswith("provider."):
            node_data.state = NodeState.CONFIG_PROVIDER
            parts = address.split(".")
            if len(parts) >= 2:
                node_data.provider = parts[1]
        else:
            node_data.state = NodeState.EXTERNAL

        return node_data

    def _determine_node_type(
        self, address: str, tf_obj: Optional[BaseTerraformObject]
    ) -> NodeType:
        if address == "terraform":
            return NodeType.TERRAFORM

        if tf_obj and hasattr(tf_obj, "object_type"):
            return self.OBJECT_TYPE_TO_NODE_TYPE.get(
                tf_obj.object_type, NodeType.RESOURCE
            )

        parts = address.split(".")
        type_map = {
            "var": NodeType.VARIABLE,
            "local": NodeType.LOCAL,
            "module": NodeType.MODULE,
            "data": NodeType.DATA,
            "output": NodeType.OUTPUT,
            "provider": NodeType.PROVIDER,
        }

        return type_map.get(parts[0], NodeType.RESOURCE)

    def _generate_node_name(
        self, address: str, tf_obj: Optional[BaseTerraformObject], node_type: NodeType
    ) -> str:
        if node_type == NodeType.TERRAFORM:
            return "terraform"

        if node_type == NodeType.PROVIDER:
            return address

        parts = address.split(".")

        if node_type in {NodeType.RESOURCE, NodeType.DATA}:
            if len(parts) >= 2:
                return f"{parts[-2]}.{parts[-1]}"

        return parts[-1] if parts else address

    def _calculate_base_weight(
        self, node_type: NodeType, obj_deps: ObjectDependencies
    ) -> float:
        type_weights = {
            NodeType.TERRAFORM: 2.0,
            NodeType.PROVIDER: 1.8,
            NodeType.MODULE: 1.5,
            NodeType.RESOURCE: 1.0,
            NodeType.DATA: 0.9,
            NodeType.VARIABLE: 0.7,
            NodeType.LOCAL: 0.6,
            NodeType.OUTPUT: 0.5,
        }

        base_weight = type_weights.get(node_type, 1.0)
        connectivity = (len(obj_deps.depends_on) + len(obj_deps.referenced_by)) * 0.1

        return min(base_weight + connectivity, 5.0)

    def _is_synthetic_node(self, address: str) -> bool:
        return address == "terraform" or address.startswith("provider.")

    def _create_links(self, dependency_map: Dict[str, ObjectDependencies]) -> None:
        seen_links: Set[Tuple[str, str, DependencyType]] = set()

        for address, obj_deps in dependency_map.items():
            for dep in obj_deps.depends_on:
                link_signature = (
                    dep.source_address,
                    dep.target_address,
                    dep.dependency_type,
                )

                if link_signature in seen_links:
                    continue

                if not self._both_nodes_exist(dep.source_address, dep.target_address):
                    continue

                link = self._build_link(dep)
                if link:
                    self.graph_data.add_link(link)
                    seen_links.add(link_signature)

    def _build_link(self, dep: TerraformDependency) -> Optional[Link]:
        link_type = self.DEPENDENCY_TYPE_TO_LINK_TYPE.get(
            dep.dependency_type, LinkType.IMPLICIT
        )

        strength = dep.calculate_strength()
        ref_path = dep.attribute_path.split(".") if dep.attribute_path else None

        return Link(
            source=dep.source_address,
            target=dep.target_address,
            link_type=link_type,
            strength=strength,
            reference_path=ref_path,
        )

    def _both_nodes_exist(self, source: str, target: str) -> bool:
        return source in self.graph_data.nodes and target in self.graph_data.nodes

    def _calculate_connectivity_metrics(self) -> None:
        for node in self.graph_data.nodes.values():
            links = self.graph_data.get_node_links(node.id)

            incoming = [link for link in links if link.target == node.id]
            outgoing = [link for link in links if link.source == node.id]

            node.data.dependency_count = len(outgoing)
            node.data.reference_count = len(incoming)

    def _determine_node_states(self) -> None:
        self._detect_hub_nodes()
        self._detect_bridge_nodes()
        self._detect_leaf_nodes()
        self._detect_orphan_nodes()
        self._assign_default_states()

    def _detect_hub_nodes(self) -> None:
        hub_threshold = 5

        for node in self.graph_data.nodes.values():
            if node.data.reference_count >= hub_threshold:
                node.data.state = NodeState.HUB

    def _detect_bridge_nodes(self) -> None:
        for node in self.graph_data.nodes.values():
            if node.data.state != NodeState.UNKNOWN:
                continue

            if self._is_bridge_node(node.id):
                node.data.state = NodeState.BRIDGE

    def _is_bridge_node(self, node_id: str) -> bool:
        links = self.graph_data.get_node_links(node_id)

        incoming_sources = {link.source for link in links if link.target == node_id}
        outgoing_targets = {link.target for link in links if link.source == node_id}

        has_multiple_inputs = len(incoming_sources) >= 2
        has_multiple_outputs = len(outgoing_targets) >= 2
        no_overlap = not incoming_sources.intersection(outgoing_targets)

        return has_multiple_inputs and has_multiple_outputs and no_overlap

    def _detect_leaf_nodes(self) -> None:
        for node in self.graph_data.nodes.values():
            if node.data.state != NodeState.UNKNOWN:
                continue

            is_leaf = node.data.reference_count == 0 and node.data.dependency_count > 0

            if is_leaf:
                node.data.state = NodeState.LEAF

    def _detect_orphan_nodes(self) -> None:
        for node in self.graph_data.nodes.values():
            if node.data.state != NodeState.UNKNOWN:
                continue

            is_isolated = (
                node.data.dependency_count == 0 and node.data.reference_count == 0
            )

            if is_isolated and node.type not in {NodeType.TERRAFORM, NodeType.PROVIDER}:
                node.data.state = NodeState.ORPHAN

    def _assign_default_states(self) -> None:
        for node in self.graph_data.nodes.values():
            if node.data.state != NodeState.UNKNOWN:
                continue

            if node.type == NodeType.TERRAFORM:
                node.data.state = NodeState.CONFIGURATION
            elif node.type == NodeType.PROVIDER:
                node.data.state = NodeState.CONFIG_PROVIDER
            elif node.type == NodeType.VARIABLE:
                node.data.state = NodeState.CONFIG_PROVIDER
            elif node.type == NodeType.LOCAL:
                node.data.state = NodeState.CONFIG_PROVIDER
            elif node.type == NodeType.OUTPUT:
                node.data.state = NodeState.CONFIG_CONSUMER
            elif node.type == NodeType.MODULE:
                node.data.state = NodeState.AGGREGATOR
            elif node.data.reference_count > 0 and node.data.dependency_count > 0:
                node.data.state = NodeState.ACTIVE
            elif node.data.dependency_count == 0 and node.data.reference_count > 0:
                node.data.state = NodeState.HUB
            elif node.data.reference_count == 0 and node.data.dependency_count > 0:
                node.data.state = NodeState.LEAF
            else:
                node.data.state = NodeState.ORPHAN

    def _assign_visibility(self) -> None:
        for node in self.graph_data.nodes.values():
            if node.type in {NodeType.TERRAFORM, NodeType.PROVIDER, NodeType.MODULE}:
                node.visibility = True
                continue

            if node.data.state == NodeState.ORPHAN:
                node.visibility = False
                continue

            is_connected = (
                node.data.dependency_count > 0 or node.data.reference_count > 0
            )
            node.visibility = is_connected

    def _assign_groups(self) -> None:
        provider_groups = self._build_provider_groups()
        module_groups = self._build_module_groups()
        type_groups = self._build_type_groups()

        for node in self.graph_data.nodes.values():
            group_parts = []

            if node.id in provider_groups:
                group_parts.append(provider_groups[node.id])

            if node.id in module_groups:
                group_parts.append(module_groups[node.id])

            if node.id in type_groups:
                group_parts.append(type_groups[node.id])

            node.group = ":".join(group_parts) if group_parts else None

    def _build_provider_groups(self) -> Dict[str, str]:
        groups = {}
        for node in self.graph_data.nodes.values():
            if node.data.provider:
                groups[node.id] = f"provider:{node.data.provider}"
        return groups

    def _build_module_groups(self) -> Dict[str, str]:
        groups = {}
        for node in self.graph_data.nodes.values():
            if node.data.module_path:
                module_name = node.data.module_path[0]
                groups[node.id] = f"module:{module_name}"
        return groups

    def _build_type_groups(self) -> Dict[str, str]:
        groups = {}
        for node in self.graph_data.nodes.values():
            groups[node.id] = f"type:{node.type.value}"
        return groups
