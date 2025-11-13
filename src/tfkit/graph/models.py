from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(Enum):
    DATA = "data"
    RESOURCE = "resource"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    PROVIDER = "provider"
    LOCAL = "local"
    TERRAFORM = "terraform"


class NodeState(Enum):
    ACTIVE = "active"
    UNUSED = "unused"
    EXTERNAL = "external"
    ORPHAN = "orphan"
    LEAF = "leaf"
    HUB = "hub"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    INVALID = "invalid"
    TRANSIENT = "transient"
    EPHEMERAL = "ephemeral"
    SHARED = "shared"
    AGGREGATOR = "aggregator"
    BRIDGE = "bridge"
    DERIVED = "derived"
    CONFIG_CONSUMER = "config_consumer"
    CONFIG_PROVIDER = "config_provider"
    OBSOLETE = "obsolete"
    STALE = "stale"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"

    def is_config_related(self) -> bool:
        return self in {
            NodeState.CONFIGURATION,
            NodeState.CONFIG_CONSUMER,
            NodeState.CONFIG_PROVIDER,
        }

    def is_structural(self) -> bool:
        return self in {NodeState.HUB, NodeState.BRIDGE, NodeState.AGGREGATOR}

    def is_temporary(self) -> bool:
        return self in {NodeState.TRANSIENT, NodeState.EPHEMERAL}

    def is_inactive(self) -> bool:
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
    EXPLICIT = "explicit"
    PROVIDER_CONFIG = "provider_config"
    PROVIDER_RELATIONSHIP = "provider_relationship"
    MODULE_CALL = "module_call"
    LIFECYCLE = "lifecycle"
    CONFIGURATION = "configuration"
    EXPORT = "export"
    DATA_REFERENCE = "data_reference"


@dataclass
class NodeData:
    """Data for graph nodes."""

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
    dependency_count: int = 0
    reference_count: int = 0
    resource_type: Optional[str] = None


@dataclass
class Node:
    id: str
    name: str
    type: NodeType
    data: NodeData
    position: Optional[Dict[str, float]] = None
    group: Optional[str] = None
    weight: float = 1.0
    visibility: bool = True


@dataclass
class Link:
    """Represents a relationship between two nodes in the dependency graph."""

    source: str
    target: str
    link_type: LinkType = LinkType.IMPLICIT
    strength: float = 1.0
    reference_path: Optional[List[str]] = None


@dataclass
class GraphData:
    nodes: Dict[str, Node] = field(default_factory=dict)
    links: List[Link] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_link(self, link: Link) -> None:
        self.links.append(link)

    def get_node_links(self, node_id: str) -> List[Link]:
        return [
            link
            for link in self.links
            if link.source == node_id or link.target == node_id
        ]

    def get_adjacent_nodes(self, node_id: str) -> List[Node]:
        adjacent_nodes = []
        for link in self.links:
            if link.source == node_id:
                adjacent_nodes.append(self.nodes[link.target])
            elif link.target == node_id:
                adjacent_nodes.append(self.nodes[link.source])
        return adjacent_nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type.value,
                    "group": node.group,
                    "weight": node.weight,
                    "visibility": node.visibility,
                    "position": node.position,
                    "data": {
                        "provider": node.data.provider,
                        "module_path": node.data.module_path,
                        "source_file": node.data.source_file,
                        "line_number": node.data.line_number,
                        "depends_on": node.data.depends_on,
                        "count": node.data.count,
                        "for_each": node.data.for_each,
                        "lifecycle_rules": node.data.lifecycle_rules,
                        "tags": node.data.tags,
                        "state": node.data.state.value,
                        "attributes": node.data.attributes,
                        "dependency_count": node.data.dependency_count,
                        "reference_count": node.data.reference_count,
                        "resource_type": node.data.resource_type,
                    },
                }
                for node in self.nodes.values()
            ],
            "links": [
                {
                    "source": link.source,
                    "target": link.target,
                    "link_type": link.link_type.value,
                    "strength": link.strength,
                    "reference_path": link.reference_path,
                }
                for link in self.links
            ],
        }
