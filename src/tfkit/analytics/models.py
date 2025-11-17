from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from tfkit.graph.models import LinkType, NodeState, NodeType


class ComplexityLevel(Enum):
    """Node complexity classification"""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EXTREME = "extreme"


class ComponentType(Enum):
    """Graph component classification"""

    ISOLATED = "isolated"
    LINEAR = "linear"
    STAR = "star"
    TREE = "tree"
    CYCLIC = "cyclic"
    MESH = "mesh"
    COMPLEX = "complex"


class RiskLevel(Enum):
    """Risk classification"""

    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ArchetypePattern(Enum):
    """Common Terraform patterns"""

    HUB_AND_SPOKE = "hub_and_spoke"
    LAYERED = "layered"
    MODULAR = "modular"
    MONOLITHIC = "monolithic"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"


@dataclass
class NodeMetrics:
    """Comprehensive metrics for a single node"""

    node_id: str

    # Degree metrics
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    weighted_in_degree: float = 0.0
    weighted_out_degree: float = 0.0

    # Centrality metrics
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    eigenvector_centrality: float = 0.0
    pagerank: float = 0.0
    katz_centrality: float = 0.0

    # Structural metrics
    clustering_coefficient: float = 0.0
    eccentricity: Optional[int] = None
    depth_from_root: Optional[int] = None
    height_to_leaf: Optional[int] = None

    # Dependency metrics
    dependency_chain_length: int = 0
    max_dependency_depth: int = 0
    transitive_dependencies: int = 0
    transitive_dependents: int = 0
    fan_in: int = 0  # Number of direct dependents
    fan_out: int = 0  # Number of direct dependencies

    # Path metrics
    shortest_paths_count: int = 0
    critical_paths_count: int = 0

    # Classification
    complexity_level: ComplexityLevel = ComplexityLevel.LOW
    risk_level: RiskLevel = RiskLevel.LOW

    # Flags
    is_critical: bool = False
    is_bottleneck: bool = False
    is_hub: bool = False
    is_authority: bool = False
    is_bridge: bool = False
    is_leaf: bool = False
    is_root: bool = False
    is_orphan: bool = False

    # Terraform-specific
    provider_coupling_count: int = 0
    module_depth: int = 0
    resource_blast_radius: int = 0  # Potential impact if changed

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["complexity_level"] = self.complexity_level.value
        data["risk_level"] = self.risk_level.value
        return data


@dataclass
class PathMetrics:
    """Enhanced metrics for dependency paths"""

    path: List[str]
    length: int

    # Weight metrics
    total_weight: float = 0.0
    avg_weight: float = 0.0
    min_weight: float = 0.0
    max_weight: float = 0.0

    # Risk metrics
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW

    # Composition
    node_types: List[NodeType] = field(default_factory=list)
    link_types: List[LinkType] = field(default_factory=list)
    node_states: List[NodeState] = field(default_factory=list)

    # Provider diversity
    provider_count: int = 0
    providers: List[str] = field(default_factory=list)

    # Complexity indicators
    implicit_link_count: int = 0
    cross_provider_links: int = 0
    cross_module_links: int = 0

    # Impact analysis
    blast_radius: int = 0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["node_types"] = [t.value for t in self.node_types]
        data["link_types"] = [t.value for t in self.link_types]
        data["node_states"] = [s.value for s in self.node_states]
        data["risk_level"] = self.risk_level.value
        return data


@dataclass
class ComponentMetrics:
    """Enhanced metrics for graph components"""

    component_id: int
    node_ids: Set[str]
    size: int

    # Structure metrics
    edge_count: int = 0
    density: float = 0.0
    diameter: int = 0
    radius: int = 0
    average_path_length: float = 0.0

    # Connectivity
    component_type: ComponentType = ComponentType.COMPLEX
    is_strongly_connected: bool = False
    articulation_points: Set[str] = field(default_factory=set)
    bridges: Set[Tuple[str, str]] = field(default_factory=set)

    # Entry/Exit
    entry_points: Set[str] = field(default_factory=set)
    exit_points: Set[str] = field(default_factory=set)

    # Composition
    node_type_distribution: Dict[NodeType, int] = field(default_factory=dict)
    provider_distribution: Dict[str, int] = field(default_factory=dict)

    # Quality metrics
    modularity_score: float = 0.0
    cohesion: float = 0.0
    coupling: float = 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["component_type"] = self.component_type.value
        data["node_ids"] = list(self.node_ids)
        data["entry_points"] = list(self.entry_points)
        data["exit_points"] = list(self.exit_points)
        data["articulation_points"] = list(self.articulation_points)
        data["bridges"] = [f"{s}->{t}" for s, t in self.bridges]
        data["node_type_distribution"] = {
            k.value: v for k, v in self.node_type_distribution.items()
        }
        return data


@dataclass
class ClusterMetrics:
    """Enhanced metrics for node clusters"""

    cluster_id: int
    node_ids: Set[str]

    # Quality metrics
    cohesion: float = 0.0
    separation: float = 0.0
    silhouette_score: float = 0.0

    # Composition
    dominant_type: Optional[NodeType] = None
    dominant_provider: Optional[str] = None
    node_type_distribution: Dict[NodeType, int] = field(default_factory=dict)

    # Internal structure
    internal_edges: int = 0
    external_edges: int = 0
    density: float = 0.0

    # Terraform-specific
    resource_types: Set[str] = field(default_factory=set)
    providers: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["node_ids"] = list(self.node_ids)
        data["resource_types"] = list(self.resource_types)
        data["providers"] = list(self.providers)
        if self.dominant_type:
            data["dominant_type"] = self.dominant_type.value
        data["node_type_distribution"] = {
            k.value: v for k, v in self.node_type_distribution.items()
        }
        return data


@dataclass
class ProviderAnalysis:
    """Analysis of provider relationships and coupling"""

    provider: str

    # Size metrics
    resource_count: int = 0
    node_count: int = 0

    # Resource type diversity
    resource_types: Set[str] = field(default_factory=set)
    resource_type_count: int = 0

    # Coupling metrics
    internal_dependencies: int = 0
    external_dependencies: int = 0
    coupling_ratio: float = 0.0

    # Provider relationships
    coupled_providers: Dict[str, int] = field(default_factory=dict)
    coupling_strength: Dict[str, float] = field(default_factory=dict)

    # Complexity
    avg_resource_complexity: float = 0.0
    max_resource_complexity: float = 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["resource_types"] = list(self.resource_types)
        return data


@dataclass
class ModuleAnalysis:
    """Analysis of module structure and dependencies"""

    module_name: str

    # Size metrics
    node_count: int = 0
    resource_count: int = 0

    # Depth metrics
    depth: int = 0
    max_child_depth: int = 0

    # Dependencies
    input_count: int = 0
    output_count: int = 0
    internal_dependencies: int = 0
    external_dependencies: int = 0

    # Composition
    node_types: Dict[NodeType, int] = field(default_factory=dict)
    providers: Set[str] = field(default_factory=set)

    # Quality metrics
    cohesion: float = 0.0
    coupling: float = 0.0
    reusability_score: float = 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["node_types"] = {k.value: v for k, v in self.node_types.items()}
        data["providers"] = list(self.providers)
        return data


@dataclass
class SecurityInsight:
    """Security-related insights"""

    insight_type: str
    severity: RiskLevel
    node_id: str
    description: str
    recommendation: str
    affected_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class ArchitecturePattern:
    """Detected architecture patterns"""

    pattern: ArchetypePattern
    confidence: float
    nodes: Set[str]
    description: str
    characteristics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["pattern"] = self.pattern.value
        data["nodes"] = list(self.nodes)
        return data


@dataclass
class ChangeImpactAnalysis:
    """Impact analysis for potential changes"""

    node_id: str

    # Direct impact
    direct_dependents: Set[str] = field(default_factory=set)
    direct_dependencies: Set[str] = field(default_factory=set)

    # Transitive impact
    transitive_dependents: Set[str] = field(default_factory=set)
    transitive_dependencies: Set[str] = field(default_factory=set)

    # Blast radius
    total_affected_nodes: int = 0
    affected_resources: int = 0
    affected_modules: int = 0
    affected_providers: Set[str] = field(default_factory=set)

    # Risk assessment
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW

    # Critical paths affected
    critical_paths_affected: int = 0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["direct_dependents"] = list(self.direct_dependents)
        data["direct_dependencies"] = list(self.direct_dependencies)
        data["transitive_dependents"] = list(self.transitive_dependents)
        data["transitive_dependencies"] = list(self.transitive_dependencies)
        data["affected_providers"] = list(self.affected_providers)
        data["risk_level"] = self.risk_level.value
        return data


@dataclass
class GraphAnalytics:
    """Comprehensive graph analytics results"""

    # ========== Basic Statistics ==========
    total_nodes: int = 0
    total_edges: int = 0
    total_components: int = 0

    # ========== Distributions ==========
    type_distribution: Dict[NodeType, int] = field(default_factory=dict)
    state_distribution: Dict[NodeState, int] = field(default_factory=dict)
    link_type_distribution: Dict[LinkType, int] = field(default_factory=dict)
    complexity_distribution: Dict[ComplexityLevel, int] = field(default_factory=dict)
    risk_distribution: Dict[RiskLevel, int] = field(default_factory=dict)

    # ========== Connectivity Metrics ==========
    avg_in_degree: float = 0.0
    avg_out_degree: float = 0.0
    max_in_degree: int = 0
    max_out_degree: int = 0
    graph_density: float = 0.0

    # Terraform-specific averages
    avg_resource_degree: float = 0.0
    avg_local_degree: float = 0.0
    avg_variable_degree: float = 0.0

    # ========== Structural Metrics ==========
    diameter: int = 0
    radius: int = 0
    avg_path_length: float = 0.0
    avg_clustering_coefficient: float = 0.0
    transitivity: float = 0.0
    assortativity: float = 0.0

    # ========== Complexity Metrics ==========
    cyclomatic_complexity: int = 0
    cognitive_complexity: float = 0.0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_score: float = 0.0

    # ========== Node Analytics ==========
    node_metrics: Dict[str, NodeMetrics] = field(default_factory=dict)
    hub_nodes: List[str] = field(default_factory=list)
    authority_nodes: List[str] = field(default_factory=list)
    bridge_nodes: List[str] = field(default_factory=list)
    bottleneck_nodes: List[str] = field(default_factory=list)
    root_nodes: List[str] = field(default_factory=list)
    leaf_nodes: List[str] = field(default_factory=list)

    # ========== Path Analytics ==========
    critical_paths: List[PathMetrics] = field(default_factory=list)
    longest_paths: List[PathMetrics] = field(default_factory=list)
    high_risk_paths: List[PathMetrics] = field(default_factory=list)
    circular_paths: List[List[str]] = field(default_factory=list)

    # ========== Component Analytics ==========
    components: Dict[int, ComponentMetrics] = field(default_factory=dict)
    strongly_connected_components: List[Set[str]] = field(default_factory=list)
    largest_component_size: int = 0

    # ========== Cluster Analytics ==========
    clusters: Dict[int, ClusterMetrics] = field(default_factory=dict)
    optimal_cluster_count: int = 0

    # ========== Provider Analytics ==========
    provider_analysis: Dict[str, ProviderAnalysis] = field(default_factory=dict)
    provider_distribution: Dict[str, int] = field(default_factory=dict)
    provider_coupling: Dict[Tuple[str, str], int] = field(default_factory=dict)
    provider_diversity_score: float = 0.0

    # ========== Module Analytics ==========
    module_analysis: Dict[str, ModuleAnalysis] = field(default_factory=dict)
    module_distribution: Dict[str, int] = field(default_factory=dict)
    module_depth_distribution: Dict[int, int] = field(default_factory=dict)
    max_module_depth: int = 0

    # ========== Anomaly Detection ==========
    isolated_nodes: List[str] = field(default_factory=list)
    orphaned_nodes: List[str] = field(default_factory=list)
    unused_nodes: List[str] = field(default_factory=list)
    over_connected_nodes: List[str] = field(default_factory=list)
    redundant_dependencies: List[Tuple[str, str]] = field(default_factory=list)

    # ========== Risk Analysis ==========
    high_risk_nodes: List[Tuple[str, float]] = field(default_factory=list)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    dependency_violations: List[str] = field(default_factory=list)
    security_insights: List[SecurityInsight] = field(default_factory=list)

    # ========== Change Impact ==========
    change_impact: Dict[str, ChangeImpactAnalysis] = field(default_factory=dict)
    high_impact_nodes: List[str] = field(default_factory=list)

    # ========== Architecture Patterns ==========
    detected_patterns: List[ArchitecturePattern] = field(default_factory=list)
    architecture_quality_score: float = 0.0

    # ========== Optimization Suggestions ==========
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    refactoring_suggestions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary"""

        def serialize(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, tuple):
                return list(obj)
            elif hasattr(obj, "to_dict"):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {
                    (
                        k.value
                        if isinstance(k, Enum)
                        else "_".join(map(str, k))
                        if isinstance(k, tuple)
                        else k
                    ): serialize(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, (list, tuple)):
                return [serialize(item) for item in obj]
            return obj

        return serialize(asdict(self))
