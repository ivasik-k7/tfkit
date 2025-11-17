import random
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from tfkit.analytics.models import (
    ArchetypePattern,
    ArchitecturePattern,
    ChangeImpactAnalysis,
    ClusterMetrics,
    ComplexityLevel,
    ComponentMetrics,
    ComponentType,
    GraphAnalytics,
    ModuleAnalysis,
    NodeMetrics,
    PathMetrics,
    ProviderAnalysis,
    RiskLevel,
    SecurityInsight,
)
from tfkit.graph.models import GraphData, Link, LinkType, Node, NodeState, NodeType


class TerraformGraphAnalytics:
    """Enhanced Terraform-specific graph analytics"""

    def __init__(self, graph_data: GraphData):
        self.graph = graph_data
        self.analytics = GraphAnalytics()

        # Optimized data structures
        self._adjacency_list: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: {"in": set(), "out": set()}
        )
        self._link_map: Dict[Tuple[str, str], Link] = {}
        self._node_map: Dict[str, Node] = {}
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

        self._build_optimized_structures()

    def _build_optimized_structures(self) -> None:
        """Build optimized data structures for O(1) lookups"""
        for node in self.graph.nodes.values():
            self._node_map[node.id] = node

        for link in self.graph.links:
            self._adjacency_list[link.source]["out"].add(link.target)
            self._adjacency_list[link.target]["in"].add(link.source)
            self._link_map[(link.source, link.target)] = link
            self._reverse_adjacency[link.target].add(link.source)

    def analyze(self) -> GraphAnalytics:
        """Perform comprehensive Terraform graph analysis"""
        print("🔍 Starting Enhanced Terraform Analytics...")

        # Core analysis
        self._compute_basic_statistics()
        self._compute_distributions()
        self._compute_connectivity_metrics()
        self._compute_structural_metrics()

        # Node-level analysis
        self._compute_node_metrics()
        self._identify_special_nodes()
        self._classify_node_complexity()
        self._assess_node_risks()

        # Path analysis
        self._analyze_paths()
        self._find_circular_dependencies()

        # Component analysis
        self._analyze_components()
        self._find_strongly_connected_components()
        self._find_articulation_points()

        # Clustering
        self._analyze_clusters()

        # Terraform-specific
        self._analyze_providers()
        self._analyze_modules()
        self._analyze_resource_relationships()

        # Advanced analysis
        # self._detect_anomalies()
        self._analyze_risks()
        self._compute_change_impact()
        self._detect_architecture_patterns()
        self._generate_insights()

        # Quality metrics
        self._compute_complexity_metrics()
        self._compute_quality_scores()
        self._generate_optimization_suggestions()

        print("✅ Enhanced Analytics Completed!")
        return self.analytics

    # ========== Basic Statistics ==========

    def _compute_basic_statistics(self) -> None:
        """Compute fundamental graph statistics"""
        self.analytics.total_nodes = len(self.graph.nodes)
        self.analytics.total_edges = len(self.graph.links)

    def _compute_distributions(self) -> None:
        """Compute all distribution metrics"""
        for node in self.graph.nodes.values():
            # Type distribution
            self.analytics.type_distribution[node.type] = (
                self.analytics.type_distribution.get(node.type, 0) + 1
            )

            # State distribution
            if node.data.state:
                self.analytics.state_distribution[node.data.state] = (
                    self.analytics.state_distribution.get(node.data.state, 0) + 1
                )

        # Link type distribution
        for link in self.graph.links:
            self.analytics.link_type_distribution[link.link_type] = (
                self.analytics.link_type_distribution.get(link.link_type, 0) + 1
            )

    def _compute_connectivity_metrics(self) -> None:
        """Compute connectivity and degree metrics"""
        if not self._node_map:
            return

        in_degrees, out_degrees = [], []
        resource_degrees, local_degrees, variable_degrees = [], [], []

        for node_id, node in self._node_map.items():
            in_deg = len(self._adjacency_list[node_id]["in"])
            out_deg = len(self._adjacency_list[node_id]["out"])

            in_degrees.append(in_deg)
            out_degrees.append(out_deg)

            total_deg = in_deg + out_deg
            if node.type == NodeType.RESOURCE:
                resource_degrees.append(total_deg)
            elif node.type == NodeType.LOCAL:
                local_degrees.append(total_deg)
            elif node.type == NodeType.VARIABLE:
                variable_degrees.append(total_deg)

        self.analytics.avg_in_degree = (
            sum(in_degrees) / len(in_degrees) if in_degrees else 0
        )
        self.analytics.avg_out_degree = (
            sum(out_degrees) / len(out_degrees) if out_degrees else 0
        )
        self.analytics.max_in_degree = max(in_degrees) if in_degrees else 0
        self.analytics.max_out_degree = max(out_degrees) if out_degrees else 0

        # Type-specific averages
        self.analytics.avg_resource_degree = (
            sum(resource_degrees) / len(resource_degrees) if resource_degrees else 0
        )
        self.analytics.avg_local_degree = (
            sum(local_degrees) / len(local_degrees) if local_degrees else 0
        )
        self.analytics.avg_variable_degree = (
            sum(variable_degrees) / len(variable_degrees) if variable_degrees else 0
        )

        # Graph density
        n = self.analytics.total_nodes
        max_edges = n * (n - 1)
        self.analytics.graph_density = (
            self.analytics.total_edges / max_edges if max_edges > 0 else 0
        )

    def _compute_structural_metrics(self) -> None:
        """Compute graph structural properties"""
        # Compute all-pairs shortest paths (sampled for performance)
        all_distances = []
        eccentricities = []

        sample_size = min(50, len(self._node_map))
        sample_nodes = random.sample(list(self._node_map.keys()), sample_size)

        for node in sample_nodes:
            distances = self._bfs_distances(node)
            all_distances.extend(distances.values())
            if distances:
                eccentricities.append(max(distances.values()))

        if all_distances:
            self.analytics.avg_path_length = sum(all_distances) / len(all_distances)
            self.analytics.diameter = max(all_distances)

        if eccentricities:
            self.analytics.radius = min(eccentricities)

        # Clustering coefficient
        self._compute_clustering_coefficient()

        # Transitivity (global clustering)
        self._compute_transitivity()

    def _compute_clustering_coefficient(self) -> None:
        """Compute local clustering coefficients"""
        total_coeff = 0.0
        count = 0

        for node_id in self._node_map.keys():
            neighbors = (
                self._adjacency_list[node_id]["in"]
                | self._adjacency_list[node_id]["out"]
            ) - {node_id}

            if len(neighbors) < 2:
                continue

            edges_between = 0
            neighbors_list = list(neighbors)
            for i, n1 in enumerate(neighbors_list):
                for n2 in neighbors_list[i + 1 :]:
                    if (
                        n2 in self._adjacency_list[n1]["out"]
                        or n1 in self._adjacency_list[n2]["out"]
                    ):
                        edges_between += 1

            possible = len(neighbors) * (len(neighbors) - 1) / 2
            if possible > 0:
                coeff = edges_between / possible
                if node_id in self.analytics.node_metrics:
                    self.analytics.node_metrics[node_id].clustering_coefficient = coeff
                total_coeff += coeff
                count += 1

        if count > 0:
            self.analytics.avg_clustering_coefficient = total_coeff / count

    def _compute_transitivity(self) -> None:
        """Compute graph transitivity (ratio of closed triplets)"""
        triangles = 0
        triplets = 0

        for node in self._node_map.keys():
            neighbors = list(self._adjacency_list[node]["out"])
            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i + 1 :]:
                    triplets += 1
                    if n2 in self._adjacency_list[n1]["out"]:
                        triangles += 1

        self.analytics.transitivity = 3 * triangles / triplets if triplets > 0 else 0

    # ========== Node Metrics ==========

    def _compute_node_metrics(self) -> None:
        """Compute comprehensive node-level metrics"""
        print("📊 Computing node metrics...")

        # Initialize basic metrics
        for node_id, node in self._node_map.items():
            metrics = NodeMetrics(node_id=node_id)

            # Degree metrics
            metrics.in_degree = len(self._adjacency_list[node_id]["in"])
            metrics.out_degree = len(self._adjacency_list[node_id]["out"])
            metrics.total_degree = metrics.in_degree + metrics.out_degree
            metrics.fan_in = metrics.in_degree
            metrics.fan_out = metrics.out_degree

            # Weighted degrees
            metrics.weighted_in_degree = sum(
                self._link_map.get(
                    (pred, node_id), Link(pred, node_id, LinkType.IMPLICIT, 1.0)
                ).strength
                for pred in self._adjacency_list[node_id]["in"]
            )
            metrics.weighted_out_degree = sum(
                self._link_map.get(
                    (node_id, succ), Link(node_id, succ, LinkType.IMPLICIT, 1.0)
                ).strength
                for succ in self._adjacency_list[node_id]["out"]
            )

            # Transitive dependencies
            metrics.transitive_dependencies = len(self._get_all_dependencies(node_id))
            metrics.transitive_dependents = len(self._get_all_dependents(node_id))

            # Dependency chain length
            metrics.dependency_chain_length = self._compute_chain_length(node_id)
            metrics.max_dependency_depth = self._compute_max_depth(node_id)

            # Flags
            metrics.is_root = metrics.in_degree == 0
            metrics.is_leaf = metrics.out_degree == 0
            metrics.is_orphan = metrics.total_degree == 0

            # Terraform-specific
            if node.data.module_path:
                metrics.module_depth = len(node.data.module_path)

            metrics.resource_blast_radius = self._compute_blast_radius(node_id)

            self.analytics.node_metrics[node_id] = metrics

        # Compute centrality metrics
        self._compute_centrality_metrics()

    def _compute_centrality_metrics(self) -> None:
        """Compute all centrality metrics"""
        print("🎯 Computing centrality metrics...")

        # PageRank
        self._compute_pagerank()

        # Betweenness (sampled for performance)
        self._compute_betweenness_centrality()

        # Eigenvector centrality
        self._compute_eigenvector_centrality()

    def _compute_pagerank(self, damping: float = 0.85, max_iter: int = 50) -> None:
        """Compute PageRank with Terraform-specific weighting"""
        n = len(self._node_map)
        if n == 0:
            return

        pagerank = dict.fromkeys(self._node_map.keys(), 1.0 / n)

        for _iteration in range(max_iter):
            new_pagerank = {}

            for node_id in self._node_map.keys():
                rank = (1 - damping) / n

                for predecessor in self._adjacency_list[node_id]["in"]:
                    pred_node = self._node_map[predecessor]
                    out_degree = len(self._adjacency_list[predecessor]["out"])

                    # Weight resources higher
                    weight = 2.0 if pred_node.type == NodeType.RESOURCE else 1.0

                    if out_degree > 0:
                        rank += damping * (pagerank[predecessor] / out_degree) * weight

                new_pagerank[node_id] = rank

            # Check convergence
            if all(abs(new_pagerank[nid] - pagerank[nid]) < 1e-6 for nid in pagerank):
                break

            pagerank = new_pagerank

        # Normalize
        total = sum(pagerank.values())
        if total > 0:
            for node_id in pagerank:
                self.analytics.node_metrics[node_id].pagerank = (
                    pagerank[node_id] / total
                )

    def _compute_betweenness_centrality(self) -> None:
        """Compute betweenness centrality (sampled)"""
        betweenness = defaultdict(float)

        sample_size = min(50, len(self._node_map))
        sample_nodes = random.sample(list(self._node_map.keys()), sample_size)

        for source in sample_nodes:
            stack = []
            predecessors = defaultdict(list)
            sigma = defaultdict(int)
            sigma[source] = 1
            distances = {source: 0}
            queue = deque([source])

            # BFS
            while queue:
                v = queue.popleft()
                stack.append(v)

                for w in self._adjacency_list[v]["out"]:
                    if w not in distances:
                        distances[w] = distances[v] + 1
                        queue.append(w)

                    if distances[w] == distances[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

            # Accumulation
            delta = defaultdict(float)
            while stack:
                w = stack.pop()
                for v in predecessors[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != source:
                    betweenness[w] += delta[w]

        # Normalize
        scale = (
            1.0 / (sample_size * (len(self._node_map) - 1)) if sample_size > 0 else 0
        )
        for node_id, value in betweenness.items():
            self.analytics.node_metrics[node_id].betweenness_centrality = value * scale

    def _compute_eigenvector_centrality(self, max_iter: int = 100) -> None:
        """Compute eigenvector centrality using power iteration"""
        n = len(self._node_map)
        if n == 0:
            return

        # Initialize centrality for all nodes in the graph
        centrality = {node_id: 1.0 / n for node_id in self._node_map.keys()}

        for _ in range(max_iter):
            new_centrality = defaultdict(float)

            for node_id in self._node_map.keys():
                for predecessor in self._adjacency_list[node_id]["in"]:
                    # Only include predecessors that exist in our graph
                    if predecessor in centrality:
                        new_centrality[node_id] += centrality[predecessor]
                    else:
                        # Handle case where predecessor is not in centrality dict
                        # This can happen with incomplete graph data
                        continue

            # Check if we have any values to normalize
            if not new_centrality:
                break

            # Normalize
            norm = sum(v**2 for v in new_centrality.values()) ** 0.5
            if norm > 1e-10:  # Use a small epsilon to avoid division by near-zero
                centrality = {k: v / norm for k, v in new_centrality.items()}

                # Check for convergence
                if _ > 0:  # Skip convergence check on first iteration
                    max_change = max(
                        abs(centrality.get(k, 0) - new_centrality.get(k, 0))
                        for k in set(centrality.keys()) | set(new_centrality.keys())
                    )
                    if max_change < 1e-6:
                        break
            else:
                break

        for node_id in self._node_map.keys():
            value = centrality.get(node_id, 0.0)
            self.analytics.node_metrics[node_id].eigenvector_centrality = value

    # ========== Helper Methods ==========

    def _get_all_dependencies(
        self, node_id: str, visited: Optional[Set[str]] = None
    ) -> Set[str]:
        """Get all transitive dependencies of a node"""
        if visited is None:
            visited = set()

        if node_id in visited:
            return visited

        visited.add(node_id)
        for dep in self._adjacency_list[node_id]["out"]:
            self._get_all_dependencies(dep, visited)

        visited.remove(node_id)
        return visited

    def _get_all_dependents(
        self, node_id: str, visited: Optional[Set[str]] = None
    ) -> Set[str]:
        """Get all transitive dependents of a node"""
        if visited is None:
            visited = set()

        if node_id in visited:
            return visited

        visited.add(node_id)
        for dep in self._adjacency_list[node_id]["in"]:
            self._get_all_dependents(dep, visited)

        visited.remove(node_id)
        return visited

    def _compute_chain_length(self, node_id: str) -> int:
        """Compute longest path through this node"""
        max_length = 0
        queue = deque([(node_id, 0)])
        visited = {node_id}

        while queue:
            current, length = queue.popleft()
            max_length = max(max_length, length)

            for predecessor in self._adjacency_list[current]["in"]:
                if predecessor not in visited:
                    visited.add(predecessor)
                    queue.append((predecessor, length + 1))

        return max_length

    def _compute_max_depth(self, node_id: str) -> int:
        """Compute maximum depth from root nodes"""
        depths = []

        for root in self.analytics.root_nodes:
            if root == node_id:
                depths.append(0)
                continue

            distance = self._shortest_distance(root, node_id)
            if distance >= 0:
                depths.append(distance)

        return max(depths) if depths else 0

    def _compute_blast_radius(self, node_id: str) -> int:
        """Compute potential impact if node changes"""
        affected = self._get_all_dependents(node_id)
        return len(affected)

    def _shortest_distance(self, start: str, end: str) -> int:
        """BFS shortest distance"""
        if start == end:
            return 0

        distances = {start: 0}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            for neighbor in self._adjacency_list[current]["out"]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    if neighbor == end:
                        return distances[neighbor]
                    queue.append(neighbor)

        return -1

    def _bfs_distances(self, start: str) -> Dict[str, int]:
        """BFS to compute all distances from start"""
        distances = {start: 0}
        queue = deque([start])

        while queue:
            node = queue.popleft()
            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)

        return distances

    # ========== Node Classification ==========

    def _identify_special_nodes(self) -> None:
        """Identify hubs, authorities, bridges, bottlenecks"""
        print("🎯 Identifying special nodes...")

        metrics_list = list(self.analytics.node_metrics.values())
        if not metrics_list:
            return

        # Hub nodes (high out-degree)
        hub_candidates = sorted(
            [
                m
                for m in metrics_list
                if m.out_degree > max(2, self.analytics.avg_out_degree * 1.5)
            ],
            key=lambda m: m.out_degree,
            reverse=True,
        )[:10]
        self.analytics.hub_nodes = [m.node_id for m in hub_candidates]
        for m in hub_candidates:
            m.is_hub = True

        # Authority nodes (high in-degree)
        auth_candidates = sorted(
            [
                m
                for m in metrics_list
                if m.in_degree > max(2, self.analytics.avg_in_degree * 1.5)
            ],
            key=lambda m: m.in_degree,
            reverse=True,
        )[:10]
        self.analytics.authority_nodes = [m.node_id for m in auth_candidates]
        for m in auth_candidates:
            m.is_authority = True

        # Bottleneck nodes (high betweenness)
        bottleneck_candidates = sorted(
            [m for m in metrics_list if m.betweenness_centrality > 0.01],
            key=lambda m: m.betweenness_centrality,
            reverse=True,
        )[:10]
        self.analytics.bottleneck_nodes = [m.node_id for m in bottleneck_candidates]
        for m in bottleneck_candidates:
            m.is_bottleneck = True

        # Bridge nodes (connecting different components)
        self._identify_bridge_nodes()

        # Root and leaf nodes
        self.analytics.root_nodes = [m.node_id for m in metrics_list if m.is_root]
        self.analytics.leaf_nodes = [m.node_id for m in metrics_list if m.is_leaf]

    def _identify_bridge_nodes(self) -> None:
        """Identify bridge nodes using structural analysis"""
        for node_id, metrics in self.analytics.node_metrics.items():
            in_neighbors = self._adjacency_list[node_id]["in"]
            out_neighbors = self._adjacency_list[node_id]["out"]

            # A bridge connects different subgraphs
            if len(in_neighbors) >= 2 and len(out_neighbors) >= 2:
                # Check if removing this node would disconnect the graph
                is_bridge = self._is_articulation_point(node_id)
                if is_bridge:
                    metrics.is_bridge = True
                    self.analytics.bridge_nodes.append(node_id)

    def _is_articulation_point(self, node_id: str) -> bool:
        """Check if node is an articulation point (simplified)"""
        # Count connected components without this node
        neighbors = (
            self._adjacency_list[node_id]["in"] | self._adjacency_list[node_id]["out"]
        )

        if len(neighbors) < 2:
            return False

        # Check if all neighbors are connected without going through node_id
        visited = set()
        start = next(iter(neighbors))
        queue = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()
            for neighbor in (
                self._adjacency_list[current]["in"]
                | self._adjacency_list[current]["out"]
            ):
                if neighbor != node_id and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # If we didn't reach all neighbors, node_id is an articulation point
        return len(visited) < len(neighbors)

    def _classify_node_complexity(self) -> None:
        """Classify nodes by complexity level"""
        print("📈 Classifying node complexity...")

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            score = 0.0

            # Degree contribution
            score += metrics.total_degree * 0.5

            # Type contribution
            if node.type == NodeType.RESOURCE:
                score += 4.0
            elif node.type == NodeType.MODULE:
                score += 3.0
            elif node.type == NodeType.LOCAL:
                score += 1.5
            elif node.type == NodeType.VARIABLE:
                score += 1.0

            # Centrality contribution
            score += metrics.betweenness_centrality * 20
            score += metrics.pagerank * 15

            # Structural contribution
            score += metrics.dependency_chain_length * 0.4
            score += metrics.transitive_dependencies * 0.2

            # State contribution
            if node.data.state in [NodeState.HUB, NodeState.BRIDGE]:
                score += 3.0

            # Classify
            if score > 25:
                metrics.complexity_level = ComplexityLevel.EXTREME
            elif score > 18:
                metrics.complexity_level = ComplexityLevel.CRITICAL
            elif score > 12:
                metrics.complexity_level = ComplexityLevel.HIGH
            elif score > 6:
                metrics.complexity_level = ComplexityLevel.MEDIUM
            elif score > 2:
                metrics.complexity_level = ComplexityLevel.LOW
            else:
                metrics.complexity_level = ComplexityLevel.MINIMAL

            # Update distribution
            self.analytics.complexity_distribution[metrics.complexity_level] = (
                self.analytics.complexity_distribution.get(metrics.complexity_level, 0)
                + 1
            )

    def _assess_node_risks(self) -> None:
        """Assess risk level for each node"""
        print("⚠️ Assessing node risks...")

        risk_scores = []

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            risk = 0.0

            # Complexity risk
            complexity_risk = {
                ComplexityLevel.MINIMAL: 0,
                ComplexityLevel.LOW: 1,
                ComplexityLevel.MEDIUM: 3,
                ComplexityLevel.HIGH: 5,
                ComplexityLevel.CRITICAL: 8,
                ComplexityLevel.EXTREME: 10,
            }
            risk += complexity_risk[metrics.complexity_level]

            # Structural risk
            if metrics.is_bottleneck:
                risk += 8.0
            if metrics.is_bridge:
                risk += 6.0
            if metrics.is_hub:
                risk += 4.0

            # Impact risk
            risk += min(metrics.resource_blast_radius * 0.3, 10.0)

            # Type risk
            if node.type == NodeType.RESOURCE:
                risk += 3.0
            elif node.type == NodeType.MODULE:
                risk += 2.0

            # State risk
            if node.data.state in [NodeState.UNRESOLVED, NodeState.INVALID]:
                risk += 10.0
            elif node.data.state == NodeState.ORPHAN:
                risk += 5.0

            # Implicit dependency risk
            implicit_count = sum(
                1
                for succ in self._adjacency_list[node_id]["out"]
                if self._link_map.get(
                    (node_id, succ), Link(node_id, succ, LinkType.IMPLICIT, 1.0)
                ).link_type
                == LinkType.IMPLICIT
            )
            risk += implicit_count * 2.0

            # Classify risk level
            if risk > 25:
                metrics.risk_level = RiskLevel.CRITICAL
            elif risk > 15:
                metrics.risk_level = RiskLevel.HIGH
            elif risk > 8:
                metrics.risk_level = RiskLevel.MODERATE
            elif risk > 3:
                metrics.risk_level = RiskLevel.LOW
            else:
                metrics.risk_level = RiskLevel.SAFE

            risk_scores.append((node_id, risk))

            # Update distribution
            self.analytics.risk_distribution[metrics.risk_level] = (
                self.analytics.risk_distribution.get(metrics.risk_level, 0) + 1
            )

        # Store high-risk nodes
        risk_scores.sort(key=lambda x: x[1], reverse=True)
        self.analytics.high_risk_nodes = risk_scores[:20]

    # ========== Path Analysis ==========

    def _analyze_paths(self) -> None:
        """Comprehensive path analysis"""
        print("🛤️ Analyzing dependency paths...")

        # Critical resource chains
        self._find_critical_resource_chains()

        # Configuration flow paths
        self._find_configuration_paths()

        # Longest paths
        self._find_longest_paths()

        # Compute path statistics
        self._compute_path_statistics()

    def _find_critical_resource_chains(self) -> None:
        """Find critical dependency chains through resources"""
        resource_nodes = [
            nid for nid, n in self._node_map.items() if n.type == NodeType.RESOURCE
        ]

        critical_paths = []
        sample_size = min(20, len(resource_nodes))

        for resource in resource_nodes[:sample_size]:
            paths = self._find_long_chains_from(resource, max_length=10)
            critical_paths.extend(paths)

        # Score and rank paths
        scored = [self._create_path_metrics(p) for p in critical_paths]
        scored.sort(key=lambda p: (p.length, p.risk_score), reverse=True)

        self.analytics.critical_paths = scored[:15]

    def _find_long_chains_from(
        self, start: str, max_length: int = 10
    ) -> List[List[str]]:
        """Find long dependency chains from a starting node"""
        chains = []
        stack = [(start, [start])]

        while stack:
            node, path = stack.pop()

            if len(path) >= max_length:
                chains.append(path)
                if len(path) >= 15:  # Hard limit
                    continue

            outgoing = [
                n
                for n in self._adjacency_list[node]["out"]
                if n not in path and self._node_map[n].type == NodeType.RESOURCE
            ]

            for neighbor in outgoing:
                stack.append((neighbor, path + [neighbor]))

        return chains

    def _find_configuration_paths(self) -> None:
        """Find paths from variables to resources"""
        variables = [
            nid for nid, n in self._node_map.items() if n.type == NodeType.VARIABLE
        ]
        resources = [
            nid for nid, n in self._node_map.items() if n.type == NodeType.RESOURCE
        ]

        config_paths = []

        for var in variables[:10]:
            for res in resources[:20]:
                paths = self._find_all_paths(var, res, max_length=8)
                if paths:
                    shortest = min(paths, key=len)
                    config_paths.append(shortest)

        scored = [self._create_path_metrics(p) for p in config_paths]
        scored.sort(key=lambda p: p.risk_score, reverse=True)

        self.analytics.high_risk_paths = scored[:15]

    def _find_longest_paths(self) -> None:
        """Find the longest paths in the graph"""
        all_paths = []

        for root in self.analytics.root_nodes[:10]:
            for leaf in self.analytics.leaf_nodes[:20]:
                if root != leaf:
                    paths = self._find_all_paths(root, leaf, max_length=12)
                    all_paths.extend(paths)

        all_paths.sort(key=len, reverse=True)

        scored = [self._create_path_metrics(p) for p in all_paths[:15]]
        self.analytics.longest_paths = scored

    def _find_all_paths(
        self, start: str, end: str, max_length: int = 10
    ) -> List[List[str]]:
        """Find all simple paths between two nodes"""
        if start == end:
            return [[start]]

        paths = []
        stack = [(start, [start])]

        while stack:
            node, path = stack.pop()

            if len(path) > max_length:
                continue

            if node == end:
                paths.append(path)
                continue

            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor]))

        return paths

    def _create_path_metrics(self, path: List[str]) -> PathMetrics:
        """Create comprehensive path metrics"""
        metrics = PathMetrics(path=path, length=len(path))

        weights = []
        providers = set()
        modules = set()
        implicit_count = 0
        cross_provider = 0
        cross_module = 0

        for i, node_id in enumerate(path):
            node = self._node_map[node_id]
            metrics.node_types.append(node.type)
            metrics.node_states.append(node.data.state)

            if node.data.provider:
                providers.add(node.data.provider)
            if node.data.module_path:
                modules.add(tuple(node.data.module_path))

            if i < len(path) - 1:
                link = self._link_map.get((node_id, path[i + 1]))
                if link:
                    metrics.link_types.append(link.link_type)
                    weights.append(link.strength)

                    if link.link_type == LinkType.IMPLICIT:
                        implicit_count += 1

                    next_node = self._node_map[path[i + 1]]
                    if (
                        node.data.provider
                        and next_node.data.provider
                        and node.data.provider != next_node.data.provider
                    ):
                        cross_provider += 1

                    if (
                        node.data.module_path
                        and next_node.data.module_path
                        and node.data.module_path != next_node.data.module_path
                    ):
                        cross_module += 1

        # Weight metrics
        if weights:
            metrics.total_weight = sum(weights)
            metrics.avg_weight = metrics.total_weight / len(weights)
            metrics.min_weight = min(weights)
            metrics.max_weight = max(weights)

        # Provider metrics
        metrics.provider_count = len(providers)
        metrics.providers = list(providers)

        # Complexity indicators
        metrics.implicit_link_count = implicit_count
        metrics.cross_provider_links = cross_provider
        metrics.cross_module_links = cross_module

        # Risk score
        risk = 0.0
        risk += metrics.length * 0.8
        risk += implicit_count * 3.0
        risk += cross_provider * 2.5
        risk += cross_module * 1.5
        risk += sum(
            5.0
            for nid in path
            if self.analytics.node_metrics[nid].risk_level == RiskLevel.CRITICAL
        )

        metrics.risk_score = risk

        # Risk level
        if risk > 30:
            metrics.risk_level = RiskLevel.CRITICAL
        elif risk > 20:
            metrics.risk_level = RiskLevel.HIGH
        elif risk > 10:
            metrics.risk_level = RiskLevel.MODERATE
        else:
            metrics.risk_level = RiskLevel.LOW

        # Blast radius
        metrics.blast_radius = sum(
            self.analytics.node_metrics[nid].resource_blast_radius for nid in path
        )

        return metrics

    def _compute_path_statistics(self) -> None:
        """Compute aggregate path statistics"""
        all_distances = []

        sample_nodes = list(self._node_map.keys())[:50]
        for node in sample_nodes:
            distances = self._bfs_distances(node)
            all_distances.extend(distances.values())

        if all_distances:
            self.analytics.avg_path_length = sum(all_distances) / len(all_distances)
            self.analytics.diameter = max(all_distances)

    def _find_circular_dependencies(self) -> None:
        """Find all circular dependencies (cycles)"""
        print("🔄 Finding circular dependencies...")

        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs(node, path):
            if node in recursion_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                if len(cycle) > 1:
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self._adjacency_list[node]["out"]:
                dfs(neighbor, path + [neighbor])

            recursion_stack.remove(node)

        for node_id in self._node_map.keys():
            if node_id not in visited:
                dfs(node_id, [node_id])

        # Remove duplicates
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            normalized = tuple(sorted(cycle))
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle)
                self.analytics.circular_dependencies.append(cycle)

        self.analytics.circular_paths = unique_cycles

    # ========== Component Analysis ==========

    def _analyze_components(self) -> None:
        """Analyze weakly connected components"""
        print("🔗 Analyzing components...")

        visited = set()
        component_id = 0

        for node_id in self._node_map.keys():
            if node_id in visited:
                continue

            component = self._find_component(node_id)
            visited.update(component)

            if len(component) > 1:
                metrics = self._compute_component_metrics(component_id, component)
                self.analytics.components[component_id] = metrics
                component_id += 1

        self.analytics.total_components = component_id

        if self.analytics.components:
            self.analytics.largest_component_size = max(
                c.size for c in self.analytics.components.values()
            )

    def _find_component(self, start: str) -> Set[str]:
        """Find connected component (undirected)"""
        component = set()
        stack = [start]

        while stack:
            node = stack.pop()
            if node in component:
                continue

            component.add(node)
            neighbors = (
                self._adjacency_list[node]["in"] | self._adjacency_list[node]["out"]
            )
            stack.extend(neighbors - component)

        return component

    def _compute_component_metrics(
        self, component_id: int, nodes: Set[str]
    ) -> ComponentMetrics:
        """Compute detailed component metrics"""
        metrics = ComponentMetrics(
            component_id=component_id, node_ids=nodes, size=len(nodes)
        )

        # Count internal edges
        internal_edges = sum(
            1
            for node in nodes
            for succ in self._adjacency_list[node]["out"]
            if succ in nodes
        )
        metrics.edge_count = internal_edges

        # Density
        max_edges = len(nodes) * (len(nodes) - 1)
        metrics.density = internal_edges / max_edges if max_edges > 0 else 0

        # Entry/exit points
        for node in nodes:
            has_external_in = any(
                p not in nodes for p in self._adjacency_list[node]["in"]
            )
            has_external_out = any(
                s not in nodes for s in self._adjacency_list[node]["out"]
            )

            if has_external_in:
                metrics.entry_points.add(node)
            if has_external_out:
                metrics.exit_points.add(node)

        # Node type distribution
        for node_id in nodes:
            node_type = self._node_map[node_id].type
            metrics.node_type_distribution[node_type] = (
                metrics.node_type_distribution.get(node_type, 0) + 1
            )

            provider = self._node_map[node_id].data.provider
            if provider:
                metrics.provider_distribution[provider] = (
                    metrics.provider_distribution.get(provider, 0) + 1
                )

        # Component type
        metrics.component_type = self._classify_component_type(nodes, internal_edges)

        # Cohesion and coupling
        external_edges = sum(
            1
            for node in nodes
            for succ in self._adjacency_list[node]["out"]
            if succ not in nodes
        )
        total_possible = len(nodes) * len(self._node_map)
        metrics.cohesion = internal_edges / max_edges if max_edges > 0 else 0
        metrics.coupling = external_edges / total_possible if total_possible > 0 else 0

        return metrics

    def _classify_component_type(
        self, nodes: Set[str], edge_count: int
    ) -> ComponentType:
        """Classify component structure"""
        n = len(nodes)

        if n == 1:
            return ComponentType.ISOLATED

        # Tree: n-1 edges
        if edge_count == n - 1:
            return ComponentType.TREE

        # Star: one central node
        degrees = [
            len(self._adjacency_list[node]["out"])
            + len(self._adjacency_list[node]["in"])
            for node in nodes
        ]
        if max(degrees) == 2 * (n - 1):
            return ComponentType.STAR

        # Linear: all nodes have degree ≤ 2
        if all(d <= 2 for d in degrees):
            return ComponentType.LINEAR

        # Check for cycles
        if self._has_cycle_in_subgraph(nodes):
            return ComponentType.CYCLIC

        # High density suggests mesh
        max_edges = n * (n - 1)
        if edge_count > 0.6 * max_edges:
            return ComponentType.MESH

        return ComponentType.COMPLEX

    def _has_cycle_in_subgraph(self, nodes: Set[str]) -> bool:
        """Check if subgraph contains a cycle"""
        visited = set()
        recursion_stack = set()

        def dfs(node):
            if node in recursion_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor in nodes and dfs(neighbor):
                    return True

            recursion_stack.remove(node)
            return False

        for node in nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def _find_strongly_connected_components(self) -> None:
        """Find strongly connected components using Kosaraju's algorithm"""
        print("🔗 Finding strongly connected components...")

        # Step 1: First DFS to get finishing times
        visited = set()
        stack = []

        def dfs_first(node):
            visited.add(node)
            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor not in visited:
                    dfs_first(neighbor)
            stack.append(node)

        for node_id in self._node_map.keys():
            if node_id not in visited:
                dfs_first(node_id)

        # Step 2: Transpose graph
        transposed = defaultdict(set)
        for node_id in self._node_map.keys():
            for neighbor in self._adjacency_list[node_id]["out"]:
                transposed[neighbor].add(node_id)

        # Step 3: Second DFS on transposed graph
        visited.clear()
        sccs = []

        def dfs_second(node, component):
            visited.add(node)
            component.add(node)
            for neighbor in transposed[node]:
                if neighbor not in visited:
                    dfs_second(neighbor, component)

        while stack:
            node = stack.pop()
            if node not in visited:
                component = set()
                dfs_second(node, component)
                if len(component) > 1:  # Only consider non-trivial SCCs
                    sccs.append(component)

        self.analytics.strongly_connected_components = sccs

    def _find_articulation_points(self) -> None:
        """Find articulation points using DFS"""
        print("📍 Finding articulation points...")

        visited = set()
        discovery = {}
        low = {}
        parent = {}
        articulation_points = set()
        time = [0]

        def dfs(node):
            visited.add(node)
            discovery[node] = time[0]
            low[node] = time[0]
            time[0] += 1
            children = 0

            for neighbor in (
                self._adjacency_list[node]["in"] | self._adjacency_list[node]["out"]
            ):
                if neighbor not in visited:
                    parent[neighbor] = node
                    children += 1
                    dfs(neighbor)

                    low[node] = min(low[node], low[neighbor])

                    # Root with two or more children is articulation point
                    if parent.get(node) is None and children > 1:
                        articulation_points.add(node)

                    # Non-root with low[child] >= discovery[node]
                    if (
                        parent.get(node) is not None
                        and low[neighbor] >= discovery[node]
                    ):
                        articulation_points.add(node)

                elif neighbor != parent.get(node):
                    low[node] = min(low[node], discovery[neighbor])

        for node_id in self._node_map.keys():
            if node_id not in visited:
                dfs(node_id)

        # Update component metrics
        for component in self.analytics.components.values():
            component.articulation_points = articulation_points & component.node_ids

    # ========== Clustering Analysis ==========

    def _analyze_clusters(self) -> None:
        """Perform community detection using modularity optimization"""
        print("🏘️ Analyzing clusters...")

        # Simple community detection based on connectivity
        clusters = self._detect_communities()

        for cluster_id, nodes in enumerate(clusters):
            if len(nodes) > 1:  # Only meaningful clusters
                metrics = self._compute_cluster_metrics(cluster_id, nodes)
                self.analytics.clusters[cluster_id] = metrics

        self.analytics.optimal_cluster_count = len(clusters)

    def _detect_communities(self) -> List[Set[str]]:
        """Simple community detection using label propagation"""
        nodes = list(self._node_map.keys())
        communities = {node: i for i, node in enumerate(nodes)}

        changed = True
        max_iter = 10

        while changed and max_iter > 0:
            changed = False
            random.shuffle(nodes)

            for node in nodes:
                # Count community frequencies in neighbors
                neighbor_communities = defaultdict(int)
                neighbors = (
                    self._adjacency_list[node]["in"] | self._adjacency_list[node]["out"]
                )

                for neighbor in neighbors:
                    neighbor_communities[communities[neighbor]] += 1

                if neighbor_communities:
                    # Find most frequent community
                    new_community = max(
                        neighbor_communities.items(), key=lambda x: x[1]
                    )[0]
                    if new_community != communities[node]:
                        communities[node] = new_community
                        changed = True

            max_iter -= 1

        # Group by community
        community_groups = defaultdict(set)
        for node, community_id in communities.items():
            community_groups[community_id].add(node)

        return list(community_groups.values())

    def _compute_cluster_metrics(
        self, cluster_id: int, nodes: Set[str]
    ) -> ClusterMetrics:
        """Compute comprehensive cluster metrics"""
        metrics = ClusterMetrics(cluster_id=cluster_id, node_ids=nodes)

        # Count internal and external edges
        internal_edges = 0
        external_edges = 0

        for node in nodes:
            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor in nodes:
                    internal_edges += 1
                else:
                    external_edges += 1

        metrics.internal_edges = internal_edges
        metrics.external_edges = external_edges

        # Density
        n = len(nodes)
        max_internal = n * (n - 1)
        metrics.density = internal_edges / max_internal if max_internal > 0 else 0

        # Cohesion and separation
        total_possible_external = n * (len(self._node_map) - n)
        metrics.cohesion = internal_edges / max_internal if max_internal > 0 else 0
        metrics.separation = 1 - (
            external_edges / total_possible_external
            if total_possible_external > 0
            else 0
        )

        # Silhouette score (simplified)
        metrics.silhouette_score = metrics.cohesion - (1 - metrics.separation)

        # Composition analysis
        type_counts = defaultdict(int)
        providers = set()
        resource_types = set()

        for node_id in nodes:
            node = self._node_map[node_id]
            type_counts[node.type] += 1

            if node.data.provider:
                providers.add(node.data.provider)
            if node.type == NodeType.RESOURCE and node.data.resource_type:
                resource_types.add(node.data.resource_type)

        metrics.node_type_distribution = dict(type_counts)
        metrics.providers = providers
        metrics.resource_types = resource_types

        # Dominant type
        if type_counts:
            metrics.dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]

        # Dominant provider
        if providers:
            provider_counts = defaultdict(int)
            for node_id in nodes:
                provider = self._node_map[node_id].data.provider
                if provider:
                    provider_counts[provider] += 1
            if provider_counts:
                metrics.dominant_provider = max(
                    provider_counts.items(), key=lambda x: x[1]
                )[0]

        return metrics

    # ========== Provider Analysis ==========

    def _analyze_providers(self) -> None:
        """Comprehensive provider analysis"""
        print("🏢 Analyzing providers...")

        provider_nodes = defaultdict(list)

        for node_id, node in self._node_map.items():
            if node.data.provider:
                provider_nodes[node.data.provider].append(node_id)

        for provider, nodes in provider_nodes.items():
            analysis = self._compute_provider_analysis(provider, nodes)
            self.analytics.provider_analysis[provider] = analysis
            self.analytics.provider_distribution[provider] = len(nodes)

        self._analyze_provider_coupling()

    def _compute_provider_analysis(
        self, provider: str, nodes: List[str]
    ) -> ProviderAnalysis:
        """Compute detailed provider metrics"""
        analysis = ProviderAnalysis(provider=provider)

        analysis.node_count = len(nodes)
        analysis.resource_count = sum(
            1 for node_id in nodes if self._node_map[node_id].type == NodeType.RESOURCE
        )

        # Resource type analysis
        resource_types = set()
        for node_id in nodes:
            node = self._node_map[node_id]
            if node.type == NodeType.RESOURCE and node.data.resource_type:
                resource_types.add(node.data.resource_type)

        analysis.resource_types = resource_types
        analysis.resource_type_count = len(resource_types)

        # Coupling analysis
        internal_deps = 0
        external_deps = 0

        for node_id in nodes:
            for neighbor in self._adjacency_list[node_id]["out"]:
                neighbor_provider = self._node_map[neighbor].data.provider
                if neighbor_provider == provider:
                    internal_deps += 1
                else:
                    external_deps += 1
                    if neighbor_provider:
                        analysis.coupled_providers[neighbor_provider] = (
                            analysis.coupled_providers.get(neighbor_provider, 0) + 1
                        )

        analysis.internal_dependencies = internal_deps
        analysis.external_dependencies = external_deps
        analysis.coupling_ratio = (
            external_deps / (internal_deps + external_deps)
            if (internal_deps + external_deps) > 0
            else 0
        )

        # Complexity analysis
        complexities = [
            self.analytics.node_metrics[node_id].complexity_level
            for node_id in nodes
            if node_id in self.analytics.node_metrics
        ]
        if complexities:
            complexity_scores = {
                ComplexityLevel.MINIMAL: 1,
                ComplexityLevel.LOW: 2,
                ComplexityLevel.MEDIUM: 3,
                ComplexityLevel.HIGH: 4,
                ComplexityLevel.CRITICAL: 5,
                ComplexityLevel.EXTREME: 6,
            }
            avg_complexity = sum(
                complexity_scores.get(c, 1) for c in complexities
            ) / len(complexities)
            analysis.avg_resource_complexity = avg_complexity
            analysis.max_resource_complexity = max(
                complexity_scores.get(c, 1) for c in complexities
            )

        return analysis

    def _analyze_provider_coupling(self) -> None:
        """Analyze coupling between providers"""
        provider_coupling = defaultdict(int)

        for link in self.graph.links:
            source_provider = self._node_map[link.source].data.provider
            target_provider = self._node_map[link.target].data.provider

            if (
                source_provider
                and target_provider
                and source_provider != target_provider
            ):
                key = (source_provider, target_provider)
                provider_coupling[key] += 1

        self.analytics.provider_coupling = dict(provider_coupling)

        # Provider diversity
        unique_providers = len(self.analytics.provider_distribution)
        total_nodes = len(self._node_map)
        self.analytics.provider_diversity_score = (
            unique_providers / (total_nodes**0.5) if total_nodes > 0 else 0
        )

    # ========== Module Analysis ==========

    def _analyze_modules(self) -> None:
        """Comprehensive module analysis"""
        print("📦 Analyzing modules...")

        module_nodes = defaultdict(list)
        module_depths = defaultdict(int)

        for node_id, node in self._node_map.items():
            if node.data.module_path:
                module_name = ".".join(node.data.module_path)
                module_nodes[module_name].append(node_id)
                module_depths[module_name] = len(node.data.module_path)

        for module_name, nodes in module_nodes.items():
            analysis = self._compute_module_analysis(module_name, nodes)
            self.analytics.module_analysis[module_name] = analysis
            self.analytics.module_distribution[module_name] = len(nodes)

        # Module depth distribution
        for depth in module_depths.values():
            self.analytics.module_depth_distribution[depth] = (
                self.analytics.module_depth_distribution.get(depth, 0) + 1
            )

        if module_depths:
            self.analytics.max_module_depth = max(module_depths.values())

    def _compute_module_analysis(
        self, module_name: str, nodes: List[str]
    ) -> ModuleAnalysis:
        """Compute detailed module metrics"""
        analysis = ModuleAnalysis(module_name=module_name)

        analysis.node_count = len(nodes)
        analysis.resource_count = sum(
            1 for node_id in nodes if self._node_map[node_id].type == NodeType.RESOURCE
        )

        # Depth analysis
        depths = [len(self._node_map[node_id].data.module_path) for node_id in nodes]
        analysis.depth = max(depths) if depths else 0

        # Input/output analysis
        input_count = sum(
            1 for node_id in nodes if self._node_map[node_id].type == NodeType.VARIABLE
        )
        output_count = sum(
            1 for node_id in nodes if self._node_map[node_id].type == NodeType.OUTPUT
        )

        analysis.input_count = input_count
        analysis.output_count = output_count

        # Dependency analysis
        internal_deps = 0
        external_deps = 0

        for node_id in nodes:
            for neighbor in self._adjacency_list[node_id]["out"]:
                neighbor_module = (
                    ".".join(self._node_map[neighbor].data.module_path)
                    if self._node_map[neighbor].data.module_path
                    else ""
                )
                if neighbor_module == module_name:
                    internal_deps += 1
                else:
                    external_deps += 1

        analysis.internal_dependencies = internal_deps
        analysis.external_dependencies = external_deps

        # Composition
        type_counts = defaultdict(int)
        providers = set()

        for node_id in nodes:
            node = self._node_map[node_id]
            type_counts[node.type] += 1
            if node.data.provider:
                providers.add(node.data.provider)

        analysis.node_types = dict(type_counts)
        analysis.providers = providers

        # Quality metrics
        _total_deps = internal_deps + external_deps
        analysis.cohesion = internal_deps / len(nodes) if len(nodes) > 0 else 0
        analysis.coupling = external_deps / len(nodes) if len(nodes) > 0 else 0

        # Reusability score (higher is better)
        analysis.reusability_score = (
            (input_count * 0.3) + (output_count * 0.4) + (1 - analysis.coupling) * 0.3
        )

        return analysis

    # ========== Resource Relationship Analysis ==========

    def _analyze_resource_relationships(self) -> None:
        """Analyze relationships between resources"""
        print("🔗 Analyzing resource relationships...")

        # This would analyze specific Terraform resource patterns
        # For now, we'll compute some basic resource metrics

        resource_nodes = [
            node_id
            for node_id, node in self._node_map.items()
            if node.type == NodeType.RESOURCE
        ]

        # Compute resource coupling patterns
        self._analyze_resource_coupling_patterns(resource_nodes)

    def _analyze_resource_coupling_patterns(self, resource_nodes: List[str]) -> None:
        """Analyze how resources are coupled together"""
        # Group resources by provider and type
        provider_resource_groups = defaultdict(lambda: defaultdict(list))

        for node_id in resource_nodes:
            node = self._node_map[node_id]
            if node.data.provider and node.data.resource_type:
                provider_resource_groups[node.data.provider][
                    node.data.resource_type
                ].append(node_id)

        # Analyze coupling within and between groups
        # This could be extended to detect anti-patterns

    # ========== Anomaly Detection ==========

    def _detect_anomalies(self) -> None:
        """Detect various graph anomalies"""
        print("🚨 Detecting anomalies...")

        self._find_isolated_nodes()
        self._find_orphaned_nodes()
        self._find_unused_nodes()
        self._find_over_connected_nodes()
        self._find_redundant_dependencies()

    def _find_isolated_nodes(self) -> None:
        """Find completely isolated nodes"""
        self.analytics.isolated_nodes = [
            node_id
            for node_id, metrics in self.analytics.node_metrics.items()
            if metrics.total_degree == 0
        ]

    def _find_orphaned_nodes(self) -> None:
        """Find nodes with no incoming dependencies but that should have some"""
        # Orphaned resources are those that aren't depended on by anything
        # but probably should be
        orphan_candidates = []

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Resources with no dependents might be orphaned
            if (
                node.type == NodeType.RESOURCE
                and metrics.in_degree == 0
                and metrics.out_degree > 0
            ):
                orphan_candidates.append(node_id)

        self.analytics.orphaned_nodes = orphan_candidates

    def _find_unused_nodes(self) -> None:
        """Find nodes that are defined but not used"""
        # Variables and outputs that aren't connected
        unused = []

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            if (node.type == NodeType.VARIABLE and metrics.out_degree == 0) or (
                node.type == NodeType.OUTPUT and metrics.in_degree == 0
            ):
                unused.append(node_id)

        self.analytics.unused_nodes = unused

    def _find_over_connected_nodes(self) -> None:
        """Find nodes with unusually high connectivity"""
        degree_threshold = self.analytics.avg_total_degree * 3

        over_connected = [
            node_id
            for node_id, metrics in self.analytics.node_metrics.items()
            if metrics.total_degree > max(degree_threshold, 10)
        ]

        self.analytics.over_connected_nodes = over_connected

    def _find_redundant_dependencies(self) -> None:
        """Find redundant dependency relationships"""
        redundant = []

        for node_id in self._node_map.keys():
            # Check for transitive reductions
            direct_deps = self._adjacency_list[node_id]["out"]

            for dep in direct_deps:
                # If there's a longer path to dep, the direct link might be redundant
                if self._has_alternative_path(node_id, dep, direct_deps):
                    redundant.append((node_id, dep))

        self.analytics.redundant_dependencies = redundant

    def _has_alternative_path(
        self, source: str, target: str, direct_deps: Set[str]
    ) -> bool:
        """Check if there's an alternative path from source to target"""
        visited = set()
        stack = [neighbor for neighbor in direct_deps if neighbor != target]

        while stack:
            current = stack.pop()
            if current == target:
                return True

            if current in visited:
                continue

            visited.add(current)
            stack.extend(self._adjacency_list[current]["out"] - visited)

        return False

    # ========== Risk Analysis ==========

    def _analyze_risks(self) -> None:
        """Comprehensive risk analysis"""
        print("⚠️ Performing risk analysis...")

        self._analyze_circular_dependency_risks()
        self._analyze_dependency_violations()
        self._generate_security_insights()

    def _analyze_circular_dependency_risks(self) -> None:
        """Analyze risks from circular dependencies"""
        # Already captured in circular_dependencies
        pass

    def _analyze_dependency_violations(self) -> None:
        """Detect dependency violations and anti-patterns"""
        violations = []

        # Check for module -> provider dependencies (should be avoided)
        for link in self.graph.links:
            source = self._node_map[link.source]
            target = self._node_map[link.target]

            # Module depending on resource (usually should be the other way)
            if source.type == NodeType.MODULE and target.type == NodeType.RESOURCE:
                violations.append(f"Module {source.id} depends on resource {target.id}")

        self.analytics.dependency_violations = violations

    def _generate_security_insights(self) -> None:
        """Generate security-related insights"""
        insights = []

        # Check for overly permissive dependencies
        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Resources with many dependents might be security concerns
            if (
                node.type == NodeType.RESOURCE
                and metrics.in_degree > 10
                and "security" in node.id.lower()
            ):
                insight = SecurityInsight(
                    insight_type="OVERLY_PERMISSIVE_RESOURCE",
                    severity=RiskLevel.HIGH,
                    node_id=node_id,
                    description=f"Security resource {node_id} has {metrics.in_degree} dependents",
                    recommendation="Review access patterns and consider reducing dependencies",
                    affected_nodes=list(self._adjacency_list[node_id]["in"]),
                )
                insights.append(insight)

        self.analytics.security_insights = insights

    # ========== Change Impact Analysis ==========

    def _compute_change_impact(self) -> None:
        """Compute change impact for all nodes"""
        print("📈 Computing change impact...")

        for node_id in self._node_map.keys():
            impact = self._compute_node_change_impact(node_id)
            self.analytics.change_impact[node_id] = impact

            if impact.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.analytics.high_impact_nodes.append(node_id)

    def _compute_node_change_impact(self, node_id: str) -> ChangeImpactAnalysis:
        """Compute change impact for a specific node"""
        impact = ChangeImpactAnalysis(node_id=node_id)

        # Direct relationships
        impact.direct_dependents = self._adjacency_list[node_id]["in"]
        impact.direct_dependencies = self._adjacency_list[node_id]["out"]

        # Transitive relationships
        impact.transitive_dependents = self._get_all_dependents(node_id)
        impact.transitive_dependencies = self._get_all_dependencies(node_id)

        # Blast radius
        impact.total_affected_nodes = len(impact.transitive_dependents)

        # Affected resources and modules
        affected_resources = 0
        affected_modules = set()
        affected_providers = set()

        for affected_node in impact.transitive_dependents:
            node = self._node_map[affected_node]
            if node.type == NodeType.RESOURCE:
                affected_resources += 1
            if node.data.module_path:
                affected_modules.add(tuple(node.data.module_path))
            if node.data.provider:
                affected_providers.add(node.data.provider)

        impact.affected_resources = affected_resources
        impact.affected_modules = len(affected_modules)
        impact.affected_providers = affected_providers

        # Risk assessment
        risk_score = 0.0
        risk_score += impact.total_affected_nodes * 0.5
        risk_score += affected_resources * 1.0
        risk_score += len(affected_providers) * 2.0

        # Critical paths affected
        critical_paths_affected = sum(
            1 for path in self.analytics.critical_paths if node_id in path.path
        )
        impact.critical_paths_affected = critical_paths_affected
        risk_score += critical_paths_affected * 3.0

        # Node-specific risk factors
        node_metrics = self.analytics.node_metrics.get(node_id)
        if node_metrics:
            if node_metrics.is_bottleneck:
                risk_score += 10.0
            if node_metrics.is_bridge:
                risk_score += 8.0
            if node_metrics.risk_level == RiskLevel.CRITICAL:
                risk_score += 15.0
            elif node_metrics.risk_level == RiskLevel.HIGH:
                risk_score += 10.0

        impact.risk_score = risk_score

        # Risk level classification
        if risk_score > 40:
            impact.risk_level = RiskLevel.CRITICAL
        elif risk_score > 25:
            impact.risk_level = RiskLevel.HIGH
        elif risk_score > 15:
            impact.risk_level = RiskLevel.MODERATE
        elif risk_score > 5:
            impact.risk_level = RiskLevel.LOW
        else:
            impact.risk_level = RiskLevel.SAFE

        return impact

    # ========== Architecture Pattern Detection ==========

    def _detect_architecture_patterns(self) -> None:
        """Detect common Terraform architecture patterns"""
        print("🏛️ Detecting architecture patterns...")

        patterns = []

        # Hub and spoke pattern
        hub_spoke = self._detect_hub_and_spoke()
        if hub_spoke:
            patterns.append(hub_spoke)

        # Layered pattern
        layered = self._detect_layered_architecture()
        if layered:
            patterns.append(layered)

        # Modular pattern
        modular = self._detect_modular_architecture()
        if modular:
            patterns.append(modular)

        self.analytics.detected_patterns = patterns

    def _detect_hub_and_spoke(self) -> Optional[ArchitecturePattern]:
        """Detect hub-and-spoke architecture pattern"""
        # Look for nodes with high out-degree and low in-degree (hubs)
        # connected to nodes with high in-degree and low out-degree (spokes)
        hub_candidates = [
            node_id
            for node_id, metrics in self.analytics.node_metrics.items()
            if metrics.out_degree > 5 and metrics.in_degree < 3
        ]

        if len(hub_candidates) < 1:
            return None

        # Find the strongest hub
        main_hub = max(
            hub_candidates, key=lambda x: self.analytics.node_metrics[x].out_degree
        )

        hub_metrics = self.analytics.node_metrics[main_hub]
        spokes = self._adjacency_list[main_hub]["out"]

        if len(spokes) < 3:
            return None

        confidence = min(hub_metrics.out_degree / 10, 1.0)

        return ArchitecturePattern(
            pattern=ArchetypePattern.HUB_AND_SPOKE,
            confidence=confidence,
            nodes={main_hub} | spokes,
            description=f"Hub-and-spoke pattern with {main_hub} as central hub",
            characteristics={
                "hub_node": main_hub,
                "spoke_count": len(spokes),
                "hub_out_degree": hub_metrics.out_degree,
            },
        )

    def _detect_layered_architecture(self) -> Optional[ArchitecturePattern]:
        """Detect layered architecture pattern"""
        # Look for clear separation between data, networking, compute layers
        # This is a simplified detection
        layer_candidates = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.type == NodeType.RESOURCE and node.data.resource_type:
                resource_type = node.data.resource_type.lower()

                if any(
                    net in resource_type
                    for net in ["network", "subnet", "vpc", "firewall"]
                ):
                    layer_candidates["networking"].add(node_id)
                elif any(
                    compute in resource_type
                    for compute in ["instance", "vm", "container", "lambda"]
                ):
                    layer_candidates["compute"].add(node_id)
                elif any(
                    data in resource_type
                    for data in ["bucket", "database", "storage", "table"]
                ):
                    layer_candidates["data"].add(node_id)

        if len(layer_candidates) >= 2:
            all_nodes = set()
            for layer_nodes in layer_candidates.values():
                all_nodes.update(layer_nodes)

            return ArchitecturePattern(
                pattern=ArchetypePattern.LAYERED,
                confidence=0.7,
                nodes=all_nodes,
                description="Layered architecture with clear separation of concerns",
                characteristics={
                    "layers": list(layer_candidates.keys()),
                    "layer_sizes": {
                        layer: len(nodes) for layer, nodes in layer_candidates.items()
                    },
                },
            )

        return None

    def _detect_modular_architecture(self) -> Optional[ArchitecturePattern]:
        """Detect modular architecture pattern"""
        module_count = len(self.analytics.module_analysis)

        if module_count >= 3:
            # Check for good module characteristics
            good_modules = 0
            total_modules = 0

            for module_analysis in self.analytics.module_analysis.values():
                total_modules += 1
                # Good modules have balanced inputs/outputs and reasonable size
                if (
                    module_analysis.input_count >= 1
                    and module_analysis.output_count >= 1
                    and 3 <= module_analysis.node_count <= 20
                ):
                    good_modules += 1

            modularity_ratio = good_modules / total_modules if total_modules > 0 else 0

            if modularity_ratio >= 0.6:
                return ArchitecturePattern(
                    pattern=ArchetypePattern.MODULAR,
                    confidence=modularity_ratio,
                    nodes=set(
                        self._node_map.keys()
                    ),  # All nodes participate in modular architecture
                    description="Well-structured modular architecture",
                    characteristics={
                        "total_modules": module_count,
                        "good_module_ratio": modularity_ratio,
                        "avg_module_size": sum(
                            m.node_count
                            for m in self.analytics.module_analysis.values()
                        )
                        / module_count,
                    },
                )

        return None

    # ========== Complexity and Quality Metrics ==========

    def _compute_complexity_metrics(self) -> None:
        """Compute overall complexity metrics"""
        print("📊 Computing complexity metrics...")

        # Cyclomatic complexity (approximate)
        self.analytics.cyclomatic_complexity = (
            self.analytics.total_edges
            - self.analytics.total_nodes
            + 2 * self.analytics.total_components
        )

        # Cognitive complexity (weighted by node complexity)
        cognitive_weights = {
            ComplexityLevel.MINIMAL: 1,
            ComplexityLevel.LOW: 2,
            ComplexityLevel.MEDIUM: 3,
            ComplexityLevel.HIGH: 5,
            ComplexityLevel.CRITICAL: 8,
            ComplexityLevel.EXTREME: 13,
        }

        total_cognitive = sum(
            cognitive_weights[metrics.complexity_level]
            for metrics in self.analytics.node_metrics.values()
        )
        self.analytics.cognitive_complexity = (
            total_cognitive / len(self.analytics.node_metrics)
            if self.analytics.node_metrics
            else 0
        )

        # Coupling and cohesion scores
        total_cohesion = sum(c.cohesion for c in self.analytics.components.values())
        total_coupling = sum(c.coupling for c in self.analytics.components.values())

        self.analytics.cohesion_score = (
            total_cohesion / len(self.analytics.components)
            if self.analytics.components
            else 0
        )
        self.analytics.coupling_score = (
            total_coupling / len(self.analytics.components)
            if self.analytics.components
            else 0
        )

    def _compute_quality_scores(self) -> None:
        """Compute overall quality and maintainability scores"""
        print("⭐ Computing quality scores...")

        # Maintainability Index (simplified)
        # Higher is better (0-100 scale)
        base_score = 100.0

        # Penalties
        penalties = 0.0

        # Complexity penalty
        penalties += min(self.analytics.cognitive_complexity * 2, 30)

        # Coupling penalty
        penalties += min(self.analytics.coupling_score * 50, 20)

        # Risk penalty
        high_risk_count = len(
            [
                n
                for n in self.analytics.node_metrics.values()
                if n.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ]
        )
        penalties += min(high_risk_count * 1.5, 15)

        # Circular dependency penalty
        penalties += min(len(self.analytics.circular_dependencies) * 3, 10)

        # Anomaly penalty
        penalties += min(len(self.analytics.isolated_nodes) * 0.5, 5)
        penalties += min(len(self.analytics.orphaned_nodes) * 0.7, 5)

        self.analytics.maintainability_index = max(0, base_score - penalties)

        # Technical debt score (higher is worse)
        self.analytics.technical_debt_score = (
            (self.analytics.cognitive_complexity * 0.3)
            + (self.analytics.coupling_score * 0.4)
            + (high_risk_count * 0.3)
        )

        # Architecture quality score
        pattern_bonus = sum(p.confidence * 10 for p in self.analytics.detected_patterns)
        modularity_bonus = len(self.analytics.module_analysis) * 2
        provider_diversity_bonus = self.analytics.provider_diversity_score * 5

        self.analytics.architecture_quality_score = (
            pattern_bonus + modularity_bonus + provider_diversity_bonus
        )

    # ========== Optimization Suggestions ==========

    def _generate_optimization_suggestions(self) -> None:
        """Generate optimization and refactoring suggestions"""
        print("💡 Generating optimization suggestions...")

        self._generate_dependency_optimizations()
        self._generate_module_optimizations()
        self._generate_risk_mitigations()
        self._generate_performance_optimizations()

    def _generate_dependency_optimizations(self) -> None:
        """Generate dependency-related optimizations"""
        optimizations = []

        # Reduce circular dependencies
        if self.analytics.circular_dependencies:
            optimizations.append(
                {
                    "type": "CIRCULAR_DEPENDENCY_REDUCTION",
                    "priority": "HIGH",
                    "description": f"Found {len(self.analytics.circular_dependencies)} circular dependencies",
                    "suggestion": "Break circular dependencies by introducing interfaces or restructuring resources",
                    "impact": "High",
                    "effort": "Medium",
                }
            )

        # Reduce long dependency chains
        long_chains = [p for p in self.analytics.critical_paths if p.length > 8]
        if long_chains:
            optimizations.append(
                {
                    "type": "DEPENDENCY_CHAIN_OPTIMIZATION",
                    "priority": "MEDIUM",
                    "description": f"Found {len(long_chains)} long dependency chains (>8 steps)",
                    "suggestion": "Break long chains by creating intermediate resources or using data sources",
                    "impact": "Medium",
                    "effort": "Low",
                }
            )

        self.analytics.optimization_opportunities.extend(optimizations)

    def _generate_module_optimizations(self) -> None:
        """Generate module-related optimizations"""
        refactorings = []

        # Identify modules that could be split
        for module_name, analysis in self.analytics.module_analysis.items():
            if analysis.node_count > 15:
                refactorings.append(
                    {
                        "type": "MODULE_SPLITTING",
                        "module": module_name,
                        "description": f"Module {module_name} has {analysis.node_count} resources (consider splitting)",
                        "suggestion": "Split into smaller, more focused modules",
                        "benefit": "Improved maintainability and reusability",
                    }
                )

            # Low cohesion modules
            if analysis.cohesion < 0.3:
                refactorings.append(
                    {
                        "type": "MODULE_COHESION_IMPROVEMENT",
                        "module": module_name,
                        "description": f"Module {module_name} has low cohesion ({analysis.cohesion:.2f})",
                        "suggestion": "Restructure module to group related resources more effectively",
                        "benefit": "Better organization and reduced coupling",
                    }
                )

        self.analytics.refactoring_suggestions.extend(refactorings)

    def _generate_risk_mitigations(self) -> None:
        """Generate risk mitigation suggestions"""
        mitigations = []

        # High-risk nodes
        for node_id, risk_score in self.analytics.high_risk_nodes[:10]:
            node_metrics = self.analytics.node_metrics[node_id]

            mitigations.append(
                {
                    "type": "RISK_MITIGATION",
                    "node": node_id,
                    "risk_level": node_metrics.risk_level.value,
                    "description": f"High-risk node {node_id} (risk score: {risk_score:.1f})",
                    "suggestion": "Add monitoring, implement graceful degradation, or reduce dependencies",
                    "urgency": "HIGH"
                    if node_metrics.risk_level == RiskLevel.CRITICAL
                    else "MEDIUM",
                }
            )

        self.analytics.optimization_opportunities.extend(mitigations)

    def _generate_performance_optimizations(self) -> None:
        """Generate performance optimization suggestions"""
        optimizations = []

        # Bottleneck optimization
        for node_id in self.analytics.bottleneck_nodes:
            optimizations.append(
                {
                    "type": "BOTTLENECK_OPTIMIZATION",
                    "node": node_id,
                    "description": f"Node {node_id} is a potential bottleneck",
                    "suggestion": "Consider replicating or load balancing this resource",
                    "benefit": "Improved parallelism and reduced deployment time",
                }
            )

        # Over-connected nodes
        for node_id in self.analytics.over_connected_nodes:
            degree = self.analytics.node_metrics[node_id].total_degree
            optimizations.append(
                {
                    "type": "CONNECTIVITY_OPTIMIZATION",
                    "node": node_id,
                    "description": f"Node {node_id} has high connectivity ({degree} connections)",
                    "suggestion": "Reduce dependencies by introducing abstraction layers",
                    "benefit": "Reduced complexity and improved modularity",
                }
            )

        self.analytics.optimization_opportunities.extend(optimizations)

    def _generate_insights(self) -> None:
        """Generate final insights and summary"""
        print("📋 Generating final insights...")

        # This would create a comprehensive summary
        # For now, we'll just ensure all metrics are computed

        # Sort optimization opportunities by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        self.analytics.optimization_opportunities.sort(
            key=lambda x: priority_order.get(x.get("priority", "LOW"), 2)
        )

    # ========== Utility Methods ==========

    @property
    def _avg_total_degree(self) -> float:
        """Helper property for average total degree"""
        if not self.analytics.node_metrics:
            return 0.0
        return sum(m.total_degree for m in self.analytics.node_metrics.values()) / len(
            self.analytics.node_metrics
        )

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get a summary of key analytics metrics"""
        return {
            "graph_size": {
                "nodes": self.analytics.total_nodes,
                "edges": self.analytics.total_edges,
                "components": self.analytics.total_components,
            },
            "complexity": {
                "cognitive_complexity": round(self.analytics.cognitive_complexity, 2),
                "cyclomatic_complexity": self.analytics.cyclomatic_complexity,
                "maintainability_index": round(self.analytics.maintainability_index, 1),
            },
            "risks": {
                "high_risk_nodes": len(self.analytics.high_risk_nodes),
                "critical_paths": len(self.analytics.critical_paths),
                "circular_dependencies": len(self.analytics.circular_dependencies),
            },
            "quality": {
                "architecture_quality_score": round(
                    self.analytics.architecture_quality_score, 1
                ),
                "technical_debt_score": round(self.analytics.technical_debt_score, 2),
            },
            "optimizations": {
                "opportunities": len(self.analytics.optimization_opportunities),
                "refactorings": len(self.analytics.refactoring_suggestions),
            },
        }
