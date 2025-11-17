from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from tfkit.graph.models import LinkType, NodeState, NodeType


def _to_serializable(data: Any) -> Any:
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if isinstance(k, (Tuple, LinkType, NodeState, NodeType)):
                key_str = str(k.value) if isinstance(k, Enum) else "_".join(map(str, k))
                new_dict[key_str] = _to_serializable(v)
            elif isinstance(k, Enum):
                new_dict[k.value] = _to_serializable(v)
            else:
                new_dict[k] = _to_serializable(v)
        return new_dict
    elif isinstance(data, (list, tuple, set)):
        return [_to_serializable(item) for item in data]
    elif hasattr(data, "to_dict"):
        return data.to_dict()
    else:
        try:
            return asdict(data)
        except TypeError:
            return str(data)


class ComplexityLevel(Enum):
    """Node complexity classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComponentType(Enum):
    """Graph component classification"""

    ISOLATED = "isolated"
    LINEAR = "linear"
    CYCLIC = "cyclic"
    TREE = "tree"
    COMPLEX = "complex"


@dataclass
class NodeMetrics:
    """Comprehensive metrics for a single node"""

    node_id: str
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    pagerank: float = 0.0
    clustering_coefficient: float = 0.0
    depth_from_root: Optional[int] = None
    height_to_leaf: Optional[int] = None
    complexity_level: ComplexityLevel = ComplexityLevel.LOW
    is_critical: bool = False
    is_bottleneck: bool = False
    shortest_paths_count: int = 0
    dependency_chain_length: int = 0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["complexity_level"] = self.complexity_level.value
        return data


@dataclass
class PathMetrics:
    """Metrics for dependency paths"""

    path: List[str]
    length: int
    total_weight: float = 0.0
    risk_score: float = 0.0
    node_types: List[NodeType] = field(default_factory=list)
    link_types: List[LinkType] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["node_types"] = [t.value for t in self.node_types]
        data["link_types"] = [t.value for t in self.link_types]
        return data


@dataclass
class ComponentMetrics:
    """Metrics for graph components"""

    component_id: int
    node_ids: Set[str]
    size: int
    density: float = 0.0
    diameter: int = 0
    average_path_length: float = 0.0
    component_type: ComponentType = ComponentType.COMPLEX
    is_strongly_connected: bool = False
    entry_points: Set[str] = field(default_factory=set)
    exit_points: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["component_type"] = self.component_type.value
        data["node_ids"] = list(self.node_ids)
        data["entry_points"] = list(self.entry_points)
        data["exit_points"] = list(self.exit_points)
        return data


@dataclass
class ClusterMetrics:
    """Metrics for node clusters"""

    cluster_id: int
    node_ids: Set[str]
    cohesion: float = 0.0
    separation: float = 0.0
    silhouette_score: float = 0.0
    dominant_type: Optional[NodeType] = None
    dominant_provider: Optional[str] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["node_ids"] = list(self.node_ids)
        if self.dominant_type:
            data["dominant_type"] = self.dominant_type.value
        return data


@dataclass
class GraphAnalytics:
    """Complete graph analytics results"""

    # Basic statistics
    total_nodes: int = 0
    total_edges: int = 0
    total_components: int = 0

    # Type and state distributions
    type_distribution: Dict[NodeType, int] = field(default_factory=dict)
    state_distribution: Dict[NodeState, int] = field(default_factory=dict)
    link_type_distribution: Dict[LinkType, int] = field(default_factory=dict)

    # Connectivity metrics
    avg_in_degree: float = 0.0
    avg_out_degree: float = 0.0
    max_in_degree: int = 0
    max_out_degree: int = 0
    graph_density: float = 0.0

    # Structural metrics
    diameter: int = 0
    avg_path_length: float = 0.0
    avg_clustering_coefficient: float = 0.0
    modularity: float = 0.0

    # Complexity metrics
    cyclomatic_complexity: int = 0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    maintainability_index: float = 0.0

    # Node analytics
    node_metrics: Dict[str, NodeMetrics] = field(default_factory=dict)
    hub_nodes: List[str] = field(default_factory=list)
    authority_nodes: List[str] = field(default_factory=list)
    bridge_nodes: List[str] = field(default_factory=list)
    bottleneck_nodes: List[str] = field(default_factory=list)

    # Path analytics
    critical_paths: List[PathMetrics] = field(default_factory=list)
    longest_paths: List[PathMetrics] = field(default_factory=list)
    high_risk_paths: List[PathMetrics] = field(default_factory=list)

    # Component analytics
    components: Dict[int, ComponentMetrics] = field(default_factory=dict)
    strongly_connected_components: List[Set[str]] = field(default_factory=list)

    # Cluster analytics
    clusters: Dict[int, ClusterMetrics] = field(default_factory=dict)

    # Provider analytics
    provider_distribution: Dict[str, int] = field(default_factory=dict)
    provider_coupling: Dict[Tuple[str, str], int] = field(default_factory=dict)

    # Module analytics
    module_distribution: Dict[str, int] = field(default_factory=dict)
    module_depth_distribution: Dict[int, int] = field(default_factory=dict)

    # Anomaly detection
    isolated_nodes: List[str] = field(default_factory=list)
    orphaned_nodes: List[str] = field(default_factory=list)
    unused_nodes: List[str] = field(default_factory=list)
    over_connected_nodes: List[str] = field(default_factory=list)

    # Risk analysis
    high_risk_nodes: List[Tuple[str, float]] = field(default_factory=list)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    dependency_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """
        Converts the entire GraphAnalytics object into a Jinja/JSON-safe dictionary.
        Handles nested dataclasses, Enums, Sets, and Tuple keys.
        """
        raw_dict = asdict(self)

        raw_dict["node_metrics"] = {
            k: metrics.to_dict() for k, metrics in self.node_metrics.items()
        }
        raw_dict["critical_paths"] = [path.to_dict() for path in self.critical_paths]
        raw_dict["longest_paths"] = [path.to_dict() for path in self.longest_paths]
        raw_dict["high_risk_paths"] = [path.to_dict() for path in self.high_risk_paths]
        raw_dict["components"] = {
            k: comp.to_dict() for k, comp in self.components.items()
        }
        raw_dict["clusters"] = {
            k: cluster.to_dict() for k, cluster in self.clusters.items()
        }

        raw_dict["type_distribution"] = _to_serializable(self.type_distribution)
        raw_dict["state_distribution"] = _to_serializable(self.state_distribution)
        raw_dict["link_type_distribution"] = _to_serializable(
            self.link_type_distribution
        )
        raw_dict["provider_coupling"] = _to_serializable(self.provider_coupling)

        raw_dict["strongly_connected_components"] = [
            list(scc) for scc in self.strongly_connected_components
        ]

        return raw_dict
