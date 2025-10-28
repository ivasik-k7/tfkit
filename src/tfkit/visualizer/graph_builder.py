import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from ..analyzer.models import ObjectState, ResourceType
from ..analyzer.project import TerraformProject


class GraphNodeState(Enum):
    """Visual states for graph nodes with clear UI semantics."""

    # Positive states
    HEALTHY = "healthy"
    ACTIVE = "active"
    INTEGRATED = "integrated"

    # Neutral/Informational states
    INPUT = "input"
    OUTPUT = "output"
    CONFIGURATION = "configuration"
    EXTERNAL_DATA = "external_data"
    LEAF = "leaf"
    HUB = "hub"

    # Warning states
    UNUSED = "unused"
    ISOLATED = "isolated"
    ORPHANED = "orphaned"
    UNDERUTILIZED = "underutilized"
    COMPLEX = "complex"

    # Error states
    INCOMPLETE = "incomplete"
    BROKEN = "broken"
    MISSING_DEPENDENCY = "missing_dependency"


class EdgeType(Enum):
    """Types of edges in the dependency graph."""

    EXPLICIT = "explicit"  # depends_on
    IMPLICIT = "implicit"  # reference in configuration
    PROVIDER = "provider"  # resource -> provider relationship


@dataclass
class GraphNode:
    """Node in the visualization graph."""

    id: int
    label: str
    type: str  # ResourceType value
    subtype: str  # Specific type (e.g., "aws_instance", "string")
    state: GraphNodeState
    state_reason: str

    # Connection counts
    dependencies_out: int = 0  # This node depends on X others
    dependencies_in: int = 0  # X others depend on this node

    # Visual metadata
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "subtype": self.subtype,
            "state": self.state.value,
            "state_reason": self.state_reason,
            "dependencies_out": self.dependencies_out,
            "dependencies_in": self.dependencies_in,
            "details": self.details,
        }


@dataclass
class GraphEdge:
    """Edge in the visualization graph."""

    source: int  # source node ID
    target: int  # target node ID
    type: EdgeType
    strength: float  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "strength": self.strength,
        }


class TerraformGraphBuilder:
    """
    Builds visualization-ready dependency graphs from Terraform projects.

    Creates a graph representation suitable for D3.js, Cytoscape.js,
    or other visualization libraries.
    """

    # Edge strength constants
    STRENGTH_EXPLICIT = 1.0
    STRENGTH_IMPLICIT = 0.7
    STRENGTH_PROVIDER = 0.5

    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.node_map: Dict[str, int] = {}  # object_name -> node_id
        self.next_id = 0

    def build_graph(self, project: TerraformProject) -> Dict[str, Any]:
        """
        Build complete graph from a Terraform project.

        Args:
            project: TerraformProject instance

        Returns:
            Dictionary with 'nodes', 'edges', and 'statistics'
        """
        # Reset state
        self.nodes = []
        self.edges = []
        self.node_map = {}
        self.next_id = 0

        # Phase 1: Create all nodes
        self._create_nodes(project)

        # Phase 2: Create all edges
        self._create_edges(project)

        # Phase 3: Generate statistics
        statistics = self._generate_statistics(project)

        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "statistics": statistics,
        }

    def _create_nodes(self, project: TerraformProject) -> None:
        """Create all graph nodes from project objects."""
        for obj in project.all_objects.values():
            visual_state = self._map_object_state_to_visual(obj.state)

            state_meta = self._get_state_metadata(visual_state)

            subtype = self._determine_subtype(obj)

            details = {
                "file": obj.location.file_path,
                "line": obj.location.line_number,
                "color": state_meta["color"],
                "severity": state_meta["severity"],
                "icon": state_meta["icon"],
                "priority": state_meta["priority"],
            }

            if obj.resource_type:
                details["resource_type"] = obj.resource_type
            if obj.provider_info:
                details["provider"] = obj.provider_info.full_provider_reference
            if obj.description:
                details["description"] = obj.description
            if obj.source:
                details["source"] = obj.source
            if obj.sensitive:
                details["sensitive"] = True

            node = GraphNode(
                id=self.next_id,
                label=obj.full_name,
                type=obj.type.value,
                subtype=subtype,
                state=visual_state,
                state_reason=obj.state_reason,
                details=details,
            )

            self.nodes.append(node)
            self.node_map[obj.full_name] = self.next_id
            self.next_id += 1

    def _create_edges(self, project: TerraformProject) -> None:
        """Create all graph edges from project dependencies."""
        for obj in project.all_objects.values():
            source_id = self.node_map.get(obj.full_name)
            if source_id is None:
                continue

            # Explicit dependencies
            for dep_name in obj.dependency_info.explicit_dependencies:
                target_id = self.node_map.get(dep_name)
                if target_id is not None:
                    edge_type = EdgeType.EXPLICIT
                    # Check if this is a provider dependency
                    if dep_name.startswith("provider."):
                        edge_type = EdgeType.PROVIDER
                    self._add_edge(
                        source_id, target_id, edge_type, self.STRENGTH_EXPLICIT
                    )

            # Implicit dependencies (includes provider relationships)
            for dep_name in obj.dependency_info.implicit_dependencies:
                target_id = self.node_map.get(dep_name)
                if target_id is not None:
                    edge_type = EdgeType.IMPLICIT
                    strength = self.STRENGTH_IMPLICIT

                    # Provider relationships are implicit but should be marked as PROVIDER type
                    if dep_name.startswith("provider."):
                        edge_type = EdgeType.PROVIDER
                        strength = self.STRENGTH_PROVIDER

                    self._add_edge(source_id, target_id, edge_type, strength)

    def _add_edge(
        self, source_id: int, target_id: int, edge_type: EdgeType, strength: float
    ) -> None:
        """Add an edge and update node connection counts."""
        edge = GraphEdge(
            source=source_id,
            target=target_id,
            type=edge_type,
            strength=strength,
        )

        self.edges.append(edge)

        # Update connection counts
        self.nodes[source_id].dependencies_out += 1
        self.nodes[target_id].dependencies_in += 1

    def _map_object_state_to_visual(
        self, state: ObjectState, obj=None
    ) -> GraphNodeState:
        """
        Map enhanced semantic states to visual graph states.

        Now uses the comprehensive ObjectState enum directly for more accurate mapping.
        """
        try:
            # Direct mapping since we now have comprehensive states
            state_mapping = {
                # Positive states
                ObjectState.HEALTHY: GraphNodeState.HEALTHY,
                ObjectState.ACTIVE: GraphNodeState.ACTIVE,
                ObjectState.INTEGRATED: GraphNodeState.INTEGRATED,
                ObjectState.INPUT: GraphNodeState.INPUT,
                ObjectState.OUTPUT_INTERFACE: GraphNodeState.OUTPUT,
                ObjectState.CONFIGURATION: GraphNodeState.CONFIGURATION,
                ObjectState.EXTERNAL_DATA: GraphNodeState.EXTERNAL_DATA,
                ObjectState.LEAF: GraphNodeState.LEAF,
                ObjectState.HUB: GraphNodeState.HUB,
                # Warning states
                ObjectState.UNUSED: GraphNodeState.UNUSED,
                ObjectState.ISOLATED: GraphNodeState.ISOLATED,
                ObjectState.ORPHANED: GraphNodeState.ORPHANED,
                ObjectState.UNDERUTILIZED: GraphNodeState.UNDERUTILIZED,
                ObjectState.COMPLEX: GraphNodeState.COMPLEX,
                # Error states
                ObjectState.INCOMPLETE: GraphNodeState.INCOMPLETE,
                ObjectState.BROKEN: GraphNodeState.BROKEN,
                ObjectState.MISSING_DEPENDENCY: GraphNodeState.MISSING_DEPENDENCY,
            }

            return state_mapping.get(state, GraphNodeState.ACTIVE)

        except Exception:
            return GraphNodeState.ACTIVE

    def _get_state_metadata(self, state: GraphNodeState) -> Dict[str, Any]:
        """
        Get comprehensive metadata for each state including color, icon, severity.

        Returns:
            Dictionary with visualization and semantic information
        """
        metadata = {
            # Positive states
            GraphNodeState.HEALTHY: {
                "color": "#10b981",
                "severity": "success",
                "icon": "check-circle",
                "description": "Well-balanced and properly integrated",
                "priority": 10,
            },
            GraphNodeState.ACTIVE: {
                "color": "#22c55e",
                "severity": "success",
                "icon": "check",
                "description": "Actively used in infrastructure",
                "priority": 15,
            },
            GraphNodeState.INTEGRATED: {
                "color": "#84cc16",
                "severity": "success",
                "icon": "link",
                "description": "Connected with dependencies and dependents",
                "priority": 20,
            },
            # Neutral/Informational states
            GraphNodeState.INPUT: {
                "color": "#3b82f6",
                "severity": "info",
                "icon": "arrow-down-circle",
                "description": "Provides input to infrastructure",
                "priority": 5,
            },
            GraphNodeState.OUTPUT: {
                "color": "#06b6d4",
                "severity": "info",
                "icon": "arrow-up-circle",
                "description": "Exports values externally",
                "priority": 5,
            },
            GraphNodeState.CONFIGURATION: {
                "color": "#8b5cf6",
                "severity": "info",
                "icon": "settings",
                "description": "System configuration",
                "priority": 5,
            },
            GraphNodeState.EXTERNAL_DATA: {
                "color": "#a855f7",
                "severity": "info",
                "icon": "database",
                "description": "External data source",
                "priority": 5,
            },
            GraphNodeState.LEAF: {
                "color": "#06b6d4",
                "severity": "info",
                "icon": "file",
                "description": "Terminal node with no dependencies",
                "priority": 8,
            },
            GraphNodeState.HUB: {
                "color": "#0ea5e9",
                "severity": "info",
                "icon": "share-2",
                "description": "Highly connected hub node",
                "priority": 12,
            },
            # Warning states
            GraphNodeState.UNUSED: {
                "color": "#f59e0b",
                "severity": "warning",
                "icon": "alert-circle",
                "description": "Declared but never used",
                "priority": 60,
            },
            GraphNodeState.ISOLATED: {
                "color": "#f97316",
                "severity": "warning",
                "icon": "alert-triangle",
                "description": "No connections to infrastructure",
                "priority": 65,
            },
            GraphNodeState.ORPHANED: {
                "color": "#fb923c",
                "severity": "warning",
                "icon": "git-branch",
                "description": "Has dependencies but not used",
                "priority": 70,
            },
            GraphNodeState.UNDERUTILIZED: {
                "color": "#fdba74",
                "severity": "warning",
                "icon": "trending-down",
                "description": "Complex but minimally used",
                "priority": 55,
            },
            GraphNodeState.COMPLEX: {
                "color": "#fb923c",
                "severity": "warning",
                "icon": "git-merge",
                "description": "High complexity, hard to maintain",
                "priority": 75,
            },
            # Error states
            GraphNodeState.INCOMPLETE: {
                "color": "#ef4444",
                "severity": "error",
                "icon": "x-circle",
                "description": "Missing required configuration",
                "priority": 90,
            },
            GraphNodeState.BROKEN: {
                "color": "#dc2626",
                "severity": "error",
                "icon": "alert-octagon",
                "description": "Critical issues detected",
                "priority": 100,
            },
            GraphNodeState.MISSING_DEPENDENCY: {
                "color": "#b91c1c",
                "severity": "error",
                "icon": "link-off",
                "description": "References undefined objects",
                "priority": 95,
            },
        }

        return metadata.get(
            state,
            {
                "color": "#6b7280",
                "severity": "unknown",
                "icon": "help-circle",
                "description": "Unknown state",
                "priority": 50,
            },
        )

    def _determine_subtype(self, obj) -> str:
        """Determine the subtype for display purposes."""
        # For resources and data sources, use the resource_type
        if obj.resource_type:
            return obj.resource_type

        # For variables, format the type nicely
        if obj.type == ResourceType.VARIABLE and obj.variable_type:
            return self._format_terraform_type(obj.variable_type)

        # For providers, use the provider name
        if obj.provider_info:
            return obj.provider_info.provider_name

        # For modules, extract from source if available
        if obj.type == ResourceType.MODULE and obj.source:
            # Extract last part of source path
            source_parts = obj.source.split("/")
            return source_parts[-1] if source_parts else "module"

        # Default to type name
        return obj.type.value

    def _format_terraform_type(self, type_str: str, indent_level: int = 0) -> str:
        """
        Format Terraform type strings for readable display.

        Handles complex types like object(), list(), map() with proper formatting.
        """
        if not isinstance(type_str, str):
            type_str = str(type_str)

        # Remove wrapper syntax
        if type_str.startswith("${") and type_str.endswith("}"):
            type_str = type_str[2:-1]
        if type_str.startswith('"') and type_str.endswith('"'):
            type_str = type_str[1:-1]

        indent = "  " * indent_level
        next_indent = "  " * (indent_level + 1)

        # Handle object types
        if type_str.startswith("object({"):
            body = type_str[len("object(") : -1]
            if body == "{}":
                return "object({})"

            try:
                body_dict = ast.literal_eval(body)
                parts = []
                for key, value in body_dict.items():
                    formatted_value = self._format_terraform_type(
                        value, indent_level + 1
                    )
                    parts.append(f"{next_indent}{key}: {formatted_value}")
                return "object(\n" + ",\n".join(parts) + f"\n{indent})"
            except (ValueError, SyntaxError, TypeError):
                return type_str.replace('"', "")

        # Handle list types
        elif type_str.startswith("list("):
            inner = type_str[len("list(") : -1]
            formatted_inner = self._format_terraform_type(inner, indent_level + 1)
            if "\n" in formatted_inner:
                return f"list(\n{formatted_inner}\n{indent})"
            return f"list({formatted_inner})"

        # Handle map types
        elif type_str.startswith("map("):
            inner = type_str[len("map(") : -1]
            formatted_inner = self._format_terraform_type(inner, indent_level + 1)
            if "\n" in formatted_inner:
                return f"map(\n{formatted_inner}\n{indent})"
            return f"map({formatted_inner})"

        # Handle set types
        elif type_str.startswith("set("):
            inner = type_str[len("set(") : -1]
            formatted_inner = self._format_terraform_type(inner, indent_level + 1)
            if "\n" in formatted_inner:
                return f"set(\n{formatted_inner}\n{indent})"
            return f"set({formatted_inner})"

        # Primitive type
        return type_str.replace('"', "")

    def _generate_statistics(self, project: TerraformProject) -> Dict[str, Any]:
        """Generate comprehensive graph statistics."""
        # Get project statistics
        proj_stats = project.compute_statistics()

        # Count graph-specific metrics
        node_state_counts = {}
        for node in self.nodes:
            state = node.state.value
            node_state_counts[state] = node_state_counts.get(state, 0) + 1

        edge_type_counts = {}
        for edge in self.edges:
            edge_type = edge.type.value
            edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1

        # Calculate connectivity metrics
        avg_deps_out = (
            sum(n.dependencies_out for n in self.nodes) / len(self.nodes)
            if self.nodes
            else 0
        )
        avg_deps_in = (
            sum(n.dependencies_in for n in self.nodes) / len(self.nodes)
            if self.nodes
            else 0
        )

        # Find highly connected nodes (hubs)
        sorted_by_in = sorted(self.nodes, key=lambda n: n.dependencies_in, reverse=True)
        sorted_by_out = sorted(
            self.nodes, key=lambda n: n.dependencies_out, reverse=True
        )

        hubs = []
        for node in sorted_by_in[:5]:  # Top 5 most depended-upon
            if node.dependencies_in > 0:
                hubs.append(
                    {
                        "name": node.label,
                        "type": node.type,
                        "used_by": node.dependencies_in,
                    }
                )

        complex_nodes = []
        for node in sorted_by_out[:5]:  # Top 5 most dependent
            if node.dependencies_out > 0:
                complex_nodes.append(
                    {
                        "name": node.label,
                        "type": node.type,
                        "depends_on": node.dependencies_out,
                    }
                )

        # Calculate health metrics by grouping states by severity
        # Positive states
        healthy_states = [
            GraphNodeState.HEALTHY.value,
            GraphNodeState.ACTIVE.value,
            GraphNodeState.INTEGRATED.value,
        ]
        healthy_count = sum(node_state_counts.get(s, 0) for s in healthy_states)

        # Neutral states
        neutral_states = [
            GraphNodeState.INPUT.value,
            GraphNodeState.OUTPUT.value,
            GraphNodeState.CONFIGURATION.value,
            GraphNodeState.EXTERNAL_DATA.value,
            GraphNodeState.LEAF.value,
            GraphNodeState.HUB.value,
        ]
        neutral_count = sum(node_state_counts.get(s, 0) for s in neutral_states)

        # Warning states
        warning_states = [
            GraphNodeState.UNUSED.value,
            GraphNodeState.ISOLATED.value,
            GraphNodeState.ORPHANED.value,
            GraphNodeState.UNDERUTILIZED.value,
            GraphNodeState.COMPLEX.value,
        ]
        warning_count = sum(node_state_counts.get(s, 0) for s in warning_states)

        # Error states
        error_states = [
            GraphNodeState.INCOMPLETE.value,
            GraphNodeState.BROKEN.value,
            GraphNodeState.MISSING_DEPENDENCY.value,
        ]
        error_count = sum(node_state_counts.get(s, 0) for s in error_states)

        total_nodes = len(self.nodes)
        graph_health = 0.0
        if total_nodes > 0:
            # Health score calculation
            # Base: healthy nodes contribute positively
            graph_health = (healthy_count / total_nodes) * 100
            # Neutral nodes are okay but don't add to health
            # Warnings reduce health moderately
            graph_health -= (warning_count / total_nodes) * 15
            # Errors reduce health significantly
            graph_health -= (error_count / total_nodes) * 30
            graph_health = max(0.0, min(100.0, graph_health))

        return {
            "graph": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "node_states": node_state_counts,
                "edge_types": edge_type_counts,
                "graph_health_score": round(graph_health, 2),
                "severity_counts": {
                    "healthy": healthy_count,
                    "neutral": neutral_count,
                    "warning": warning_count,
                    "error": error_count,
                },
            },
            "connectivity": {
                "avg_dependencies_out": round(avg_deps_out, 2),
                "avg_dependencies_in": round(avg_deps_in, 2),
                "most_used_nodes": hubs,
                "most_complex_nodes": complex_nodes,
            },
            "project": proj_stats.to_dict(),
        }


class GraphLayoutCalculator:
    """
    Calculate layout positions for graph visualization.

    Provides force-directed and hierarchical layout algorithms.
    """

    @staticmethod
    def calculate_force_layout(
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        width: int = 1000,
        height: int = 800,
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate force-directed layout positions.

        Simple implementation - for production use a library like networkx.

        Returns:
            Dictionary mapping node_id to {"x": float, "y": float}
        """
        import math
        import random

        # Initialize random positions
        positions = {}
        for node in nodes:
            positions[node.id] = {
                "x": random.uniform(50, width - 50),
                "y": random.uniform(50, height - 50),
            }

        # Simple force-directed algorithm
        iterations = 100
        k = math.sqrt((width * height) / len(nodes))  # Optimal distance

        for _ in range(iterations):
            # Repulsive forces between all nodes
            forces = {node.id: {"x": 0, "y": 0} for node in nodes}

            for i, node1 in enumerate(nodes):
                for node2 in nodes[i + 1 :]:
                    pos1 = positions[node1.id]
                    pos2 = positions[node2.id]

                    dx = pos1["x"] - pos2["x"]
                    dy = pos1["y"] - pos2["y"]
                    distance = math.sqrt(dx**2 + dy**2) or 1

                    # Repulsive force
                    force = k**2 / distance
                    fx = (dx / distance) * force
                    fy = (dy / distance) * force

                    forces[node1.id]["x"] += fx
                    forces[node1.id]["y"] += fy
                    forces[node2.id]["x"] -= fx
                    forces[node2.id]["y"] -= fy

            # Attractive forces along edges
            for edge in edges:
                pos_source = positions[edge.source]
                pos_target = positions[edge.target]

                dx = pos_target["x"] - pos_source["x"]
                dy = pos_target["y"] - pos_source["y"]
                distance = math.sqrt(dx**2 + dy**2) or 1

                # Attractive force
                force = distance**2 / k
                fx = (dx / distance) * force * edge.strength
                fy = (dy / distance) * force * edge.strength

                forces[edge.source]["x"] += fx
                forces[edge.source]["y"] += fy
                forces[edge.target]["x"] -= fx
                forces[edge.target]["y"] -= fy

            # Apply forces
            for node in nodes:
                positions[node.id]["x"] += forces[node.id]["x"] * 0.1
                positions[node.id]["y"] += forces[node.id]["y"] * 0.1

                # Keep within bounds
                positions[node.id]["x"] = max(
                    50, min(width - 50, positions[node.id]["x"])
                )
                positions[node.id]["y"] = max(
                    50, min(height - 50, positions[node.id]["y"])
                )

        return positions

    @staticmethod
    def calculate_hierarchical_layout(
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        width: int = 1000,
        height: int = 800,
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate hierarchical (layered) layout positions.

        Places nodes in layers based on dependency depth.

        Returns:
            Dictionary mapping node_id to {"x": float, "y": float}
        """
        # Build adjacency list
        adj = {node.id: [] for node in nodes}
        in_degree = {node.id: 0 for node in nodes}

        for edge in edges:
            adj[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Topological sort with layer assignment
        layers = []
        current_layer = [node.id for node in nodes if in_degree[node.id] == 0]

        while current_layer:
            layers.append(current_layer)
            next_layer = []

            for node_id in current_layer:
                for neighbor in adj[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_layer.append(neighbor)

            current_layer = next_layer

        # Handle cycles (nodes with non-zero in-degree)
        remaining = [node.id for node in nodes if in_degree[node.id] > 0]
        if remaining:
            layers.append(remaining)

        # Calculate positions
        positions = {}
        layer_height = height / (len(layers) + 1)

        for layer_idx, layer in enumerate(layers):
            y = layer_height * (layer_idx + 1)
            layer_width = width / (len(layer) + 1)

            for node_idx, node_id in enumerate(layer):
                x = layer_width * (node_idx + 1)
                positions[node_id] = {"x": x, "y": y}

        return positions


def create_graph_from_project(
    project: TerraformProject,
    layout: str = "force",
    width: int = 1000,
    height: int = 800,
) -> Dict[str, Any]:
    """
    Convenience function to create a complete graph with layout.

    Args:
        project: TerraformProject instance
        layout: "force" or "hierarchical"
        width: Canvas width
        height: Canvas height

    Returns:
        Complete graph data with nodes, edges, positions, and statistics
    """
    builder = TerraformGraphBuilder()
    graph_data = builder.build_graph(project)

    # Calculate layout
    calculator = GraphLayoutCalculator()
    if layout == "hierarchical":
        positions = calculator.calculate_hierarchical_layout(
            builder.nodes, builder.edges, width, height
        )
    else:
        positions = calculator.calculate_force_layout(
            builder.nodes, builder.edges, width, height
        )

    # Add positions to nodes
    for node_dict in graph_data["nodes"]:
        node_id = node_dict["id"]
        if node_id in positions:
            node_dict["x"] = positions[node_id]["x"]
            node_dict["y"] = positions[node_id]["y"]

    return graph_data
