from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from tfkit.graph.models import LinkType, NodeState, NodeType


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


@dataclass
class PathMetrics:
    """Metrics for dependency paths"""

    path: List[str]
    length: int
    total_weight: float = 0.0
    risk_score: float = 0.0
    node_types: List[NodeType] = field(default_factory=list)
    link_types: List[LinkType] = field(default_factory=list)


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
