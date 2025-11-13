from collections import defaultdict
from typing import Any, Dict, List, Optional

from tfkit.dependency import (
    DependencyType,
    ObjectDependencies,
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
from tfkit.parser.models import TerraformCatalog


class TerraformGraphBuilder:
    """
    Builds a comprehensive dependency graph from Terraform catalog and dependencies.
    Analyzes node relationships to determine states (hub, leaf, unused, etc.)
    """

    # Mapping from Terraform object types to NodeType
    OBJECT_TYPE_TO_NODE_TYPE = {
        "resource": NodeType.RESOURCE,
        "data": NodeType.DATA,
        "module": NodeType.MODULE,
        "variable": NodeType.VARIABLE,
        "output": NodeType.OUTPUT,
        "provider": NodeType.PROVIDER,
        "local": NodeType.LOCAL,
        "terraform": NodeType.TERRAFORM,
    }

    DEPENDENCY_TO_LINK_TYPE = {
        DependencyType.DIRECT: LinkType.DIRECT,
        DependencyType.IMPLICIT: LinkType.IMPLICIT,
        DependencyType.PROVIDER: LinkType.PROVIDER_CONFIG,
        DependencyType.MODULE: LinkType.MODULE_CALL,
        DependencyType.MOVED: LinkType.LIFECYCLE,
    }

    def __init__(
        self,
        catalog: TerraformCatalog,
        dependencies: Dict[str, ObjectDependencies] = None,
    ):
        """
        Initialize the graph builder.

        Args:
            catalog: TerraformCatalog with parsed objects
            dependencies: Pre-built dependencies mapping from address to list of Dependency objects
        """
        if dependencies is None:
            dependencies = {}
        self.catalog = catalog
        self.dependencies = dependencies or {}
        self.graph = GraphData()

        # Analysis caches
        self._in_degree: Dict[str, int] = {}
        self._out_degree: Dict[str, int] = {}
        self._node_depth: Dict[str, int] = {}

    def build_graph(self) -> GraphData:
        """
        Build the complete dependency graph with nodes and links.

        Returns:
            GraphData with all nodes and links
        """
        # Build nodes
        self._build_nodes()

        # Build links
        self._build_links()

        # Analyze and set node states
        self._analyze_node_states()

        # Calculate graph metrics
        self._calculate_graph_metrics()

        return self.graph

    def _build_nodes(self):
        """Create nodes for all objects in the catalog"""
        for address in self.catalog.get_all_addresses():
            obj = self.catalog.get_by_address(address)
            if not obj:
                continue

            # Determine node type
            obj_type_value = getattr(obj, "object_type", None)
            if not obj_type_value:
                continue

            node_type = self.OBJECT_TYPE_TO_NODE_TYPE.get(
                obj_type_value.value, NodeType.RESOURCE
            )

            # Extract metadata
            node_data = self._extract_node_data(obj, address)

            # Create node
            node = Node(
                id=address,
                name=self._extract_display_name(obj, address),
                type=node_type,
                data=node_data,
                group=self._determine_group(obj, node_type),
            )

            self.graph.add_node(node)

    def _extract_node_data(self, obj: Any, address: str) -> NodeData:
        """
        Extract comprehensive metadata from Terraform object.

        Args:
            obj: Terraform object
            address: Object address

        Returns:
            NodeData with extracted information
        """
        # Extract basic attributes
        provider = getattr(obj, "provider", None)
        source_location = getattr(obj, "source_location", None)

        source_file = None
        line_number = None
        if source_location:
            source_file = str(getattr(source_location, "file_path", None))
            line_number = getattr(source_location, "start_line", None)

        # Extract depends_on
        depends_on_attr = getattr(obj, "depends_on", None)
        depends_on = []
        if depends_on_attr:
            if isinstance(depends_on_attr, list):
                depends_on = depends_on_attr
            elif isinstance(depends_on_attr, str):
                depends_on = [depends_on_attr]

        # Extract count/for_each
        count = getattr(obj, "count", None)
        for_each = getattr(obj, "for_each", None)

        # Extract lifecycle rules
        lifecycle_rules = getattr(obj, "lifecycle", None)

        # Extract tags (common in resources)
        tags = {}
        attributes = getattr(obj, "attributes", {})
        if isinstance(attributes, dict):
            tags = attributes.get("tags", {})
            if not isinstance(tags, dict):
                tags = {}

        # Build node data
        return NodeData(
            provider=provider,
            source_file=source_file,
            line_number=line_number,
            depends_on=depends_on,
            count=count,
            for_each=for_each,
            lifecycle_rules=lifecycle_rules,
            tags=tags,
            state=NodeState.ACTIVE,  # Will be updated in analysis phase
            attributes=attributes if isinstance(attributes, dict) else {},
        )

    def _extract_display_name(self, obj: Any, address: str) -> str:
        """
        Extract a human-readable display name.

        Args:
            obj: Terraform object
            address: Object address

        Returns:
            Display name string
        """
        name = getattr(obj, "name", None)
        if name:
            return name

        # Fallback to last part of address
        parts = address.split(".")
        if parts:
            return parts[-1]

        return address

    def _determine_group(self, obj: Any, node_type: NodeType) -> Optional[str]:
        """
        Determine logical grouping for the node.

        Args:
            obj: Terraform object
            node_type: Type of node

        Returns:
            Group identifier
        """
        # Group by provider for resources and data sources
        if node_type in (NodeType.RESOURCE, NodeType.DATA):
            provider = getattr(obj, "provider", None)
            if provider:
                return f"provider:{provider}"

            # Infer from resource type
            resource_type = getattr(obj, "resource_type", None) or getattr(
                obj, "data_type", None
            )
            if resource_type:
                prefix = resource_type.split("_")[0] if "_" in resource_type else None
                if prefix:
                    return f"provider:{prefix}"

        # Group by type for others
        return f"type:{node_type.value}"

    def _build_links(self):
        """Create links from dependency information"""
        for _address, obj_deps in self.dependencies.items():
            for dep in obj_deps.depends_on:
                # Determine link type
                link_type = self.DEPENDENCY_TO_LINK_TYPE.get(
                    dep.dependency_type, LinkType.IMPLICIT
                )

                # Calculate link strength based on dependency type
                strength = self._calculate_link_strength(dep.dependency_type)

                # Extract reference path
                reference_path = None
                if dep.attribute_path:
                    reference_path = dep.attribute_path.split(".")

                # Create link
                link = Link(
                    source=dep.source_address,
                    target=dep.target_address,
                    link_type=link_type,
                    strength=strength,
                    reference_path=reference_path,
                )

                self.graph.add_link(link)

    def _calculate_link_strength(self, dep_type: DependencyType) -> float:
        """
        Calculate link strength based on dependency type.

        Args:
            dep_type: Type of dependency

        Returns:
            Strength value (0.0 to 1.0)
        """
        strength_map = {
            DependencyType.DIRECT: 1.0,
            DependencyType.PROVIDER: 0.8,
            DependencyType.MODULE: 0.9,
            DependencyType.IMPLICIT: 0.6,
            DependencyType.MOVED: 0.5,
        }
        return strength_map.get(dep_type, 0.5)

    def _analyze_node_states(self):
        """Analyze nodes to determine their states in the dependency graph"""
        # Calculate in/out degrees
        self._calculate_degrees()

        # Analyze each node
        for node_id, node in self.graph.nodes.items():
            state = self._determine_node_state(node_id, node)
            node.data.state = state

            # Update node weight based on connectivity
            node.weight = self._calculate_node_weight(node_id)

    def _calculate_degrees(self):
        """Calculate in-degree and out-degree for each node"""
        self._in_degree = defaultdict(int)
        self._out_degree = defaultdict(int)

        for link in self.graph.links:
            self._out_degree[link.source] += 1
            self._in_degree[link.target] += 1

    def _determine_node_state(self, node_id: str, node: Node) -> NodeState:
        """
        Determine the state of a node based on its relationships.

        Args:
            node_id: Node identifier
            node: Node object

        Returns:
            Determined NodeState
        """
        in_deg = self._in_degree.get(node_id, 0)
        out_deg = self._out_degree.get(node_id, 0)

        # Get dependency details
        # obj_deps = self.dependencies.get_dependencies(node_id)

        # UNUSED: No incoming or outgoing dependencies
        if in_deg == 0 and out_deg == 0:
            # Exception for terraform block and providers (they're configuration)
            if node.type in (NodeType.TERRAFORM, NodeType.PROVIDER):
                return NodeState.CONFIGURATION
            return NodeState.ORPHAN

        # LEAF: Has dependencies but nothing depends on it
        if in_deg == 0 and out_deg > 0:
            # Outputs are typically leaves by design
            if node.type == NodeType.OUTPUT:
                return NodeState.LEAF
            # Resources/data without consumers
            if node.type in (NodeType.RESOURCE, NodeType.DATA):
                return NodeState.LEAF
            return NodeState.LEAF

        # Configuration nodes
        if node.type == NodeType.VARIABLE:
            # Variables with only outgoing are config providers
            if in_deg == 0 and out_deg > 0:
                return NodeState.CONFIG_PROVIDER
            return NodeState.CONFIGURATION

        if node.type == NodeType.PROVIDER:
            # Providers can depend on variables but provide config to resources
            return NodeState.CONFIGURATION

        # SHARED: Referenced by many nodes
        if in_deg >= 3:
            return NodeState.SHARED

        # HUB: High connectivity in both directions
        if in_deg >= 2 and out_deg >= 2:
            return NodeState.HUB

        # BRIDGE: Connects different parts of the graph
        if in_deg > 0 and out_deg > 0:
            # Check if it connects different provider groups
            if self._is_bridge_node(node_id):
                return NodeState.BRIDGE

        # LOCALS and computed values
        if node.type == NodeType.LOCAL:
            if out_deg > 0:
                return NodeState.DERIVED
            return NodeState.EPHEMERAL

        # MODULE nodes
        if node.type == NodeType.MODULE:
            if in_deg > 0 and out_deg > 0:
                return NodeState.AGGREGATOR
            if out_deg > 0:
                return NodeState.DEPENDENCY
            return NodeState.ACTIVE

        # DEPENDENCY: Primarily consumed by others
        if in_deg > out_deg:
            return NodeState.DEPENDENCY

        # CONFIG_CONSUMER: Depends heavily on configuration
        if out_deg > in_deg and self._depends_on_config(node_id):
            return NodeState.CONFIG_CONSUMER

        # Default: ACTIVE
        return NodeState.ACTIVE

    def _is_bridge_node(self, node_id: str) -> bool:
        """
        Check if a node acts as a bridge between different parts of the graph.

        Args:
            node_id: Node identifier

        Returns:
            True if node is a bridge
        """
        # Get source and target groups
        source_groups = set()
        target_groups = set()

        for link in self.graph.links:
            if link.target == node_id:
                source_node = self.graph.nodes.get(link.source)
                if source_node and source_node.group:
                    source_groups.add(source_node.group)

            if link.source == node_id:
                target_node = self.graph.nodes.get(link.target)
                if target_node and target_node.group:
                    target_groups.add(target_node.group)

        # Bridge if connecting multiple different groups
        return len(source_groups) > 1 or len(target_groups) > 1

    def _depends_on_config(self, node_id: str) -> bool:
        """
        Check if a node depends primarily on configuration nodes.

        Args:
            node_id: Node identifier

        Returns:
            True if depends on config nodes
        """
        config_dependency_count = 0
        total_dependencies = 0

        for link in self.graph.links:
            if link.source == node_id:
                total_dependencies += 1
                target_node = self.graph.nodes.get(link.target)
                if target_node and target_node.type in (
                    NodeType.VARIABLE,
                    NodeType.LOCAL,
                ):
                    config_dependency_count += 1

        if total_dependencies == 0:
            return False

        # If more than 50% of dependencies are config nodes
        return config_dependency_count / total_dependencies > 0.5

    def _calculate_node_weight(self, node_id: str) -> float:
        """
        Calculate node weight based on connectivity and importance.

        Args:
            node_id: Node identifier

        Returns:
            Weight value
        """
        in_deg = self._in_degree.get(node_id, 0)
        out_deg = self._out_degree.get(node_id, 0)

        total_connections = in_deg + out_deg

        weight = 1.0 + (total_connections * 0.2) + (in_deg * 0.1)

        return min(weight, 5.0)

    def _calculate_graph_metrics(self):
        """Calculate additional graph-level metrics"""
        # Calculate node depth (distance from variables/config)
        self._calculate_node_depths()

        # Apply depth to node positions for potential visualization
        for node_id, depth in self._node_depth.items():
            node = self.graph.nodes.get(node_id)
            if node:
                if not node.position:
                    node.position = {}
                node.position["depth"] = float(depth)

    def _calculate_node_depths(self):
        """
        Calculate depth of each node from root configuration nodes.
        Variables and locals are depth 0, resources depending on them are depth 1, etc.
        """
        self._node_depth = {}

        # Initialize configuration nodes at depth 0
        for node_id, node in self.graph.nodes.items():
            if node.type in (
                NodeType.VARIABLE,
                NodeType.TERRAFORM,
                NodeType.PROVIDER,
            ):
                self._node_depth[node_id] = 0

        # BFS to calculate depths
        changed = True
        max_iterations = 100
        iteration = 0

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            for link in self.graph.links:
                # Skip implicit provider links for depth calculation
                if link.link_type == LinkType.IMPLICIT:
                    continue

                source_depth = self._node_depth.get(link.source)
                target_depth = self._node_depth.get(link.target)

                # If source has depth and target doesn't, or target has higher depth
                if source_depth is not None:
                    new_depth = source_depth + 1
                    if target_depth is None or new_depth < target_depth:
                        self._node_depth[link.target] = new_depth
                        changed = True

        # Assign default depth to any remaining nodes
        for node_id in self.graph.nodes:
            if node_id not in self._node_depth:
                self._node_depth[node_id] = -1  # Unknown depth

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the graph.

        Returns:
            Dictionary with graph statistics
        """
        # Count nodes by type
        node_type_counts = defaultdict(int)
        for node in self.graph.nodes.values():
            node_type_counts[node.type.value] += 1

        # Count nodes by state
        node_state_counts = defaultdict(int)
        for node in self.graph.nodes.values():
            node_state_counts[node.data.state.value] += 1

        # Count links by type
        link_type_counts = defaultdict(int)
        for link in self.graph.links:
            link_type_counts[link.link_type.value] += 1

        # Find most connected nodes
        most_connected = sorted(
            self.graph.nodes.items(),
            key=lambda x: self._in_degree.get(x[0], 0) + self._out_degree.get(x[0], 0),
            reverse=True,
        )[:10]

        # Find hub nodes
        hubs = [
            node_id
            for node_id, node in self.graph.nodes.items()
            if node.data.state == NodeState.HUB
        ]

        # Find unused/orphan nodes
        unused = [
            node_id
            for node_id, node in self.graph.nodes.items()
            if node.data.state in (NodeState.UNUSED, NodeState.ORPHAN)
        ]

        return {
            "total_nodes": len(self.graph.nodes),
            "total_links": len(self.graph.links),
            "node_types": dict(node_type_counts),
            "node_states": dict(node_state_counts),
            "link_types": dict(link_type_counts),
            "most_connected_nodes": [
                {
                    "id": node_id,
                    "name": node.name,
                    "in_degree": self._in_degree.get(node_id, 0),
                    "out_degree": self._out_degree.get(node_id, 0),
                }
                for node_id, node in most_connected[:5]
            ],
            "hub_nodes": hubs,
            "unused_nodes": unused,
            "max_depth": max(self._node_depth.values()) if self._node_depth else 0,
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export graph to a serializable dictionary.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "state": node.data.state.value,
                    "group": node.group,
                    "weight": node.weight,
                    "provider": node.data.provider,
                    "source_file": node.data.source_file,
                    "line_number": node.data.line_number,
                    "in_degree": self._in_degree.get(node.id, 0),
                    "out_degree": self._out_degree.get(node.id, 0),
                    "depth": self._node_depth.get(node.id, -1),
                    "position": node.position,
                    "tags": node.data.tags,
                }
                for node in self.graph.nodes.values()
            ],
            "links": [
                {
                    "source": link.source,
                    "target": link.target,
                    "type": link.link_type.value,
                    "strength": link.strength,
                    "reference_path": link.reference_path,
                }
                for link in self.graph.links
            ],
            "statistics": self.get_graph_statistics(),
        }

    def get_subgraph(
        self,
        node_ids: List[str],
        include_dependencies: bool = True,
        include_dependents: bool = True,
        max_depth: int = -1,
    ) -> GraphData:
        """
        Extract a subgraph containing specified nodes and their relationships.

        Args:
            node_ids: List of node IDs to include
            include_dependencies: Include nodes this depends on
            include_dependents: Include nodes that depend on this
            max_depth: Maximum depth to traverse (-1 for unlimited)

        Returns:
            New GraphData with subgraph
        """
        subgraph = GraphData()
        visited = set()

        def collect_nodes(node_id: str, depth: int):
            if node_id in visited:
                return
            if max_depth >= 0 and depth > max_depth:
                return

            visited.add(node_id)

            # Add node
            if node_id in self.graph.nodes:
                subgraph.add_node(self.graph.nodes[node_id])

            # Traverse dependencies
            if include_dependencies:
                for link in self.graph.links:
                    if link.source == node_id:
                        collect_nodes(link.target, depth + 1)

            # Traverse dependents
            if include_dependents:
                for link in self.graph.links:
                    if link.target == node_id:
                        collect_nodes(link.source, depth + 1)

        # Collect all relevant nodes
        for node_id in node_ids:
            collect_nodes(node_id, 0)

        # Add links between collected nodes
        for link in self.graph.links:
            if link.source in visited and link.target in visited:
                subgraph.add_link(link)

        return subgraph
