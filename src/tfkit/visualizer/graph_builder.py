"""
Optimized and production-ready graph data builder for Terraform projects.
This module builds dependency graphs with clear node states and relationships.
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class NodeType(Enum):
    """Node types in the Terraform dependency graph."""

    RESOURCE = "resource"
    DATA = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    LOCAL = "local"
    TERRAFORM = "terraform"


class NodeState(Enum):
    """
    Node health states with clear definitions.

    HEALTHY: Node is properly connected and functioning as expected
    UNUSED: Node exists but is not referenced by any other nodes
    LEAF: Node is used by others but doesn't depend on anything (terminal node)
    ORPHAN: Node has dependencies but nothing uses it (potential waste)
    EXTERNAL: Node serves as an interface to external systems
    WARNING: Node has unexpected or problematic connection patterns
    """

    HEALTHY = "healthy"
    UNUSED = "unused"
    LEAF = "leaf"
    ORPHAN = "orphan"
    EXTERNAL = "external"
    WARNING = "warning"


class EdgeType(Enum):
    """Types of edges in the dependency graph."""

    DEPENDENCY = "dependency"  # Explicit depends_on or implicit reference
    REFERENCE = "reference"  # Variable or output reference
    SOURCE = "source"  # Module source reference
    PROVIDER_USE = "provider_use"  # Resource uses provider


@dataclass
class GraphNode:
    """Represents a node in the Terraform dependency graph."""

    id: int
    label: str
    type: NodeType
    subtype: str
    state: NodeState
    state_reason: str
    dependencies_out: int = 0
    dependencies_in: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type.value,
            "subtype": self.subtype,
            "state": self.state.value,
            "state_reason": self.state_reason,
            "dependencies_out": self.dependencies_out,
            "dependencies_in": self.dependencies_in,
            "details": self.details,
        }


@dataclass
class GraphEdge:
    """Represents an edge in the Terraform dependency graph."""

    source: int
    target: int
    type: EdgeType
    strength: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary for serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "strength": self.strength,
        }


class TerraformGraphBuilder:
    """
    Builds dependency graphs from Terraform project data.

    This builder creates a comprehensive graph representation of all Terraform
    objects and their relationships, with clear node states and edge types.
    """

    # Edge strength constants (0.0 to 1.0)
    STRENGTH_EXPLICIT_DEPENDENCY = 1.0  # depends_on or direct resource reference
    STRENGTH_DATA_SOURCE = 0.9  # Data source dependencies
    STRENGTH_MODULE_DEPENDENCY = 0.8  # Module dependencies
    STRENGTH_VARIABLE_REFERENCE = 0.7  # Variable/output references
    STRENGTH_PROVIDER_USE = 0.6  # Provider usage
    STRENGTH_SOURCE_REFERENCE = 0.5  # Module source reference

    def __init__(self):
        """Initialize the graph builder."""
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.node_map: Dict[str, int] = {}  # label -> node_id
        self.next_node_id: int = 0

    def build_graph(self, project_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a complete dependency graph from project data.

        Args:
            project_dict: Dictionary containing all Terraform project objects

        Returns:
            Dictionary with 'nodes', 'edges', and 'statistics' keys
        """
        # Reset state
        self.nodes = []
        self.edges = []
        self.node_map = {}
        self.next_node_id = 0

        # Phase 1: Create all nodes
        self._create_nodes(project_dict)

        # Phase 2: Create all edges
        self._create_edges(project_dict)

        # Phase 3: Calculate node states
        self._calculate_node_states()

        # Phase 4: Generate statistics
        statistics = self._generate_statistics()

        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "statistics": statistics,
        }

    def _create_nodes(self, project_dict: Dict[str, Any]) -> None:
        """Create all nodes from project data."""
        # Resources
        for res_name, res_data in project_dict.get("resources", {}).items():
            full_resource_type = res_data.get(
                "resource_type", self._extract_type_value(res_data.get("type"))
            )
            provider_prefix = self._get_provider_prefix(full_resource_type)
            details = self._sanitize_details(res_data)
            # Ensure full resource type is in details, as subtype is now just the prefix
            details["full_resource_type"] = full_resource_type

            self._add_node(
                label=res_name,
                node_type=NodeType.RESOURCE,
                subtype=provider_prefix,
                details=details,
            )

        # Data sources
        for data_name, data_data in project_dict.get("data_sources", {}).items():
            full_data_type = data_data.get(
                "resource_type", self._extract_type_value(data_data.get("type"))
            )
            provider_prefix = self._get_provider_prefix(full_data_type)
            details = self._sanitize_details(data_data)
            # Ensure full data type is in details, as subtype is now just the prefix
            details["full_data_type"] = full_data_type

            self._add_node(
                label=data_name,
                node_type=NodeType.DATA,
                subtype=provider_prefix,
                details=details,
            )

        # Modules
        for mod_name, mod_data in project_dict.get("modules", {}).items():
            self._add_node(
                label=mod_name,
                node_type=NodeType.MODULE,
                subtype="module",
                details=self._sanitize_details(mod_data),
            )

        # Variables
        for var_name, var_data in project_dict.get("variables", {}).items():
            # Extract the raw type string
            raw_var_type = self._extract_type_value(
                var_data.get("variable_type", "any")
            )
            # Format the type string for pretty display
            formatted_var_type = self._format_tf_type_string(raw_var_type)

            self._add_node(
                label=var_name,
                node_type=NodeType.VARIABLE,
                subtype=formatted_var_type,  # Use the formatted type
                details=self._sanitize_details(var_data),
            )

        # Outputs
        for out_name, out_data in project_dict.get("outputs", {}).items():
            self._add_node(
                label=out_name,
                node_type=NodeType.OUTPUT,
                subtype="output",
                details=self._sanitize_details(out_data),
            )

        # Providers
        for provider_name, provider_data in project_dict.get("providers", {}).items():
            provider_subtype = self._extract_type_value(
                provider_data.get("name", "unknown")
            )
            self._add_node(
                label=provider_name,
                node_type=NodeType.PROVIDER,
                subtype=provider_subtype,
                details=self._sanitize_details(provider_data),
            )

        # Locals
        for local_name, local_data in project_dict.get("locals", {}).items():
            self._add_node(
                label=local_name,
                node_type=NodeType.LOCAL,
                subtype="local",
                details=self._sanitize_details(local_data),
            )

        # Terraform blocks
        for tf_name, tf_data in project_dict.get("terraform_blocks", {}).items():
            self._add_node(
                label=tf_name,
                node_type=NodeType.TERRAFORM,
                subtype="terraform",
                details=self._sanitize_details(tf_data),
            )

    def _create_edges(self, project_dict: Dict[str, Any]) -> None:
        """Create all edges from project data."""
        # Resource dependencies
        for res_name, res_data in project_dict.get("resources", {}).items():
            dependencies = res_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    self._add_edge(
                        source=res_name,
                        target=dep,
                        edge_type=EdgeType.DEPENDENCY,
                        strength=self.STRENGTH_EXPLICIT_DEPENDENCY,
                    )

            # Provider usage
            provider = res_data.get("provider")
            if provider:
                # Try to find provider node
                provider_node = self._find_provider_node(provider)
                if provider_node:
                    self._add_edge(
                        source=res_name,
                        target=provider_node,
                        edge_type=EdgeType.PROVIDER_USE,
                        strength=self.STRENGTH_PROVIDER_USE,
                    )

        # Data source dependencies
        for data_name, data_data in project_dict.get("data_sources", {}).items():
            dependencies = data_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    self._add_edge(
                        source=data_name,
                        target=dep,
                        edge_type=EdgeType.DEPENDENCY,
                        strength=self.STRENGTH_DATA_SOURCE,
                    )

        # Module dependencies
        for mod_name, mod_data in project_dict.get("modules", {}).items():
            dependencies = mod_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    self._add_edge(
                        source=mod_name,
                        target=dep,
                        edge_type=EdgeType.DEPENDENCY,
                        strength=self.STRENGTH_MODULE_DEPENDENCY,
                    )

        # Output references
        for out_name, out_data in project_dict.get("outputs", {}).items():
            dependencies = out_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    self._add_edge(
                        source=out_name,
                        target=dep,
                        edge_type=EdgeType.REFERENCE,
                        strength=self.STRENGTH_VARIABLE_REFERENCE,
                    )

        # Local dependencies
        for local_name, local_data in project_dict.get("locals", {}).items():
            dependencies = local_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    self._add_edge(
                        source=local_name,
                        target=dep,
                        edge_type=EdgeType.REFERENCE,
                        strength=self.STRENGTH_VARIABLE_REFERENCE,
                    )

    def _calculate_node_states(self) -> None:
        """
        Calculate the state of each node based on its connections.

        Node states are determined by the pattern of incoming and outgoing edges,
        combined with the node type. This provides semantic meaning to each node's
        role in the infrastructure.
        """
        for node in self.nodes:
            node.state, node.state_reason = self._determine_node_state(node)

    def _determine_node_state(self, node: GraphNode) -> Tuple[NodeState, str]:
        """
        Determine the state and reason for a single node.

        Returns:
            Tuple of (NodeState, reason_string)
        """
        out_count = node.dependencies_out
        in_count = node.dependencies_in

        # Output nodes - exported values
        if node.type == NodeType.OUTPUT:
            if in_count == 0:
                return NodeState.WARNING, "Output has no value source"
            elif out_count == 0:
                return NodeState.EXTERNAL, "Output exported for external consumption"
            else:
                return NodeState.WARNING, "Output with unexpected outgoing dependencies"

        # Provider nodes - configuration
        elif node.type == NodeType.PROVIDER:
            if in_count == 0 and out_count == 0:
                return (
                    NodeState.UNUSED,
                    "Provider configured but not used by any resources",
                )
            elif in_count > 0:
                return NodeState.HEALTHY, f"Provider used by {in_count} resource(s)"
            else:
                return NodeState.WARNING, "Provider with unexpected dependency pattern"

        # Variable nodes - inputs
        elif node.type == NodeType.VARIABLE:
            if in_count == 0:
                return NodeState.UNUSED, "Variable declared but never referenced"
            elif out_count == 0:
                return NodeState.HEALTHY, f"Variable referenced by {in_count} object(s)"
            else:
                return (
                    NodeState.WARNING,
                    "Variable with unexpected outgoing dependencies",
                )

        # Local nodes - computed values
        elif node.type == NodeType.LOCAL:
            if in_count == 0:
                return NodeState.UNUSED, "Local value declared but never referenced"
            elif out_count > 0 and in_count > 0:
                return NodeState.HEALTHY, "Local value computing and providing data"
            elif out_count == 0 and in_count > 0:
                return (
                    NodeState.LEAF,
                    "Local value with no dependencies (literal value)",
                )
            # Corrected logic for orphan local (has dependencies, not used)
            elif out_count > 0 and in_count == 0:
                return NodeState.ORPHAN, "Local value is calculated but never used"
            else:
                return NodeState.WARNING, "Local with unexpected dependency pattern"

        # Resource nodes - infrastructure components
        elif node.type == NodeType.RESOURCE:
            if in_count == 0 and out_count == 0:
                return (
                    NodeState.UNUSED,
                    "Resource not connected to any other infrastructure",
                )
            elif in_count > 0 and out_count > 0:
                return (
                    NodeState.HEALTHY,
                    f"Resource with {out_count} dep(s), used by {in_count} object(s)",
                )
            elif in_count > 0 and out_count == 0:
                return NodeState.LEAF, "Leaf resource (no dependencies, used by others)"
            elif in_count == 0 and out_count > 0:
                return (
                    NodeState.ORPHAN,
                    f"Resource with {out_count} dep(s) but not used by others",
                )
            else:
                return NodeState.WARNING, "Resource with unexpected dependency pattern"

        # Module nodes - composition units
        elif node.type == NodeType.MODULE:
            if in_count == 0 and out_count == 0:
                return NodeState.UNUSED, "Module declared but not integrated"
            elif in_count > 0 and out_count > 0:
                return (
                    NodeState.HEALTHY,
                    f"Module with {out_count} dep(s), used by {in_count} object(s)",
                )
            elif in_count > 0 and out_count == 0:
                return NodeState.LEAF, "Leaf module (no dependencies)"
            elif in_count == 0 and out_count > 0:
                return NodeState.ORPHAN, f"Module with {out_count} dep(s) but not used"
            else:
                return NodeState.WARNING, "Module with unexpected dependency pattern"

        # Data source nodes - external data
        elif node.type == NodeType.DATA:
            if in_count == 0 and out_count == 0:
                return NodeState.UNUSED, "Data source declared but never referenced"
            elif in_count > 0 and out_count >= 0:
                return (
                    NodeState.HEALTHY,
                    f"Data source providing data to {in_count} object(s)",
                )
            else:
                return (
                    NodeState.WARNING,
                    "Data source with unexpected dependency pattern",
                )

        # Terraform block nodes - configuration
        elif node.type == NodeType.TERRAFORM:
            return NodeState.EXTERNAL, "Terraform configuration block"

        # Default fallback
        return (
            NodeState.WARNING,
            f"Unknown node pattern: in={in_count}, out={out_count}",
        )

    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive statistics about the graph."""
        state_counts = {state.value: 0 for state in NodeState}
        type_counts = {node_type.value: 0 for node_type in NodeType}
        edge_type_counts = {edge_type.value: 0 for edge_type in EdgeType}

        for node in self.nodes:
            state_counts[node.state.value] += 1
            type_counts[node.type.value] += 1

        for edge in self.edges:
            edge_type_counts[edge.type.value] += 1

        # Calculate health metrics
        total_nodes = len(self.nodes)
        healthy_nodes = state_counts[NodeState.HEALTHY.value]
        unused_nodes = state_counts[NodeState.UNUSED.value]
        warning_nodes = state_counts[NodeState.WARNING.value]

        health_score = 0.0
        if total_nodes > 0:
            # Health score: 100% for all healthy, -10% per unused, -5% per warning
            health_score = (healthy_nodes / total_nodes) * 100
            health_score -= (unused_nodes / total_nodes) * 10
            health_score -= (warning_nodes / total_nodes) * 5
            health_score = max(0.0, min(100.0, health_score))

        return {
            "node_count": total_nodes,
            "edge_count": len(self.edges),
            "state_distribution": state_counts,
            "type_distribution": type_counts,
            "edge_type_distribution": edge_type_counts,
            "health_score": round(health_score, 2),
            "metrics": {
                "healthy_percentage": round((healthy_nodes / total_nodes * 100), 2)
                if total_nodes > 0
                else 0,
                "unused_percentage": round((unused_nodes / total_nodes * 100), 2)
                if total_nodes > 0
                else 0,
                "warning_percentage": round((warning_nodes / total_nodes * 100), 2)
                if total_nodes > 0
                else 0,
            },
        }

    def _add_node(
        self,
        label: str,
        node_type: NodeType,
        subtype: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        """
        Add a node to the graph.

        Args:
            label: Unique identifier for the node
            node_type: Type of the node
            subtype: Specific subtype (e.g., resource type)
            details: Additional node metadata

        Returns:
            The created GraphNode
        """
        node = GraphNode(
            id=self.next_node_id,
            label=label,
            type=node_type,
            subtype=subtype,
            state=NodeState.HEALTHY,  # Will be calculated later
            state_reason="Pending calculation",
            details=details or {},
        )

        self.nodes.append(node)
        self.node_map[label] = self.next_node_id
        self.next_node_id += 1

        return node

    def _add_edge(
        self, source: str, target: str, edge_type: EdgeType, strength: float
    ) -> bool:
        """
        Add an edge between two nodes.

        Args:
            source: Source node label
            target: Target node label
            edge_type: Type of the edge
            strength: Edge strength (0.0 to 1.0)

        Returns:
            True if edge was added, False if nodes don't exist
        """
        if source not in self.node_map or target not in self.node_map:
            return False

        source_id = self.node_map[source]
        target_id = self.node_map[target]

        edge = GraphEdge(
            source=source_id, target=target_id, type=edge_type, strength=strength
        )

        self.edges.append(edge)

        # Update dependency counts
        self.nodes[source_id].dependencies_out += 1
        self.nodes[target_id].dependencies_in += 1

        return True

    def _get_provider_prefix(self, resource_type_str: str) -> str:
        """
        Extracts the provider prefix (e.g., 'aws') from a resource type string.

        Examples:
            "aws_instance" -> "aws"
            "tfe_workspace" -> "tfe"
            "local_file" -> "local"

        Args:
            resource_type_str: The full resource type string.

        Returns:
            The extracted prefix, or 'unknown' if input is invalid.
        """
        if not isinstance(resource_type_str, str) or not resource_type_str:
            return "unknown"

        parts = resource_type_str.split("_")
        if parts:
            return parts[0]

        return "unknown"

    def _find_provider_node(self, provider: str) -> Optional[str]:
        """
        Find a provider node by name or alias.

        Args:
            provider: Provider name or reference

        Returns:
            Provider node label if found, None otherwise
        """
        # Direct match
        if provider in self.node_map:
            return provider

        # Try with "provider." prefix
        provider_key = f"provider.{provider}"
        if provider_key in self.node_map:
            return provider_key

        # Search through nodes for alias match
        for node in self.nodes:
            if node.type == NodeType.PROVIDER:
                node_provider = node.details.get("name", "")
                node_alias = node.details.get("alias", "")

                if node_provider == provider or node_alias == provider:
                    return node.label

        return None

    def _format_tf_type_string(self, type_str: str, indent_level: int = 0) -> str:
        """Recursively formats a Terraform type string for readability."""
        if not isinstance(type_str, str):
            type_str = str(type_str)

        indent = "  " * indent_level
        next_indent = "  " * (indent_level + 1)

        # 1. Clean up wrappers
        original_str = type_str
        if type_str.startswith("${") and type_str.endswith("}"):
            type_str = type_str[2:-1]
        if type_str.startswith('"') and type_str.endswith('"'):
            type_str = type_str[1:-1]
        # Handle potential double-wrapping
        if type_str.startswith("${") and type_str.endswith("}"):
            type_str = type_str[2:-1]

        # 2. Check type
        if type_str.startswith("object({"):
            body_str = type_str[len("object(") : -1]  # get {...}
            if body_str == "{}":
                return "object({})"

            try:
                # Use ast.literal_eval for safe parsing of the dict string
                body_dict = ast.literal_eval(body_str)
                parts = []
                for k, v in body_dict.items():
                    # Recursively format the value
                    formatted_v = self._format_tf_type_string(v, indent_level + 1)
                    parts.append(f"{next_indent}{k}: {formatted_v}")
                return f"object(\n" + ",\n".join(parts) + f"\n{indent})"
            except (ValueError, SyntaxError, TypeError):
                # Fallback for unparseable strings (e.g., "any")
                return original_str.replace('"', "")

        elif type_str.startswith("list("):
            inner = type_str[len("list(") : -1]
            formatted_inner = self._format_tf_type_string(inner, indent_level + 1)
            # Add newlines if the inner type is complex (is multi-line)
            if "\n" in formatted_inner:
                return f"list(\n{formatted_inner}\n{indent})"
            else:
                return f"list({formatted_inner})"

        elif type_str.startswith("map("):
            inner = type_str[len("map(") : -1]
            formatted_inner = self._format_tf_type_string(inner, indent_level + 1)
            # Add newlines if the inner type is complex (is multi-line)
            if "\n" in formatted_inner:
                return f"map(\n{formatted_inner}\n{indent})"
            else:
                return f"map({formatted_inner})"

        # Primitive type
        return type_str.replace('"', "")  # "string" -> string

    def _extract_type_value(self, type_obj: Any) -> str:
        """
        Extract string value from a type object.

        Args:
            type_obj: Type object (could be Enum, string, etc.)

        Returns:
            String representation of the type
        """
        if type_obj is None:
            return "unknown"

        if hasattr(type_obj, "value"):
            return str(type_obj.value)

        if hasattr(type_obj, "name"):
            return str(type_obj.name)

        return str(type_obj)

    def _sanitize_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize node details to include only serializable data.

        Args:
            data: Raw data dictionary

        Returns:
            Sanitized dictionary with safe values
        """
        safe_keys = {
            "name",
            "resource_type",
            "provider",
            "source",
            "file_path",
            "line_number",
            "description",
            "variable_type",
            "sensitive",
            "alias",
        }

        sanitized = {}
        for key in safe_keys:
            if key in data:
                value = data[key]
                # Convert Enum to string
                if hasattr(value, "value"):
                    sanitized[key] = value.value
                elif hasattr(value, "name"):
                    sanitized[key] = value.name
                else:
                    sanitized[key] = value

        return sanitized
