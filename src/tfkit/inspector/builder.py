from typing import Any, Dict, Optional, Set

from tfkit.inspector.graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeStatus,
    NodeType,
    TerraformGraph,
)
from tfkit.inspector.models import (
    AttributeType,
    AttributeValue,
    TerraformAttribute,
    TerraformBlock,
    TerraformModule,
    TerraformObjectType,
)


class TerraformGraphBuilder:
    """Service that builds graph structures from TerraformModule."""

    def __init__(self):
        self._node_cache: Dict[str, GraphNode] = {}

    def build_graph(self, module: TerraformModule) -> TerraformGraph:
        """
        Build a comprehensive graph from a Terraform module.

        Args:
            module: The TerraformModule to build graph from

        Returns:
            TerraformGraph with all nodes and relationships
        """
        graph = TerraformGraph()

        # Process all blocks and create nodes
        self._process_blocks(module, graph)

        # Build relationships
        self._build_dependency_relationships(module, graph)
        self._build_reference_relationships(module, graph)
        self._build_provider_relationships(module, graph)
        self._build_module_relationships(module, graph)

        # Calculate graph metrics
        self._calculate_graph_metrics(graph)

        return graph

    def _create_root_node(self, module: TerraformModule) -> GraphNode:
        """Create root node for the module."""
        return GraphNode(
            id="root",
            node_type=NodeType.ROOT,
            label=f"Module: {module.root_path}",
            data={"root_path": module.root_path},
            metadata={
                "file_count": len(module.files),
                "total_blocks": sum(len(file.blocks) for file in module.files),
            },
        )

    def _process_blocks(self, module: TerraformModule, graph: TerraformGraph):
        """Process all blocks and create corresponding nodes."""

        # Process resources
        for resource_addr, resource_block in module._global_resource_index.items():
            node = self._create_resource_node(resource_block, resource_addr)
            graph.add_node(node)

            # Connect to root
            graph.add_edge(
                GraphEdge(
                    source_id="root",
                    target_id=resource_addr,
                    edge_type=EdgeType.CONTAINS,
                )
            )

        # Process data sources
        for data_addr, data_block in module._global_resource_index.items():
            if data_addr.startswith("data."):
                node = self._create_data_source_node(data_block, data_addr)
                graph.add_node(node)

                graph.add_edge(
                    GraphEdge(
                        source_id="root",
                        target_id=data_addr,
                        edge_type=EdgeType.CONTAINS,
                    )
                )

        # Process modules
        for module_addr, module_block in module._global_module_index.items():
            node = self._create_module_node(module_block, module_addr)
            graph.add_node(node)

            graph.add_edge(
                GraphEdge(
                    source_id="root", target_id=module_addr, edge_type=EdgeType.CONTAINS
                )
            )

        # Process variables
        for var_addr, var_block in module._global_variable_index.items():
            node = self._create_variable_node(var_block, var_addr)
            graph.add_node(node)

        # Process outputs
        for output_addr, output_block in module._global_output_index.items():
            node = self._create_output_node(output_block, output_addr)
            graph.add_node(node)

            graph.add_edge(
                GraphEdge(
                    source_id="root", target_id=output_addr, edge_type=EdgeType.OUTPUTS
                )
            )

        # Process locals
        for local_addr, local_block in module._global_local_index.items():
            node = self._create_local_node(local_block, local_addr)
            graph.add_node(node)

        # Process providers
        for provider_addr, provider_block in module._global_provider_index.items():
            node = self._create_provider_node(provider_block, provider_addr)
            graph.add_node(node)

        # Process terraform block
        terraform_blocks = list(module._global_terraform_index.values())
        if terraform_blocks:
            terraform_block = terraform_blocks[0]
            node = self._create_terraform_node(terraform_block)
            graph.add_node(node)

    def _create_resource_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for a resource block."""
        complexity = self._calculate_block_complexity(block)

        return GraphNode(
            id=address,
            node_type=NodeType.RESOURCE,
            label=f"Resource: {block.resource_type}.{block.name}",
            data=block.to_dict(),
            metadata={
                "resource_type": block.resource_type,
                "provider": self._extract_provider_from_type(block.resource_type),
                "dependencies": list(block.dependencies),
                "attribute_count": len(block.attributes),
            },
            complexity=complexity,
        )

    def _create_data_source_node(
        self, block: TerraformBlock, address: str
    ) -> GraphNode:
        """Create a node for a data source block."""
        complexity = self._calculate_block_complexity(block)

        return GraphNode(
            id=address,
            node_type=NodeType.DATA_SOURCE,
            label=f"Data: {block.resource_type}.{block.name}",
            data=block.to_dict(),
            metadata={
                "data_type": block.resource_type,
                "provider": self._extract_provider_from_type(block.resource_type),
                "dependencies": list(block.dependencies),
                "attribute_count": len(block.attributes),
            },
            complexity=complexity,
        )

    def _create_module_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for a module block."""
        complexity = self._calculate_block_complexity(block)

        return GraphNode(
            id=address,
            node_type=NodeType.MODULE,
            label=f"Module: {block.name}",
            data=block.to_dict(),
            metadata={
                "source": block.attributes.get(
                    "source",
                    TerraformAttribute(
                        name="source",
                        value=AttributeValue("unknown", AttributeType.STRING),
                    ),
                ).value.raw_value,
                "dependencies": list(block.dependencies),
                "input_count": len(
                    [
                        attr
                        for attr in block.attributes.keys()
                        if attr not in ["source", "version"]
                    ]
                ),
            },
            complexity=complexity,
        )

    def _create_variable_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for a variable block."""
        return GraphNode(
            id=address,
            node_type=NodeType.VARIABLE,
            label=f"Variable: {block.name}",
            data=block.to_dict(),
            metadata={
                "type": block.attributes.get(
                    "type",
                    TerraformAttribute(
                        name="type", value=AttributeValue("any", AttributeType.STRING)
                    ),
                ).value.raw_value,
                "has_default": "default" in block.attributes,
                "is_sensitive": block.attributes.get(
                    "sensitive",
                    TerraformAttribute(
                        name="sensitive",
                        value=AttributeValue(False, AttributeType.BOOL),
                    ),
                ).value.raw_value,
            },
            complexity=2,  # Variables are simple
        )

    def _create_output_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for an output block."""
        complexity = self._calculate_block_complexity(block)

        return GraphNode(
            id=address,
            node_type=NodeType.OUTPUT,
            label=f"Output: {block.name}",
            data=block.to_dict(),
            metadata={
                "value_type": block.attributes.get(
                    "value",
                    TerraformAttribute(
                        name="value", value=AttributeValue(None, AttributeType.NULL)
                    ),
                ).value.value_type.value,
                "is_sensitive": block.attributes.get(
                    "sensitive",
                    TerraformAttribute(
                        name="sensitive",
                        value=AttributeValue(False, AttributeType.BOOL),
                    ),
                ).value.raw_value,
                "dependencies": list(block.dependencies),
            },
            complexity=complexity,
        )

    def _create_local_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for a local value block."""
        complexity = self._calculate_block_complexity(block)

        return GraphNode(
            id=address,
            node_type=NodeType.LOCAL,
            label=f"Local: {block.name}",
            data=block.to_dict(),
            metadata={
                "value_type": block.attributes["value"].value.value_type.value,
                "dependencies": list(block.dependencies),
            },
            complexity=complexity,
        )

    def _create_provider_node(self, block: TerraformBlock, address: str) -> GraphNode:
        """Create a node for a provider block."""
        provider_name = block.name or block.labels[0] if block.labels else "unknown"

        return GraphNode(
            id=address,
            node_type=NodeType.PROVIDER,
            label=f"Provider: {provider_name}",
            data=block.to_dict(),
            metadata={
                "provider_name": provider_name,
                "alias": block.attributes.get(
                    "alias",
                    TerraformAttribute(
                        name="alias", value=AttributeValue(None, AttributeType.NULL)
                    ),
                ).value.raw_value,
                "config_attributes": list(block.attributes.keys()),
            },
            complexity=3,  # Providers are moderately complex
        )

    def _create_terraform_node(self, block: TerraformBlock) -> GraphNode:
        """Create a node for terraform block."""
        return GraphNode(
            id="terraform",
            node_type=NodeType.TERRAFORM,
            label="Terraform Settings",
            data=block.to_dict(),
            metadata={
                "required_providers": list(
                    block.attributes.get(
                        "required_providers",
                        TerraformAttribute(
                            name="required_providers",
                            value=AttributeValue({}, AttributeType.MAP),
                        ),
                    ).value.raw_value
                )
                if "required_providers" in block.attributes
                else []
            },
            complexity=1,
        )

    def _build_dependency_relationships(
        self, module: TerraformModule, graph: TerraformGraph
    ):
        """Build depends_on relationships between nodes."""
        for node_id, node in graph.nodes.items():
            if node.node_type in [
                NodeType.RESOURCE,
                NodeType.DATA_SOURCE,
                NodeType.MODULE,
                NodeType.OUTPUT,
            ]:
                block_data = node.data
                dependencies = block_data.get("dependencies", [])

                for dep in dependencies:
                    if dep in graph.nodes:
                        graph.add_edge(
                            GraphEdge(
                                source_id=node_id,
                                target_id=dep,
                                edge_type=EdgeType.DEPENDS_ON,
                                weight=2.0,  # Strong dependency
                                metadata={"explicit": True},
                            )
                        )

    def _build_reference_relationships(
        self, module: TerraformModule, graph: TerraformGraph
    ):
        """Build reference relationships from attribute values."""
        for node_id, node in graph.nodes.items():
            block_data = node.data

            # Extract all references from all attributes
            all_references = self._extract_all_references_from_block(block_data)

            for ref in all_references:
                if ref in graph.nodes:
                    graph.add_edge(
                        GraphEdge(
                            source_id=node_id,
                            target_id=ref,
                            edge_type=EdgeType.REFERENCES,
                            weight=1.0,  # Normal reference
                            metadata={"implicit": True},
                        )
                    )

    def _build_provider_relationships(
        self, module: TerraformModule, graph: TerraformGraph
    ):
        """Build provider-resource relationships."""
        # Map resources to their providers
        for node_id, node in graph.nodes.items():
            if node.node_type == NodeType.RESOURCE:
                provider_name = node.metadata.get("provider")
                if provider_name:
                    provider_node_id = f"provider.{provider_name}"

                    # Check for aliased provider
                    block_data = node.data
                    explicit_provider = block_data.get("explicit_provider")
                    if explicit_provider and explicit_provider.get("raw_value"):
                        provider_alias = explicit_provider["raw_value"]
                        provider_node_id = f"provider.{provider_name}.{provider_alias}"

                    if provider_node_id in graph.nodes:
                        graph.add_edge(
                            GraphEdge(
                                source_id=provider_node_id,
                                target_id=node_id,
                                edge_type=EdgeType.PROVIDES,
                                weight=1.5,
                            )
                        )

                        graph.add_edge(
                            GraphEdge(
                                source_id=node_id,
                                target_id=provider_node_id,
                                edge_type=EdgeType.USES,
                                weight=1.5,
                            )
                        )

    def _build_module_relationships(
        self, module: TerraformModule, graph: TerraformGraph
    ):
        """Build module input/output relationships."""
        # This would be enhanced with actual module input/output analysis
        pass

    def _calculate_block_complexity(self, block: TerraformBlock) -> int:
        """Calculate complexity score for a block."""
        complexity = 0

        # Base complexity by block type
        type_complexity = {
            TerraformObjectType.RESOURCE: 10,
            TerraformObjectType.DATA_SOURCE: 8,
            TerraformObjectType.MODULE: 15,
            TerraformObjectType.OUTPUT: 3,
            TerraformObjectType.LOCAL: 2,
            TerraformObjectType.VARIABLE: 1,
            TerraformObjectType.PROVIDER: 1,
            TerraformObjectType.TERRAFORM: 1,
        }

        complexity += type_complexity.get(block.block_type, 5)

        # Increase complexity based on attribute count
        complexity += len(block.attributes) * 0.5

        # Increase complexity for blocks with count/for_each
        if block.count:
            complexity += 5
        if block.for_each:
            complexity += 5

        # Increase complexity for blocks with many dependencies
        complexity += len(block.dependencies) * 0.2

        return min(int(complexity), 100)

    def _extract_provider_from_type(self, resource_type: str) -> str:
        """Extract provider name from resource type."""
        if not resource_type or "_" not in resource_type:
            return "unknown"
        return resource_type.split("_")[0]

    def _extract_all_references_from_block(
        self, block_data: Dict[str, Any]
    ) -> Set[str]:
        """Extract all unique references from a block's attributes."""
        references = set()

        def extract_from_attributes(attrs: Dict[str, Any]):
            for _attr_name, attr_data in attrs.items():
                if isinstance(attr_data, dict) and "value" in attr_data:
                    value_data = attr_data["value"]
                    if "references" in value_data:
                        for ref in value_data["references"]:
                            if "full_reference" in ref:
                                # Convert reference to node ID format
                                node_id = self._reference_to_node_id(
                                    ref["full_reference"]
                                )
                                if node_id:
                                    references.add(node_id)

        if "attributes" in block_data:
            extract_from_attributes(block_data["attributes"])

        return references

    def _reference_to_node_id(self, full_reference: str) -> Optional[str]:
        """Convert a reference string to a node ID."""
        if not full_reference:
            return None

        # References are already in the correct format for node IDs
        # var.name -> var.name
        # local.name -> local.name
        # aws_vpc.main -> aws_vpc.main
        # data.aws_vpc.main -> data.aws_vpc.main
        # module.vpc -> module.vpc

        return full_reference

    def _calculate_graph_metrics(self, graph: TerraformGraph):
        """Calculate additional graph metrics and update nodes."""
        # Calculate depth for each node using BFS from root
        self._calculate_node_depths(graph)

        # Update node status based on dependencies
        self._update_node_statuses(graph)

    def _calculate_node_depths(self, graph: TerraformGraph):
        """Calculate depth of each node from root using BFS."""
        visited = set()
        queue = [("root", 0)]

        while queue:
            node_id, depth = queue.pop(0)

            if node_id in visited:
                continue

            visited.add(node_id)

            # Update node depth
            node = graph.get_node(node_id)
            if node:
                node.depth = depth

            for edge in graph.get_edges_from(node_id):
                if edge.target_id not in visited:
                    queue.append((edge.target_id, depth + 1))

    def _update_node_statuses(self, graph: TerraformGraph):
        """Update node statuses based on dependency resolution."""
        for node_id, node in graph.nodes.items():
            if node.node_type == NodeType.VARIABLE:
                node.status = NodeStatus.RESOLVED  # Variables are inputs
            elif node.node_type == NodeType.PROVIDER:
                node.status = NodeStatus.RESOLVED  # Providers are configured
            elif node.node_type == NodeType.TERRAFORM:
                node.status = NodeStatus.RESOLVED  # Terraform settings are static
            else:
                # Check if node has unresolved dependencies
                incoming_edges = graph.get_edges_to(node_id)
                has_unresolved_deps = any(
                    graph.get_node(edge.source_id).status != NodeStatus.RESOLVED
                    for edge in incoming_edges
                    if edge.edge_type in [EdgeType.DEPENDS_ON, EdgeType.REFERENCES]
                )

                if has_unresolved_deps:
                    node.status = NodeStatus.PENDING
                else:
                    node.status = NodeStatus.RESOLVED
