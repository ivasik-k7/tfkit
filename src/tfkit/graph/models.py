from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(Enum):
    """Enumeration of Terraform resource types."""

    DATA = "data"
    RESOURCE = "resource"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    LOCAL = "local"
    TERRAFORM = "terraform"


class NodeState(Enum):
    """Describes how a Terraform node relates to others in the dependency graph."""

    # Core relationship categories
    ACTIVE = "active"  # Actively used and connected in the dependency graph
    UNUSED = "unused"  # Defined but not referenced or utilized
    EXTERNAL = "external"  # Imported from outside the managed Terraform state
    ORPHAN = "orphan"  # Exists without dependencies or dependents
    LEAF = "leaf"  # No children; depends on others but not depended upon
    HUB = "hub"  # Central node with multiple dependencies and dependents
    CONFIGURATION = "configuration"  # Defines or modifies settings for other nodes
    DEPENDENCY = "dependency"  # Serves as a prerequisite for other nodes
    INVALID = "invalid"  # Broken or inconsistent reference

    # Extended relationship states
    TRANSIENT = "transient"  # Temporary/intermediate node used during provisioning
    EPHEMERAL = "ephemeral"  # Exists only during runtime or execution (e.g., locals)
    SHARED = "shared"  # Referenced by multiple nodes (common dependency)
    AGGREGATOR = "aggregator"  # Combines multiple inputs into a single output (e.g., module output collector)
    BRIDGE = "bridge"  # Connects distinct parts of the graph (e.g., output → variable mapping)
    DERIVED = "derived"  # Computed or generated based on other nodes (e.g., locals or calculated variables)

    # Node that depends heavily on configuration inputs
    CONFIG_CONSUMER = "config_consumer"
    # Node that exports configuration for others to use
    CONFIG_PROVIDER = "config_provider"

    OBSOLETE = "obsolete"  # Was previously active but now superseded or deprecated
    STALE = "stale"  # Present in the state file but no longer in configuration
    UNRESOLVED = "unresolved"  # Exists but references undefined or missing nodes
    UNKNOWN = "unknown"

    def is_config_related(self) -> bool:
        """Returns True if the relation type involves configuration logic."""
        return self in {
            NodeState.CONFIGURATION,
            NodeState.CONFIG_CONSUMER,
            NodeState.CONFIG_PROVIDER,
        }

    def is_structural(self) -> bool:
        """Returns True if the node influences overall dependency graph structure."""
        return self in {NodeState.HUB, NodeState.BRIDGE, NodeState.AGGREGATOR}

    def is_temporary(self) -> bool:
        """Returns True if the node exists only during execution or transient stages."""
        return self in {NodeState.TRANSIENT, NodeState.EPHEMERAL}

    def is_inactive(self) -> bool:
        """Returns True if the node is not currently contributing to the active graph."""
        return self in {
            NodeState.UNUSED,
            NodeState.OBSOLETE,
            NodeState.STALE,
            NodeState.ORPHAN,
            NodeState.INVALID,
            NodeState.UNRESOLVED,
        }


class LinkType(Enum):
    """Types of relationships between nodes in the dependency graph."""

    DIRECT = "direct"
    IMPLICIT = "implicit"
    EXPLICIT = "explicit"  # Explicit depends_on
    PROVIDER_CONFIG = "provider_config"
    PROVIDER_RELATIONSHIP = "provider_relationship"  # Provider-to-provider
    MODULE_CALL = "module_call"
    LIFECYCLE = "lifecycle"
    CONFIGURATION = "configuration"  # Variable usage
    EXPORT = "export"  # Output exports
    DATA_REFERENCE = "data_reference"  # Data source references


@dataclass
class NodeData:
    """Enhanced metadata for graph nodes."""

    provider: Optional[str] = None
    module_path: Optional[List[str]] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    depends_on: List[str] = field(default_factory=list)
    count: Optional[int] = None
    for_each: Optional[Dict[str, Any]] = None
    lifecycle_rules: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)
    state: NodeState = NodeState.UNKNOWN
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """Enhanced Node representation with comprehensive metadata."""

    id: str
    name: str
    type: NodeType
    data: NodeData
    position: Optional[Dict[str, float]] = None
    group: Optional[str] = None
    weight: float = 1.0
    visibility: bool = True
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Link:
    """Represents a relationship between two nodes in the dependency graph."""

    source: str
    target: str
    link_type: LinkType = LinkType.IMPLICIT
    strength: float = 1.0
    reference_path: Optional[List[str]] = None
    # is_explicit: bool = False
    # is_circular: bool = False
    # metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphData:
    """Complete dependency graph representation."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    links: List[Link] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_link(self, link: Link) -> None:
        """Add a link to the graph."""
        self.links.append(link)

    def get_node_links(self, node_id: str) -> List[Link]:
        """Get all links connected to a specific node."""
        return [
            link
            for link in self.links
            if link.source == node_id or link.target == node_id
        ]

    def get_adjacent_nodes(self, node_id: str) -> List[Node]:
        """Get all nodes adjacent to the specified node."""
        adjacent_nodes = []
        for link in self.links:
            if link.source == node_id:
                adjacent_nodes.append(self.nodes[link.target])
            elif link.target == node_id:
                adjacent_nodes.append(self.nodes[link.source])
        return adjacent_nodes
