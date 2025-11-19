import random
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

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
            self.analytics.type_distribution[node.type] = (
                self.analytics.type_distribution.get(node.type, 0) + 1
            )

            if node.data.state:
                self.analytics.state_distribution[node.data.state] = (
                    self.analytics.state_distribution.get(node.data.state, 0) + 1
                )

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
        centrality = dict.fromkeys(self._node_map.keys(), 1.0 / n)

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
            if node not in visited and dfs(node):
                return True

        return False

    def _find_strongly_connected_components(self) -> None:
        """Find strongly connected components using Tarjan's algorithm"""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = set()
        sccs = []

        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)

            for successor in self._adjacency_list[node]["out"]:
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif successor in on_stack:
                    lowlinks[node] = min(lowlinks[node], index[successor])

            if lowlinks[node] == index[node]:
                scc = set()
                while True:
                    successor = stack.pop()
                    on_stack.remove(successor)
                    scc.add(successor)
                    if successor == node:
                        break
                sccs.append(scc)

        for node in self._node_map.keys():
            if node not in index:
                strongconnect(node)

        # Store non-trivial SCCs
        self.analytics.strongly_connected_components = [
            scc for scc in sccs if len(scc) > 1
        ]

    def _find_articulation_points(self) -> None:
        """Find articulation points (cut vertices) in components using Tarjan's algorithm"""
        for component in self.analytics.components.values():
            nodes = component.node_ids
            if len(nodes) < 3:
                component.articulation_points = set()
                continue

            # Initialize tracking structures
            visited: Set[str] = set()
            discovery_time: Dict[str, int] = {}
            low_link: Dict[str, int] = {}
            parent: Dict[str, Optional[str]] = {}
            articulation_points: Set[str] = set()
            timer = [0]

            def dfs_articulation_point(node: str) -> None:
                """DFS helper to find articulation points"""
                children_count = 0
                visited.add(node)
                discovery_time[node] = low_link[node] = timer[0]
                timer[0] += 1

                # Get valid neighbors within component
                neighbors = [
                    neighbor
                    for neighbor in self._adjacency_list.get(node, {}).get("out", set())
                    if neighbor in nodes
                ]

                for neighbor in neighbors:
                    if neighbor not in visited:
                        # Unvisited neighbor - explore it
                        children_count += 1
                        parent[neighbor] = node
                        dfs_articulation_point(neighbor)

                        # Update low-link value
                        low_link[node] = min(
                            low_link[node], low_link.get(neighbor, float("inf"))
                        )

                        # Check articulation point conditions
                        # Root node with multiple children
                        if parent.get(node) is None and children_count > 1:
                            articulation_points.add(node)

                        # Non-root node where child cannot reach ancestor
                        if (
                            parent.get(node) is not None
                            and low_link.get(neighbor, float("inf"))
                            >= discovery_time[node]
                        ):
                            articulation_points.add(node)

                    elif neighbor != parent.get(node):
                        # Back edge (not to parent) - update low-link
                        low_link[node] = min(
                            low_link[node], discovery_time.get(neighbor, float("inf"))
                        )

            # Start DFS from first node in component
            if nodes:
                start_node = next(iter(nodes))
                parent[start_node] = None
                dfs_articulation_point(start_node)

            component.articulation_points = articulation_points

    # ========== Clustering ==========

    def _analyze_clusters(self) -> None:
        """Analyze resource clusters and communities"""
        print("🏗️ Analyzing clusters...")

        # Provider-based clusters
        self._cluster_by_provider()

        # Resource type clusters
        self._cluster_by_resource_type()

        # Module-based clusters
        self._cluster_by_module()

        # Compute optimal cluster count
        if self.analytics.clusters:
            self.analytics.optimal_cluster_count = len(self.analytics.clusters)

    def _cluster_by_provider(self) -> None:
        """Cluster nodes by provider"""
        provider_clusters = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.data.provider:
                provider_clusters[node.data.provider].add(node_id)

        cluster_id = 0
        for provider, nodes in provider_clusters.items():
            if len(nodes) > 1:
                metrics = self._compute_cluster_metrics(cluster_id, nodes)
                metrics.dominant_provider = provider
                self.analytics.clusters[cluster_id] = metrics
                cluster_id += 1

    def _cluster_by_resource_type(self) -> None:
        """Cluster resources by type"""
        type_clusters = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.type == NodeType.RESOURCE and node.data.resource_type:
                type_clusters[node.data.resource_type].add(node_id)

        cluster_id = len(self.analytics.clusters)
        for res_type, nodes in type_clusters.items():
            if len(nodes) > 2:
                metrics = self._compute_cluster_metrics(cluster_id, nodes)
                metrics.resource_types.add(res_type)
                self.analytics.clusters[cluster_id] = metrics
                cluster_id += 1

    def _cluster_by_module(self) -> None:
        """Cluster nodes by module"""
        module_clusters = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.data.module_path:
                module_key = tuple(node.data.module_path[:1])  # First level
                module_clusters[module_key].add(node_id)

        cluster_id = len(self.analytics.clusters)
        for module, nodes in module_clusters.items():
            if len(nodes) > 1:
                metrics = self._compute_cluster_metrics(cluster_id, nodes)
                self.analytics.clusters[cluster_id] = metrics
                cluster_id += 1

    def _compute_cluster_metrics(
        self, cluster_id: int, nodes: Set[str]
    ) -> ClusterMetrics:
        """Compute metrics for a cluster"""
        metrics = ClusterMetrics(cluster_id=cluster_id, node_ids=nodes)

        # Internal and external edges
        for node in nodes:
            for succ in self._adjacency_list[node]["out"]:
                if succ in nodes:
                    metrics.internal_edges += 1
                else:
                    metrics.external_edges += 1

        # Density
        max_edges = len(nodes) * (len(nodes) - 1)
        metrics.density = metrics.internal_edges / max_edges if max_edges > 0 else 0

        # Cohesion: ratio of internal to total edges
        total_edges = metrics.internal_edges + metrics.external_edges
        metrics.cohesion = (
            metrics.internal_edges / total_edges if total_edges > 0 else 0
        )

        # Separation: average distance to other clusters
        # (simplified version)
        metrics.separation = 1.0 - metrics.cohesion

        # Silhouette score (simplified)
        if total_edges > 0:
            metrics.silhouette_score = metrics.cohesion - metrics.separation

        # Composition
        type_counts = defaultdict(int)
        for node_id in nodes:
            node = self._node_map[node_id]
            type_counts[node.type] += 1

            if node.data.resource_type:
                metrics.resource_types.add(node.data.resource_type)
            if node.data.provider:
                metrics.providers.add(node.data.provider)

        if type_counts:
            metrics.dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]

        metrics.node_type_distribution = dict(type_counts)

        return metrics

    # ========== Provider Analysis ==========

    def _analyze_providers(self) -> None:
        """Analyze provider relationships and coupling"""
        print("🔌 Analyzing providers...")

        provider_nodes = defaultdict(list)

        for node_id, node in self._node_map.items():
            if node.data.provider:
                provider_nodes[node.data.provider].append(node_id)

        # Provider distribution
        for provider, nodes in provider_nodes.items():
            self.analytics.provider_distribution[provider] = len(nodes)

            # Create detailed analysis
            analysis = ProviderAnalysis(provider=provider)
            analysis.node_count = len(nodes)
            analysis.resource_count = sum(
                1 for nid in nodes if self._node_map[nid].type == NodeType.RESOURCE
            )

            # Resource types
            for node_id in nodes:
                node = self._node_map[node_id]
                if node.data.resource_type:
                    analysis.resource_types.add(node.data.resource_type)
            analysis.resource_type_count = len(analysis.resource_types)

            # Dependencies
            internal_deps = 0
            external_deps = 0

            for node_id in nodes:
                for dep in self._adjacency_list[node_id]["out"]:
                    dep_node = self._node_map[dep]
                    if dep_node.data.provider == provider:
                        internal_deps += 1
                    elif dep_node.data.provider:
                        external_deps += 1

            analysis.internal_dependencies = internal_deps
            analysis.external_dependencies = external_deps
            total_deps = internal_deps + external_deps
            analysis.coupling_ratio = (
                external_deps / total_deps if total_deps > 0 else 0
            )

            # Complexity
            complexities = [
                self.analytics.node_metrics[nid].complexity_level
                for nid in nodes
                if nid in self.analytics.node_metrics
            ]
            if complexities:
                complexity_values = {
                    ComplexityLevel.MINIMAL: 0,
                    ComplexityLevel.LOW: 1,
                    ComplexityLevel.MEDIUM: 2,
                    ComplexityLevel.HIGH: 3,
                    ComplexityLevel.CRITICAL: 4,
                    ComplexityLevel.EXTREME: 5,
                }
                analysis.avg_resource_complexity = sum(
                    complexity_values[c] for c in complexities
                ) / len(complexities)
                analysis.max_resource_complexity = max(
                    complexity_values[c] for c in complexities
                )

            self.analytics.provider_analysis[provider] = analysis

        # Provider coupling matrix
        providers = list(provider_nodes.keys())
        for i, prov_a in enumerate(providers):
            for prov_b in providers[i + 1 :]:
                coupling = self._calculate_provider_coupling(
                    prov_a, prov_b, provider_nodes
                )
                if coupling > 0:
                    self.analytics.provider_coupling[(prov_a, prov_b)] = coupling

                    # Update analysis
                    if prov_a in self.analytics.provider_analysis:
                        self.analytics.provider_analysis[prov_a].coupled_providers[
                            prov_b
                        ] = coupling
                    if prov_b in self.analytics.provider_analysis:
                        self.analytics.provider_analysis[prov_b].coupled_providers[
                            prov_a
                        ] = coupling

        # Provider diversity score
        if providers:
            total_nodes = sum(len(nodes) for nodes in provider_nodes.values())
            entropy = -sum(
                (len(nodes) / total_nodes)
                * (len(nodes) / total_nodes if len(nodes) > 0 else 1)
                for nodes in provider_nodes.values()
            )
            self.analytics.provider_diversity_score = entropy

    def _calculate_provider_coupling(
        self, prov_a: str, prov_b: str, provider_nodes: Dict[str, List[str]]
    ) -> int:
        """Calculate coupling between two providers"""
        coupling = 0
        nodes_a = provider_nodes[prov_a]
        nodes_b = provider_nodes[prov_b]

        for node_a in nodes_a:
            for node_b in nodes_b:
                if (
                    node_b in self._adjacency_list[node_a]["out"]
                    or node_a in self._adjacency_list[node_b]["out"]
                ):
                    coupling += 1

        return coupling

    # ========== Module Analysis ==========

    def _analyze_modules(self) -> None:
        """Analyze module structure and dependencies"""
        print("📦 Analyzing modules...")

        module_nodes = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.data.module_path:
                module_key = node.data.module_path[0]
                module_nodes[module_key].add(node_id)
            else:
                module_nodes["root"].add(node_id)

        # Module distribution
        for module, nodes in module_nodes.items():
            self.analytics.module_distribution[module] = len(nodes)

            # Create detailed analysis
            analysis = ModuleAnalysis(module_name=module)
            analysis.node_count = len(nodes)
            analysis.resource_count = sum(
                1 for nid in nodes if self._node_map[nid].type == NodeType.RESOURCE
            )

            # Depth
            depths = [
                len(self._node_map[nid].data.module_path)
                for nid in nodes
                if self._node_map[nid].data.module_path
            ]
            if depths:
                analysis.depth = min(depths)
                analysis.max_child_depth = max(depths)

            # Dependencies
            internal_deps = 0
            external_deps = 0

            for node_id in nodes:
                node = self._node_map[node_id]

                # Count inputs (variables)
                if node.type == NodeType.VARIABLE:
                    analysis.input_count += 1

                # Count outputs
                if node.type == NodeType.OUTPUT:
                    analysis.output_count += 1

                # Dependencies
                for dep in self._adjacency_list[node_id]["out"]:
                    if dep in nodes:
                        internal_deps += 1
                    else:
                        external_deps += 1

            analysis.internal_dependencies = internal_deps
            analysis.external_dependencies = external_deps

            # Node types
            for node_id in nodes:
                node_type = self._node_map[node_id].type
                analysis.node_types[node_type] = (
                    analysis.node_types.get(node_type, 0) + 1
                )

                if self._node_map[node_id].data.provider:
                    analysis.providers.add(self._node_map[node_id].data.provider)

            # Quality metrics
            total_deps = internal_deps + external_deps
            max_internal = len(nodes) * (len(nodes) - 1)
            analysis.cohesion = internal_deps / max_internal if max_internal > 0 else 0
            analysis.coupling = external_deps / total_deps if total_deps > 0 else 0

            # Reusability: low coupling, high cohesion, clear interface
            analysis.reusability_score = (
                analysis.cohesion * 0.4
                + (1 - analysis.coupling) * 0.4
                + min(analysis.input_count / 10, 1.0) * 0.1
                + min(analysis.output_count / 5, 1.0) * 0.1
            )

            self.analytics.module_analysis[module] = analysis

        # Module depth distribution
        for node in self._node_map.values():
            if node.data.module_path:
                depth = len(node.data.module_path)
                self.analytics.module_depth_distribution[depth] = (
                    self.analytics.module_depth_distribution.get(depth, 0) + 1
                )
                self.analytics.max_module_depth = max(
                    self.analytics.max_module_depth, depth
                )

    def _analyze_resource_relationships(self) -> None:
        """Analyze relationships between resources"""
        # Find resource-to-resource dependencies
        resource_deps = defaultdict(list)

        for node_id, node in self._node_map.items():
            if node.type == NodeType.RESOURCE:
                for dep in self._adjacency_list[node_id]["out"]:
                    dep_node = self._node_map[dep]
                    if dep_node.type == NodeType.RESOURCE:
                        resource_deps[node_id].append(dep)

    # ========== Anomaly Detection ==========

    def _detect_anomalies(self) -> None:
        """Detect anomalies and anti-patterns"""
        print("🚨 Detecting anomalies...")

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Isolated resources
            if (
                node.type == NodeType.RESOURCE
                and metrics.total_degree == 0
                and node.data.state not in [NodeState.UNUSED, NodeState.ORPHAN]
            ):
                self.analytics.isolated_nodes.append(node_id)

            # Orphaned nodes
            if (
                metrics.in_degree == 0
                and metrics.out_degree > 0
                and node.type
                not in [NodeType.VARIABLE, NodeType.PROVIDER, NodeType.TERRAFORM]
            ):
                self.analytics.orphaned_nodes.append(node_id)

            # Unused nodes
            if (
                metrics.out_degree == 0
                and metrics.in_degree > 0
                and node.type not in [NodeType.OUTPUT]
            ):
                self.analytics.unused_nodes.append(node_id)

            # Over-connected nodes
            avg_degree = self.analytics.avg_in_degree + self.analytics.avg_out_degree
            if avg_degree > 0 and metrics.total_degree > avg_degree * 3:
                self.analytics.over_connected_nodes.append(node_id)

        # Find redundant dependencies
        self._find_redundant_dependencies()

    def _find_redundant_dependencies(self) -> None:
        """Find redundant transitive dependencies"""
        for node_id in self._node_map.keys():
            direct_deps = self._adjacency_list[node_id]["out"]

            for dep in direct_deps:
                # Check if there's an indirect path
                transitive = self._get_all_dependencies(dep)

                for other_dep in direct_deps:
                    if other_dep != dep and other_dep in transitive:
                        self.analytics.redundant_dependencies.append(
                            (node_id, other_dep)
                        )

    # ========== Risk Analysis ==========

    def _analyze_risks(self) -> None:
        """Comprehensive risk analysis"""
        print("⚠️ Analyzing risks...")

        # Security insights
        self._generate_security_insights()

        # Dependency violations
        self._find_dependency_violations()

        # High impact nodes
        self._identify_high_impact_nodes()

    def _generate_security_insights(self) -> None:
        """Generate security-related insights"""
        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Publicly exposed resources
            if node.type == NodeType.RESOURCE and "public" in node_id.lower():
                insight = SecurityInsight(
                    insight_type="public_exposure",
                    severity=RiskLevel.HIGH,
                    node_id=node_id,
                    description=f"Resource {node_id} may be publicly exposed",
                    recommendation="Review access controls and ensure least privilege",
                )
                self.analytics.security_insights.append(insight)

            # Over-privileged nodes
            if metrics.resource_blast_radius > 50:
                insight = SecurityInsight(
                    insight_type="high_blast_radius",
                    severity=RiskLevel.CRITICAL,
                    node_id=node_id,
                    description=f"Changes to {node_id} affect {metrics.resource_blast_radius} resources",
                    recommendation="Consider breaking into smaller components",
                )
                self.analytics.security_insights.append(insight)

            # Implicit dependencies (harder to audit)
            implicit_links = sum(
                1
                for succ in self._adjacency_list[node_id]["out"]
                if self._link_map.get(
                    (node_id, succ), Link(node_id, succ, LinkType.IMPLICIT, 1.0)
                ).link_type
                == LinkType.IMPLICIT
            )
            if implicit_links > 5:
                insight = SecurityInsight(
                    insight_type="implicit_dependencies",
                    severity=RiskLevel.MODERATE,
                    node_id=node_id,
                    description=f"{node_id} has {implicit_links} implicit dependencies",
                    recommendation="Make dependencies explicit for better auditability",
                )
                self.analytics.security_insights.append(insight)

    def _find_dependency_violations(self) -> None:
        """Find dependency anti-patterns"""
        for link in self.graph.links:
            source_node = self._node_map[link.source]
            target_node = self._node_map[link.target]

            # Cross-provider implicit dependencies
            if (
                link.link_type == LinkType.IMPLICIT
                and source_node.data.provider
                and target_node.data.provider
                and source_node.data.provider != target_node.data.provider
            ):
                self.analytics.dependency_violations.append(
                    f"Implicit cross-provider: {link.source} -> {link.target}"
                )

            # Output depending on another output
            if (
                source_node.type == NodeType.OUTPUT
                and target_node.type == NodeType.OUTPUT
            ):
                self.analytics.dependency_violations.append(
                    f"Output-to-output dependency: {link.source} -> {link.target}"
                )

    def _identify_high_impact_nodes(self) -> None:
        """Identify nodes with high change impact"""
        impact_scores = [
            (nid, metrics.resource_blast_radius)
            for nid, metrics in self.analytics.node_metrics.items()
        ]
        impact_scores.sort(key=lambda x: x[1], reverse=True)

        self.analytics.high_impact_nodes = [nid for nid, _ in impact_scores[:20]]

    # ========== Change Impact ==========

    def _compute_change_impact(self) -> None:
        """Compute change impact for critical nodes"""
        print("💥 Computing change impact...")

        # Analyze top 20 most critical nodes
        critical_nodes = (
            self.analytics.hub_nodes[:10] + self.analytics.bottleneck_nodes[:10]
        )

        for node_id in set(critical_nodes):
            impact = self._analyze_node_impact(node_id)
            self.analytics.change_impact[node_id] = impact

    def _analyze_node_impact(self, node_id: str) -> ChangeImpactAnalysis:
        """Analyze impact of changing a specific node"""
        impact = ChangeImpactAnalysis(node_id=node_id)

        # Direct impact
        impact.direct_dependencies = set(self._adjacency_list[node_id]["out"])
        impact.direct_dependents = set(self._adjacency_list[node_id]["in"])

        # Transitive impact
        impact.transitive_dependencies = self._get_all_dependencies(node_id)
        impact.transitive_dependents = self._get_all_dependents(node_id)

        # Total affected
        all_affected = (
            impact.transitive_dependencies | impact.transitive_dependents | {node_id}
        )
        impact.total_affected_nodes = len(all_affected)

        # Count by type
        for affected_id in all_affected:
            affected_node = self._node_map[affected_id]
            if affected_node.type == NodeType.RESOURCE:
                impact.affected_resources += 1
            elif affected_node.type == NodeType.MODULE:
                impact.affected_modules += 1

            if affected_node.data.provider:
                impact.affected_providers.add(affected_node.data.provider)

        # Risk assessment
        risk = 0.0
        risk += impact.total_affected_nodes * 0.5
        risk += impact.affected_resources * 2.0
        risk += impact.affected_modules * 5.0
        risk += len(impact.affected_providers) * 3.0

        impact.risk_score = risk

        if risk > 50:
            impact.risk_level = RiskLevel.CRITICAL
        elif risk > 30:
            impact.risk_level = RiskLevel.HIGH
        elif risk > 15:
            impact.risk_level = RiskLevel.MODERATE
        else:
            impact.risk_level = RiskLevel.LOW

        # Count affected critical paths
        impact.critical_paths_affected = sum(
            1 for path in self.analytics.critical_paths if node_id in path.path
        )

        return impact

    # ========== Architecture Patterns ==========

    def _detect_architecture_patterns(self) -> None:
        """Detect common Terraform architecture patterns"""
        print("🏛️ Detecting architecture patterns...")

        # Hub and spoke pattern
        if self.analytics.hub_nodes:
            hub_pattern = self._detect_hub_and_spoke()
            if hub_pattern:
                self.analytics.detected_patterns.append(hub_pattern)

        # Layered architecture
        layered = self._detect_layered_architecture()
        if layered:
            self.analytics.detected_patterns.append(layered)

        # Modular architecture
        if len(self.analytics.module_distribution) > 3:
            modular = ArchitecturePattern(
                pattern=ArchetypePattern.MODULAR,
                confidence=0.8,
                nodes=set(self._node_map.keys()),
                description=f"Modular architecture with {len(self.analytics.module_distribution)} modules",
            )
            self.analytics.detected_patterns.append(modular)

    def _detect_hub_and_spoke(self) -> Optional[ArchitecturePattern]:
        """Detect hub-and-spoke pattern"""
        if not self.analytics.hub_nodes:
            return None

        hub_id = self.analytics.hub_nodes[0]
        hub_metrics = self.analytics.node_metrics[hub_id]

        if hub_metrics.out_degree > 10 and hub_metrics.in_degree < 3:
            spoke_nodes = self._adjacency_list[hub_id]["out"]

            return ArchitecturePattern(
                pattern=ArchetypePattern.HUB_AND_SPOKE,
                confidence=0.85,
                nodes=spoke_nodes | {hub_id},
                description=f"Hub ({hub_id}) with {len(spoke_nodes)} spokes",
                characteristics={"hub": hub_id, "spoke_count": len(spoke_nodes)},
            )

        return None

    def _detect_layered_architecture(self) -> Optional[ArchitecturePattern]:
        """Detect layered architecture"""
        # Check if nodes can be organized into distinct layers
        layers = defaultdict(set)

        for node_id, metrics in self.analytics.node_metrics.items():
            if metrics.depth_from_root is not None:
                layers[metrics.depth_from_root].add(node_id)

        if len(layers) >= 3:
            return ArchitecturePattern(
                pattern=ArchetypePattern.LAYERED,
                confidence=0.7,
                nodes=set(self._node_map.keys()),
                description=f"Layered architecture with {len(layers)} layers",
                characteristics={
                    "layer_count": len(layers),
                    "layer_sizes": {k: len(v) for k, v in layers.items()},
                },
            )

        return None

    # ========== Quality Metrics ==========

    def _compute_complexity_metrics(self) -> None:
        """Compute graph complexity metrics"""
        print("📊 Computing complexity metrics...")

        # Cyclomatic complexity
        self.analytics.cyclomatic_complexity = (
            self.analytics.total_edges
            - self.analytics.total_nodes
            + 2 * self.analytics.total_components
        )

        # Cognitive complexity (weighted by node types)
        cognitive = 0.0
        for node_id, node in self._node_map.items():
            metrics = self.analytics.node_metrics[node_id]

            # Base complexity
            cognitive += 1.0

            # Nested complexity
            if node.data.module_path:
                cognitive += len(node.data.module_path) * 0.5

            # Branching complexity
            if metrics.out_degree > 1:
                cognitive += metrics.out_degree * 0.3

            # Type-specific complexity
            if node.type == NodeType.MODULE:
                cognitive += 2.0
            elif node.type == NodeType.RESOURCE:
                cognitive += 1.0

        self.analytics.cognitive_complexity = cognitive

        # Coupling and cohesion
        self._compute_coupling_cohesion()

        # Maintainability index
        self._compute_maintainability_index()

        # Technical debt
        self._compute_technical_debt()

    def _compute_coupling_cohesion(self) -> None:
        """Compute coupling and cohesion scores"""
        total_coupling = 0.0
        total_cohesion = 0.0
        component_count = 0

        for component in self.analytics.components.values():
            total_coupling += component.coupling
            total_cohesion += component.cohesion
            component_count += 1

        if component_count > 0:
            self.analytics.coupling_score = total_coupling / component_count
            self.analytics.cohesion_score = total_cohesion / component_count

    def _compute_maintainability_index(self) -> None:
        """Compute maintainability index (0-100)"""
        base_score = 100.0

        # Size penalties
        base_score -= min(self.analytics.total_nodes * 0.05, 15.0)
        base_score -= min(self.analytics.total_edges * 0.03, 10.0)

        # Complexity penalties
        base_score -= min(self.analytics.cyclomatic_complexity * 0.2, 20.0)
        base_score -= min(self.analytics.cognitive_complexity * 0.01, 15.0)

        # Coupling penalty
        base_score -= self.analytics.coupling_score * 15.0

        # Cohesion bonus
        base_score += self.analytics.cohesion_score * 10.0

        # Risk penalties
        base_score -= len(self.analytics.high_risk_nodes) * 0.3
        base_score -= len(self.analytics.circular_dependencies) * 2.0
        base_score -= len(self.analytics.dependency_violations) * 0.5

        # Anomaly penalties
        base_score -= len(self.analytics.isolated_nodes) * 0.2
        base_score -= len(self.analytics.orphaned_nodes) * 0.3
        base_score -= len(self.analytics.unused_nodes) * 0.1

        # Security penalties
        base_score -= (
            len(
                [
                    s
                    for s in self.analytics.security_insights
                    if s.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                ]
            )
            * 1.0
        )

        self.analytics.maintainability_index = max(0.0, min(100.0, base_score))

    def _compute_technical_debt(self) -> None:
        """Compute technical debt score"""
        debt = 0.0

        # Complexity debt
        debt += self.analytics.cyclomatic_complexity * 0.5
        debt += self.analytics.cognitive_complexity * 0.1

        # Structural debt
        debt += len(self.analytics.circular_dependencies) * 5.0
        debt += len(self.analytics.redundant_dependencies) * 2.0

        # Coupling debt
        debt += self.analytics.coupling_score * 20.0

        # Risk debt
        debt += len(self.analytics.high_risk_nodes) * 1.0
        debt += len(self.analytics.dependency_violations) * 1.5

        # Anomaly debt
        debt += len(self.analytics.isolated_nodes) * 0.5
        debt += len(self.analytics.orphaned_nodes) * 1.0
        debt += len(self.analytics.unused_nodes) * 0.3
        debt += len(self.analytics.over_connected_nodes) * 1.5

        # Security debt
        debt += len(self.analytics.security_insights) * 2.0

        self.analytics.technical_debt_score = debt

    def _compute_quality_scores(self) -> None:
        """Compute overall quality scores"""
        print("⭐ Computing quality scores...")

        # Architecture quality
        quality = 0.0

        # Maintainability contribution (40%)
        quality += (self.analytics.maintainability_index / 100.0) * 40.0

        # Structural quality (30%)
        structural = 100.0
        structural -= min(self.analytics.coupling_score * 50.0, 30.0)
        structural += self.analytics.cohesion_score * 20.0
        structural -= len(self.analytics.circular_dependencies) * 5.0
        quality += (max(0, structural) / 100.0) * 30.0

        # Risk management (20%)
        risk_quality = 100.0
        risk_quality -= len(self.analytics.high_risk_nodes) * 2.0
        risk_quality -= (
            len(
                [
                    n
                    for n in self.analytics.node_metrics.values()
                    if n.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                ]
            )
            * 1.0
        )
        quality += (max(0, risk_quality) / 100.0) * 20.0

        # Best practices (10%)
        best_practices = 100.0
        best_practices -= len(self.analytics.dependency_violations) * 3.0
        best_practices -= len(self.analytics.security_insights) * 2.0
        best_practices -= len(self.analytics.isolated_nodes) * 1.0
        quality += (max(0, best_practices) / 100.0) * 10.0

        self.analytics.architecture_quality_score = max(0.0, min(100.0, quality))

    # ========== Optimization Suggestions ==========

    def _generate_optimization_suggestions(self) -> None:
        """Generate actionable optimization suggestions"""
        print("💡 Generating optimization suggestions...")

        # High coupling opportunities
        if self.analytics.coupling_score > 0.3:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "reduce_coupling",
                    "severity": "high",
                    "description": f"High coupling score ({self.analytics.coupling_score:.2f})",
                    "suggestion": "Consider breaking dependencies between providers or modules",
                    "affected_nodes": self.analytics.over_connected_nodes[:5],
                }
            )

        # Circular dependencies
        if self.analytics.circular_dependencies:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "break_cycles",
                    "severity": "critical",
                    "description": f"Found {len(self.analytics.circular_dependencies)} circular dependencies",
                    "suggestion": "Refactor to remove circular dependencies",
                    "affected_nodes": [
                        cycle[0] for cycle in self.analytics.circular_dependencies[:5]
                    ],
                }
            )

        # Bottlenecks
        if self.analytics.bottleneck_nodes:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "remove_bottlenecks",
                    "severity": "high",
                    "description": f"Found {len(self.analytics.bottleneck_nodes)} bottleneck nodes",
                    "suggestion": "Consider parallelizing dependencies or breaking bottlenecks",
                    "affected_nodes": self.analytics.bottleneck_nodes[:5],
                }
            )

        # Unused nodes
        if len(self.analytics.unused_nodes) > 5:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "remove_unused",
                    "severity": "low",
                    "description": f"Found {len(self.analytics.unused_nodes)} unused nodes",
                    "suggestion": "Remove unused resources to reduce complexity",
                    "affected_nodes": self.analytics.unused_nodes[:10],
                }
            )

        # Isolated resources
        if self.analytics.isolated_nodes:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "connect_isolated",
                    "severity": "medium",
                    "description": f"Found {len(self.analytics.isolated_nodes)} isolated resources",
                    "suggestion": "Integrate isolated resources or remove if unnecessary",
                    "affected_nodes": self.analytics.isolated_nodes[:5],
                }
            )

        # High complexity modules
        high_complexity_modules = [
            (name, analysis)
            for name, analysis in self.analytics.module_analysis.items()
            if analysis.coupling > 0.5 or analysis.cohesion < 0.3
        ]
        if high_complexity_modules:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "refactor_modules",
                    "severity": "medium",
                    "description": f"Found {len(high_complexity_modules)} modules with quality issues",
                    "suggestion": "Refactor modules to improve cohesion and reduce coupling",
                    "affected_nodes": [name for name, _ in high_complexity_modules[:5]],
                }
            )

        # Provider coupling
        high_provider_coupling = [
            (providers, count)
            for providers, count in self.analytics.provider_coupling.items()
            if count > 10
        ]
        if high_provider_coupling:
            self.analytics.optimization_opportunities.append(
                {
                    "type": "reduce_provider_coupling",
                    "severity": "medium",
                    "description": f"High coupling between providers",
                    "suggestion": "Use abstraction layers to reduce direct provider dependencies",
                    "affected_nodes": [
                        f"{p[0]}-{p[1]}" for p, _ in high_provider_coupling[:3]
                    ],
                }
            )

        # Generate refactoring suggestions
        self._generate_refactoring_suggestions()

    def _generate_refactoring_suggestions(self) -> None:
        """Generate specific refactoring suggestions"""

        # Extract module pattern
        if self.analytics.module_distribution.get("root", 0) > 50:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "extract_module",
                    "priority": "high",
                    "description": "Large root module detected",
                    "suggestion": "Extract logical components into separate modules",
                    "benefits": [
                        "Better organization",
                        "Improved reusability",
                        "Easier testing",
                    ],
                    "estimated_effort": "medium",
                }
            )

        # Introduce provider abstraction
        if self.analytics.provider_diversity_score > 1.5:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "abstract_providers",
                    "priority": "medium",
                    "description": "Multiple providers with complex coupling",
                    "suggestion": "Introduce abstraction layer to isolate provider-specific logic",
                    "benefits": [
                        "Reduced coupling",
                        "Easier provider migration",
                        "Better testability",
                    ],
                    "estimated_effort": "high",
                }
            )

        # Consolidate similar resources
        similar_clusters = [
            cluster
            for cluster in self.analytics.clusters.values()
            if len(cluster.resource_types) == 1 and len(cluster.node_ids) > 5
        ]
        if similar_clusters:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "consolidate_resources",
                    "priority": "low",
                    "description": f"Found {len(similar_clusters)} clusters of similar resources",
                    "suggestion": "Use count or for_each to consolidate similar resources",
                    "benefits": [
                        "DRY principle",
                        "Easier maintenance",
                        "Less repetition",
                    ],
                    "estimated_effort": "low",
                }
            )

        # Split large components
        large_components = [
            comp for comp in self.analytics.components.values() if comp.size > 30
        ]
        if large_components:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "split_component",
                    "priority": "medium",
                    "description": f"Found {len(large_components)} large components",
                    "suggestion": "Split large components along domain boundaries",
                    "benefits": [
                        "Better modularity",
                        "Parallel development",
                        "Reduced blast radius",
                    ],
                    "estimated_effort": "medium",
                }
            )

        # Improve documentation
        undocumented_modules = [
            name
            for name, analysis in self.analytics.module_analysis.items()
            if analysis.input_count > 0 and analysis.output_count == 0
        ]
        if undocumented_modules:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "add_outputs",
                    "priority": "low",
                    "description": f"{len(undocumented_modules)} modules lack clear outputs",
                    "suggestion": "Add output values to document module interfaces",
                    "benefits": [
                        "Better discoverability",
                        "Clear contracts",
                        "Improved reusability",
                    ],
                    "estimated_effort": "low",
                }
            )

        # Address security issues
        critical_security = [
            insight
            for insight in self.analytics.security_insights
            if insight.severity == RiskLevel.CRITICAL
        ]
        if critical_security:
            self.analytics.refactoring_suggestions.append(
                {
                    "type": "security_hardening",
                    "priority": "critical",
                    "description": f"Found {len(critical_security)} critical security issues",
                    "suggestion": "Address critical security concerns immediately",
                    "benefits": [
                        "Improved security posture",
                        "Reduced risk",
                        "Compliance",
                    ],
                    "estimated_effort": "varies",
                }
            )

    def _generate_insights(self) -> None:
        """Generate high-level insights about the infrastructure"""
        print("🔍 Generating insights...")

        # Summary insight
        complexity_assessment = "low"
        if self.analytics.cognitive_complexity > 500:
            complexity_assessment = "very high"
        elif self.analytics.cognitive_complexity > 300:
            complexity_assessment = "high"
        elif self.analytics.cognitive_complexity > 150:
            complexity_assessment = "moderate"

        # Architecture assessment
        if self.analytics.architecture_quality_score > 80:
            quality_assessment = "excellent"
        elif self.analytics.architecture_quality_score > 60:
            quality_assessment = "good"
        elif self.analytics.architecture_quality_score > 40:
            quality_assessment = "fair"
        else:
            quality_assessment = "needs improvement"

        print(f"   Complexity: {complexity_assessment}")
        print(
            f"   Architecture Quality: {quality_assessment} ({self.analytics.architecture_quality_score:.1f}/100)"
        )
        print(
            f"   Maintainability Index: {self.analytics.maintainability_index:.1f}/100"
        )
        print(f"   Technical Debt Score: {self.analytics.technical_debt_score:.1f}")
