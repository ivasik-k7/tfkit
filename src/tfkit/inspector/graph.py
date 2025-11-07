from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(Enum):
    """Types of nodes in the Terraform graph."""

    RESOURCE = "resource"
    DATA_SOURCE = "data_source"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    LOCAL = "local"
    PROVIDER = "provider"
    TERRAFORM = "terraform"


class EdgeType(Enum):
    """Types of relationships between nodes."""

    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    PROVIDES = "provides"  # Provider provides resources
    USES = "uses"  # Resource uses provider
    CONTAINS = "contains"  # Module contains resources
    OUTPUTS = "outputs"  # Module/output provides value
    CONFIGURES = "configures"  # Terraform block configures providers


class NodeStatus(Enum):
    """Status of a node in the graph."""

    PENDING = "pending"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ERROR = "error"
    CIRCULAR = "circular"


@dataclass
class GraphNode:
    """Represents a node in the Terraform graph."""

    id: str  # Unique identifier (Terraform address)
    node_type: NodeType
    label: str  # Human-readable label
    data: Dict[str, Any] = field(default_factory=dict)  # Original block data
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    # Graph properties
    status: NodeStatus = NodeStatus.PENDING
    depth: int = 0  # Depth in dependency graph
    complexity: int = 0  # Resolution complexity score

    # Position for visualization (optional)
    x: Optional[float] = None
    y: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "label": self.label,
            "status": self.status.value,
            "depth": self.depth,
            "complexity": self.complexity,
            "data": self.data,
            "metadata": self.metadata,
            "position": {"x": self.x, "y": self.y}
            if self.x is not None and self.y is not None
            else None,
        }


@dataclass
class GraphEdge:
    """Represents a relationship between nodes."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0  # Strength of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)  # Reference details, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class TerraformGraph:
    """Complete graph representation of a Terraform module."""

    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    # Indexes for fast lookup
    _edges_by_source: Dict[str, List[GraphEdge]] = field(
        default_factory=dict, repr=False
    )
    _edges_by_target: Dict[str, List[GraphEdge]] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self):
        self._rebuild_indexes()

    def _rebuild_indexes(self):
        """Rebuild edge indexes for fast lookups."""
        self._edges_by_source.clear()
        self._edges_by_target.clear()

        for edge in self.edges:
            if edge.source_id not in self._edges_by_source:
                self._edges_by_source[edge.source_id] = []
            self._edges_by_source[edge.source_id].append(edge)

            if edge.target_id not in self._edges_by_target:
                self._edges_by_target[edge.target_id] = []
            self._edges_by_target[edge.target_id].append(edge)

    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        self._rebuild_indexes()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> List[GraphEdge]:
        """Get all edges originating from a node."""
        return self._edges_by_source.get(node_id, [])

    def get_edges_to(self, node_id: str) -> List[GraphEdge]:
        """Get all edges pointing to a node."""
        return self._edges_by_target.get(node_id, [])

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """Get all neighboring nodes (both incoming and outgoing)."""
        neighbors = set()

        # Outgoing edges
        for edge in self.get_edges_from(node_id):
            neighbors.add(edge.target_id)

        # Incoming edges
        for edge in self.get_edges_to(node_id):
            neighbors.add(edge.source_id)

        return [self.nodes[node_id] for node_id in neighbors if node_id in self.nodes]

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "summary": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": {
                    nt.value: sum(1 for n in self.nodes.values() if n.node_type == nt)
                    for nt in NodeType
                },
            },
        }
