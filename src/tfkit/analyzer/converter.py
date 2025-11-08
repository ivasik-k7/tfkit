from typing import Any, Dict, List

# from tfkit.inspector.graph import EdgeType, GraphEdge, GraphNode
from tfkit.inspector.models import SourceLocation, TerraformBlock, TerraformModule
from tfkit.visualizer.graph_builder import (
    EdgeType,
    GraphEdge,
    GraphNode,
    GraphNodeState,
)


class TerraformToGraphModelConverter:
    """
    Converts TerraformModule and TerraformBlock models to GraphNode/GraphEdge models.
    """

    def __init__(self):
        self.node_id_counter = 0
        self.node_map: Dict[str, int] = {}  # terraform_address -> graph_node_id
        self.graph_nodes: List[GraphNode] = []
        self.graph_edges: List[GraphEdge] = []

    def convert_module_to_graph(self, module: "TerraformModule") -> Dict[str, Any]:
        """
        Convert a TerraformModule to graph representation.

        Args:
            module: The TerraformModule instance from your parser

        Returns:
            Dictionary with 'nodes', 'edges', and 'statistics'
        """
        self._reset_state()

        # Convert all blocks to graph nodes
        self._convert_blocks_to_nodes(module)

        # Build dependency edges
        self._build_dependency_edges(module)

        # Generate statistics
        statistics = self._generate_graph_statistics()

        return {
            "nodes": [node.to_dict() for node in self.graph_nodes],
            "edges": [edge.to_dict() for edge in self.graph_edges],
            "statistics": statistics,
        }

    def _reset_state(self):
        """Reset the converter state for a new conversion."""
        self.node_id_counter = 0
        self.node_map.clear()
        self.graph_nodes.clear()
        self.graph_edges.clear()

    def _convert_blocks_to_nodes(self, module: "TerraformModule"):
        """Convert all Terraform blocks to GraphNode objects."""

        # Convert resources
        for address, block in module._global_resource_index.items():
            if not address.startswith("data."):
                self._convert_resource_block(block, address)

        # Convert data sources
        for address, block in module._global_resource_index.items():
            if address.startswith("data."):
                self._convert_data_source_block(block, address)

        # Convert modules
        for address, block in module._global_module_index.items():
            self._convert_module_block(block, address)

        # Convert variables
        for address, block in module._global_variable_index.items():
            self._convert_variable_block(block, address)

        # Convert outputs
        for address, block in module._global_output_index.items():
            self._convert_output_block(block, address)

        # Convert locals
        for address, block in module._global_local_index.items():
            self._convert_local_block(block, address)

        # Convert providers
        for address, block in module._global_provider_index.items():
            self._convert_provider_block(block, address)

        # Convert terraform block
        terraform_blocks = list(module._global_terraform_index.values())
        if terraform_blocks:
            self._convert_terraform_block(terraform_blocks[0])

    def _convert_resource_block(self, block: "TerraformBlock", address: str):
        """Convert a resource block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        # Determine state based on dependencies and references
        state, state_reason = self._determine_resource_state(block)

        node = GraphNode(
            id=node_id,
            label=block.name or address,
            type="resource",
            subtype=block.resource_type or "unknown",
            state=state,
            state_reason=state_reason,
            dependencies_out=len(block.dependencies),
            dependencies_in=0,
            details=self._create_resource_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_data_source_block(self, block: "TerraformBlock", address: str):
        """Convert a data source block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        # Extract data source type (remove 'data.' prefix)
        data_type = block.resource_type or "unknown"

        state, state_reason = self._determine_data_source_state(block)

        node = GraphNode(
            id=node_id,
            label=block.name or address,
            type="data_source",
            subtype=data_type,
            state=state,
            state_reason=state_reason,
            dependencies_out=len(block.dependencies),
            dependencies_in=0,
            details=self._create_data_source_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_module_block(self, block: "TerraformBlock", address: str):
        """Convert a module block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        # Extract module source for subtype
        source_attr = block.attributes.get("source")
        source = source_attr.value.raw_value if source_attr else "local"
        subtype = self._extract_module_name(source)

        state, state_reason = self._determine_module_state(block)

        node = GraphNode(
            id=node_id,
            label=block.name or address,
            type="module",
            subtype=subtype,
            state=state,
            state_reason=state_reason,
            dependencies_out=len(block.dependencies),
            dependencies_in=0,
            details=self._create_module_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_variable_block(self, block: "TerraformBlock", address: str):
        """Convert a variable block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        # Extract variable type
        type_attr = block.attributes.get("type")
        var_type = type_attr.value.raw_value if type_attr else "any"
        formatted_type = self._format_terraform_type(var_type)

        state = GraphNodeState.INPUT
        state_reason = "Input variable"

        node = GraphNode(
            id=node_id,
            label=block.name or address.replace("var.", ""),
            type="variable",
            subtype=formatted_type,
            state=state,
            state_reason=state_reason,
            dependencies_out=0,  # Variables don't have outgoing dependencies
            dependencies_in=0,  # Will be updated when building edges
            details=self._create_variable_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_output_block(self, block: "TerraformBlock", address: str):
        """Convert an output block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        state = GraphNodeState.OUTPUT
        state_reason = "Output value"

        node = GraphNode(
            id=node_id,
            label=block.name or address.replace("output.", ""),
            type="output",
            subtype="output",
            state=state,
            state_reason=state_reason,
            dependencies_out=len(block.dependencies),
            dependencies_in=0,
            details=self._create_output_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_local_block(self, block: "TerraformBlock", address: str):
        """Convert a local value block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        state, state_reason = self._determine_local_state(block)

        node = GraphNode(
            id=node_id,
            label=block.name or address.replace("local.", ""),
            type="local",
            subtype="local",
            state=state,
            state_reason=state_reason,
            dependencies_out=len(block.dependencies),
            dependencies_in=0,
            details=self._create_local_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_provider_block(self, block: "TerraformBlock", address: str):
        """Convert a provider block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map[address] = node_id

        provider_name = block.name or block.labels[0] if block.labels else "unknown"

        state = GraphNodeState.CONFIGURATION
        state_reason = "Provider configuration"

        node = GraphNode(
            id=node_id,
            label=provider_name,
            type="provider",
            subtype=provider_name,
            state=state,
            state_reason=state_reason,
            dependencies_out=0,
            dependencies_in=0,
            details=self._create_provider_details(block, address),
        )

        self.graph_nodes.append(node)

    def _convert_terraform_block(self, block: "TerraformBlock"):
        """Convert terraform block to GraphNode."""
        node_id = self._get_next_node_id()
        self.node_map["terraform"] = node_id

        state = GraphNodeState.CONFIGURATION
        state_reason = "Terraform settings"

        node = GraphNode(
            id=node_id,
            label="terraform",
            type="terraform",
            subtype="settings",
            state=state,
            state_reason=state_reason,
            dependencies_out=0,
            dependencies_in=0,
            details=self._create_terraform_details(block),
        )

        self.graph_nodes.append(node)

    def _build_dependency_edges(self, module: "TerraformModule"):
        """Build dependency edges between nodes."""

        # Build edges from explicit dependencies
        for address, block in module._global_resource_index.items():
            self._build_edges_for_block(block, address)

        for address, block in module._global_module_index.items():
            self._build_edges_for_block(block, address)

        for address, block in module._global_output_index.items():
            self._build_edges_for_block(block, address)

        for address, block in module._global_local_index.items():
            self._build_edges_for_block(block, address)

        # Build provider relationships
        self._build_provider_edges(module)

    def _build_edges_for_block(self, block: "TerraformBlock", address: str):
        """Build edges for a specific block."""
        source_id = self.node_map.get(address)
        if source_id is None:
            return

        # Build edges from explicit dependencies
        for dep_address in block.dependencies:
            target_id = self.node_map.get(dep_address)
            if target_id is not None:
                edge_type = EdgeType.EXPLICIT
                strength = 1.0

                # Check if this is a provider dependency
                if dep_address.startswith("provider."):
                    edge_type = EdgeType.PROVIDER
                    strength = 0.5

                self._add_edge(source_id, target_id, edge_type, strength)

        # Build edges from attribute references
        self._build_implicit_edges_from_attributes(block, source_id)

    def _build_implicit_edges_from_attributes(
        self, block: "TerraformBlock", source_id: int
    ):
        """Build implicit edges from attribute references."""
        for _attr_name, attribute in block.attributes.items():
            attr_value = attribute.value
            if attr_value.references:
                for ref in attr_value.references:
                    target_address = ref.full_reference
                    target_id = self.node_map.get(target_address)
                    if target_id is not None:
                        edge_type = EdgeType.IMPLICIT
                        strength = 0.7

                        self._add_edge(source_id, target_id, edge_type, strength)

    def _build_provider_edges(self, module: "TerraformModule"):
        """Build provider-resource relationships."""
        for address, block in module._global_resource_index.items():
            if not address.startswith("data."):
                self._build_provider_edge_for_resource(block, address)

    def _build_provider_edge_for_resource(self, block: "TerraformBlock", address: str):
        """Build provider edge for a specific resource."""
        source_id = self.node_map.get(address)
        if source_id is None:
            return

        # Determine provider from resource type
        if block.resource_type and "_" in block.resource_type:
            provider_name = block.resource_type.split("_")[0]
            provider_address = f"provider.{provider_name}"

            # Check for aliased provider
            provider_attr = block.attributes.get("provider")
            if provider_attr and provider_attr.value.raw_value:
                provider_alias = provider_attr.value.raw_value
                provider_address = f"provider.{provider_name}.{provider_alias}"

            target_id = self.node_map.get(provider_address)
            if target_id is not None:
                self._add_edge(source_id, target_id, EdgeType.PROVIDER, 0.5)

    def _add_edge(
        self, source_id: int, target_id: int, edge_type: EdgeType, strength: float
    ):
        """Add an edge and update node connection counts."""
        edge = GraphEdge(
            source=source_id, target=target_id, type=edge_type, strength=strength
        )

        self.graph_edges.append(edge)

        # Update connection counts
        source_node = next((n for n in self.graph_nodes if n.id == source_id), None)
        target_node = next((n for n in self.graph_nodes if n.id == target_id), None)

        if source_node:
            source_node.dependencies_out += 1
        if target_node:
            target_node.dependencies_in += 1

    def _determine_resource_state(self, block: "TerraformBlock") -> tuple:
        """Determine the visual state for a resource."""
        if not block.dependencies:
            return GraphNodeState.LEAF, "No dependencies"

        if len(block.dependencies) > 10:
            return GraphNodeState.COMPLEX, "High dependency complexity"

        return GraphNodeState.ACTIVE, "Active resource"

    def _determine_data_source_state(self, block: "TerraformBlock") -> tuple:
        """Determine the visual state for a data source."""
        return GraphNodeState.EXTERNAL_DATA, "External data source"

    def _determine_module_state(self, block: "TerraformBlock") -> tuple:
        """Determine the visual state for a module."""
        return GraphNodeState.INTEGRATED, "Integrated module"

    def _determine_local_state(self, block: "TerraformBlock") -> tuple:
        """Determine the visual state for a local value."""
        if not block.dependencies:
            return GraphNodeState.LEAF, "Simple local value"

        return GraphNodeState.INTEGRATED, "Computed local value"

    # Detail creation methods
    def _create_resource_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a resource node."""
        details = {
            "address": address,
            "resource_type": block.resource_type,
            "dependencies": list(block.dependencies),
            "attribute_count": len(block.attributes),
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_data_source_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a data source node."""
        details = {
            "address": address,
            "data_type": block.resource_type,
            "dependencies": list(block.dependencies),
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_module_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a module node."""
        source_attr = block.attributes.get("source")
        source = source_attr.value.raw_value if source_attr else "unknown"

        details = {
            "address": address,
            "source": source,
            "dependencies": list(block.dependencies),
            "input_count": len(
                [k for k in block.attributes.keys() if k not in ["source", "version"]]
            ),
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_variable_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a variable node."""
        type_attr = block.attributes.get("type")
        default_attr = block.attributes.get("default")
        sensitive_attr = block.attributes.get("sensitive")

        details = {
            "address": address,
            "variable_type": type_attr.value.raw_value if type_attr else "any",
            "has_default": default_attr is not None,
            "is_sensitive": sensitive_attr.value.raw_value if sensitive_attr else False,
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_output_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for an output node."""
        sensitive_attr = block.attributes.get("sensitive")

        details = {
            "address": address,
            "is_sensitive": sensitive_attr.value.raw_value if sensitive_attr else False,
            "dependencies": list(block.dependencies),
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_local_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a local node."""
        details = {"address": address, "dependencies": list(block.dependencies)}

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_provider_details(
        self, block: "TerraformBlock", address: str
    ) -> Dict[str, Any]:
        """Create details for a provider node."""
        alias_attr = block.attributes.get("alias")

        details = {
            "address": address,
            "alias": alias_attr.value.raw_value if alias_attr else None,
            "config_attributes": list(block.attributes.keys()),
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _create_terraform_details(self, block: "TerraformBlock") -> Dict[str, Any]:
        """Create details for terraform node."""
        required_providers_attr = block.attributes.get("required_providers")
        providers = (
            required_providers_attr.value.raw_value if required_providers_attr else {}
        )

        details = {
            "required_providers": (
                list(providers.keys()) if isinstance(providers, dict) else []
            )
        }

        if block.source_location:
            details["location"] = self._format_location(block.source_location)

        return details

    def _format_location(self, location: "SourceLocation") -> str:
        """Format source location for display."""
        filename = (
            location.file_path.split("/")[-1] if location.file_path else "unknown"
        )
        return f"{filename}:{location.line_start}"

    def _extract_module_name(self, source: str) -> str:
        """Extract module name from source string."""
        if "/" in source:
            return source.split("/")[-1]
        return source

    def _format_terraform_type(self, type_str: str) -> str:
        """Format Terraform type for display (simplified version)."""
        if not isinstance(type_str, str):
            return str(type_str)

        # Remove complex formatting for now - use the full version from your existing code if needed
        if len(type_str) > 50:
            return type_str[:47] + "..."
        return type_str

    def _get_next_node_id(self) -> int:
        """Get the next available node ID."""
        self.node_id_counter += 1
        return self.node_id_counter

    def _generate_graph_statistics(self) -> Dict[str, Any]:
        """Generate statistics for the graph."""
        if not self.graph_nodes:
            return {}

        # Count nodes by type
        type_counts = {}
        state_counts = {}

        for node in self.graph_nodes:
            type_counts[node.type] = type_counts.get(node.type, 0) + 1
            state_counts[node.state.value] = state_counts.get(node.state.value, 0) + 1

        # Calculate connectivity
        total_deps_out = sum(node.dependencies_out for node in self.graph_nodes)
        total_deps_in = sum(node.dependencies_in for node in self.graph_nodes)
        avg_deps_out = total_deps_out / len(self.graph_nodes)
        avg_deps_in = total_deps_in / len(self.graph_nodes)

        return {
            "node_count": len(self.graph_nodes),
            "edge_count": len(self.graph_edges),
            "node_types": type_counts,
            "node_states": state_counts,
            "connectivity": {
                "avg_dependencies_out": round(avg_deps_out, 2),
                "avg_dependencies_in": round(avg_deps_in, 2),
            },
        }
