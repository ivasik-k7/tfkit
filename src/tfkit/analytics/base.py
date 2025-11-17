import random
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

from tfkit.analytics.models import (
    ClusterMetrics,
    ComplexityLevel,
    ComponentMetrics,
    ComponentType,
    GraphAnalytics,
    NodeMetrics,
    PathMetrics,
)
from tfkit.graph.models import GraphData, Link, LinkType, Node, NodeState, NodeType


class TerraformGraphAnalytics:
    """Terraform-specific graph analytics with meaningful metrics"""

    def __init__(self, graph_data: GraphData):
        self.graph = graph_data
        self.analytics = GraphAnalytics()

        # Build optimized data structures
        self._adjacency_list: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: {"in": set(), "out": set()}
        )
        self._link_map: Dict[Tuple[str, str], Link] = {}
        self._node_map: Dict[str, Node] = {}

        self._build_optimized_structures()

    def _build_optimized_structures(self) -> None:
        """Build optimized adjacency list and lookup maps"""
        for node in self.graph.nodes.values():
            self._node_map[node.id] = node

        for link in self.graph.links:
            self._adjacency_list[link.source]["out"].add(link.target)
            self._adjacency_list[link.target]["in"].add(link.source)
            self._link_map[(link.source, link.target)] = link

    def analyze(self) -> GraphAnalytics:
        """Perform Terraform-specific graph analysis"""
        print("🔍 Starting Terraform-specific analytics...")

        self._compute_basic_statistics()
        self._compute_terraform_distributions()
        self._compute_terraform_connectivity()
        self._compute_terraform_node_metrics()
        self._identify_terraform_special_nodes()
        self._analyze_terraform_paths()
        self._analyze_terraform_components()
        self._analyze_resource_clusters()
        self._analyze_provider_relationships()
        self._analyze_module_structure()
        self._detect_terraform_anomalies()
        self._analyze_terraform_risks()
        self._compute_terraform_complexity()

        print("✅ Terraform analytics completed!")
        return self.analytics

    def _compute_basic_statistics(self) -> None:
        """Compute basic graph statistics"""
        self.analytics.total_nodes = len(self.graph.nodes)
        self.analytics.total_edges = len(self.graph.links)

    def _compute_terraform_distributions(self) -> None:
        """Compute Terraform-specific distributions"""
        resource_types = defaultdict(int)
        provider_types = defaultdict(int)

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

            # Resource type distribution
            if node.data.resource_type:
                resource_types[node.data.resource_type] += 1

            # Provider distribution
            if node.data.provider:
                provider_types[node.data.provider] += 1

        # Store additional distributions
        self.analytics.provider_distribution = dict(provider_types)

        # Link type distribution
        for link in self.graph.links:
            self.analytics.link_type_distribution[link.link_type] = (
                self.analytics.link_type_distribution.get(link.link_type, 0) + 1
            )

    def _compute_terraform_connectivity(self) -> None:
        """Compute Terraform-specific connectivity metrics - FIXED"""
        if self.analytics.total_nodes == 0:
            return

        # Basic degree metrics
        in_degrees = []
        out_degrees = []
        resource_degrees = []
        local_degrees = []
        variable_degrees = []

        for node_id, node in self._node_map.items():
            in_degree = len(self._adjacency_list[node_id]["in"])
            out_degree = len(self._adjacency_list[node_id]["out"])

            in_degrees.append(in_degree)
            out_degrees.append(out_degree)

            # Terraform-specific degree analysis
            if node.type == NodeType.RESOURCE:
                resource_degrees.append(in_degree + out_degree)
            elif node.type == NodeType.LOCAL:
                local_degrees.append(in_degree + out_degree)
            elif node.type == NodeType.VARIABLE:
                variable_degrees.append(in_degree + out_degree)

        self.analytics.avg_in_degree = (
            sum(in_degrees) / len(in_degrees) if in_degrees else 0
        )
        self.analytics.avg_out_degree = (
            sum(out_degrees) / len(out_degrees) if out_degrees else 0
        )
        self.analytics.max_in_degree = max(in_degrees) if in_degrees else 0
        self.analytics.max_out_degree = max(out_degrees) if out_degrees else 0

        # Terraform-specific averages
        self.analytics.avg_resource_degree = (
            sum(resource_degrees) / len(resource_degrees) if resource_degrees else 0
        )
        self.analytics.avg_local_degree = (
            sum(local_degrees) / len(local_degrees) if local_degrees else 0
        )
        self.analytics.avg_variable_degree = (
            sum(variable_degrees) / len(variable_degrees) if variable_degrees else 0
        )

    def _compute_terraform_node_metrics(self) -> None:
        """Compute Terraform-specific node metrics"""
        print("📊 Computing node metrics...")

        # First pass: basic metrics
        for node_id, node in self._node_map.items():
            metrics = NodeMetrics(node_id=node_id)
            metrics.in_degree = len(self._adjacency_list[node_id]["in"])
            metrics.out_degree = len(self._adjacency_list[node_id]["out"])
            metrics.total_degree = metrics.in_degree + metrics.out_degree

            # Terraform-specific metrics
            metrics.dependency_chain_length = self._calculate_dependency_chain_length(
                node_id
            )
            metrics.shortest_paths_count = self._count_shortest_paths_through(node_id)

            self.analytics.node_metrics[node_id] = metrics

        # Second pass: centrality metrics (optimized for Terraform graphs)
        self._compute_terraform_centrality()

        # Third pass: complexity classification
        self._classify_terraform_complexity()

    def _compute_terraform_centrality(self) -> None:
        """Compute centrality metrics optimized for Terraform dependency graphs"""
        print("🎯 Computing centrality...")

        # Betweenness centrality (simplified for Terraform)
        betweenness = defaultdict(float)
        nodes_list = list(self._node_map.keys())

        # Sample-based betweenness for large graphs
        sample_size = min(50, len(nodes_list))
        sample_nodes = (
            random.sample(nodes_list, sample_size)
            if len(nodes_list) > 50
            else nodes_list
        )

        for source in sample_nodes:
            # BFS from source
            distances = {source: 0}
            predecessors = defaultdict(list)
            queue = deque([source])

            while queue:
                v = queue.popleft()
                for w in self._adjacency_list[v]["out"]:
                    if w not in distances:
                        distances[w] = distances[v] + 1
                        queue.append(w)
                        predecessors[w].append(v)
                    elif distances[w] == distances[v] + 1:
                        predecessors[w].append(v)

            # Accumulate betweenness
            dependency = defaultdict(float)
            nodes_by_distance = sorted(
                distances.keys(), key=lambda x: distances[x], reverse=True
            )

            for w in nodes_by_distance:
                for v in predecessors[w]:
                    dependency[v] += (1 + dependency[w]) / len(predecessors[w])
                if w != source:
                    betweenness[w] += dependency[w]

        # Normalize and update
        if sample_nodes:
            scale = 1.0 / (len(sample_nodes) * (len(self._node_map) - 1))
            for node_id in betweenness:
                betweenness[node_id] *= scale
                if node_id in self.analytics.node_metrics:
                    self.analytics.node_metrics[
                        node_id
                    ].betweenness_centrality = betweenness[node_id]

        # PageRank for Terraform (resource-focused)
        self._compute_terraform_pagerank()

    def _compute_terraform_pagerank(
        self, damping: float = 0.85, max_iter: int = 50
    ) -> None:
        """Compute PageRank optimized for Terraform dependency graphs"""
        n = len(self._node_map)
        if n == 0:
            return

        pagerank = {node_id: 1.0 / n for node_id in self._node_map.keys()}

        for _ in range(max_iter):
            new_pagerank = {}
            total_rank = 0.0

            for node_id in self._node_map.keys():
                rank = (1 - damping) / n

                # Only consider incoming links from resources for more meaningful results
                for predecessor in self._adjacency_list[node_id]["in"]:
                    pred_node = self._node_map[predecessor]
                    out_degree = len(self._adjacency_list[predecessor]["out"])

                    # Weight resources higher in Terraform context
                    weight_multiplier = (
                        2.0 if pred_node.type == NodeType.RESOURCE else 1.0
                    )

                    if out_degree > 0:
                        rank += (
                            damping
                            * (pagerank[predecessor] / out_degree)
                            * weight_multiplier
                        )

                new_pagerank[node_id] = rank
                total_rank += rank

            # Normalize
            if total_rank > 0:
                for node_id in new_pagerank:
                    new_pagerank[node_id] /= total_rank

            pagerank = new_pagerank

        # Update metrics
        for node_id, value in pagerank.items():
            if node_id in self.analytics.node_metrics:
                self.analytics.node_metrics[node_id].pagerank = value

    def _calculate_dependency_chain_length(self, node_id: str) -> int:
        """Calculate the longest dependency chain this node participates in"""
        # BFS to find longest path through this node
        max_length = 0

        # Look backwards
        queue = deque([(node_id, 0)])
        visited = set([node_id])

        while queue:
            current, length = queue.popleft()
            max_length = max(max_length, length)

            for predecessor in self._adjacency_list[current]["in"]:
                if predecessor not in visited:
                    visited.add(predecessor)
                    queue.append((predecessor, length + 1))

        return max_length

    def _count_shortest_paths_through(self, node_id: str) -> int:
        """Count how many shortest paths go through this node"""
        count = 0
        nodes_list = list(self._node_map.keys())

        # Sample pairs for performance
        sample_size = min(30, len(nodes_list))
        if sample_size < 2:
            return 0

        sample_pairs = []
        for i in range(sample_size):
            for j in range(i + 1, sample_size):
                sample_pairs.append((nodes_list[i], nodes_list[j]))

        for start, end in sample_pairs:
            if start == end or start == node_id or end == node_id:
                continue

            # BFS to find if node_id is on shortest path
            distances = {start: 0}
            queue = deque([start])
            found = False

            while queue and not found:
                current = queue.popleft()
                for neighbor in self._adjacency_list[current]["out"]:
                    if neighbor not in distances:
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)

                        if neighbor == node_id and end in distances:
                            # Check if this is part of shortest path to end
                            if distances[end] == distances[
                                node_id
                            ] + self._get_distance(node_id, end):
                                count += 1
                                found = True
                                break

        return count

    def _get_distance(self, start: str, end: str) -> int:
        """Get shortest distance between two nodes"""
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

        return -1  # No path

    def _classify_terraform_complexity(self) -> None:
        """Classify node complexity based on Terraform-specific factors"""
        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Terraform-specific complexity score
            complexity_score = 0

            # Base on degree
            complexity_score += metrics.total_degree * 0.5

            # Resources are more complex than variables/locals
            if node.type == NodeType.RESOURCE:
                complexity_score += 3.0
            elif node.type == NodeType.LOCAL:
                complexity_score += 1.0
            elif node.type == NodeType.VARIABLE:
                complexity_score += 0.5

            # Consider dependency chain length
            complexity_score += metrics.dependency_chain_length * 0.3

            # Consider betweenness (if computed)
            complexity_score += metrics.betweenness_centrality * 20

            # Node state factors
            if node.data.state in [NodeState.HUB, NodeState.BRIDGE]:
                complexity_score += 2.0
            if node.data.state in [NodeState.UNRESOLVED, NodeState.INVALID]:
                complexity_score += 5.0

            # Classify based on score
            if complexity_score > 15:
                metrics.complexity_level = ComplexityLevel.CRITICAL
                metrics.is_critical = True
            elif complexity_score > 8:
                metrics.complexity_level = ComplexityLevel.HIGH
            elif complexity_score > 4:
                metrics.complexity_level = ComplexityLevel.MEDIUM
            else:
                metrics.complexity_level = ComplexityLevel.LOW

    # def _compute_clustering_coefficients(self) -> None:
    #     """Compute clustering coefficient for all nodes - FIXED"""
    #     total_coefficient = 0.0
    #     nodes_with_coefficient = 0

    #     for node_id in self._node_map.keys():
    #         neighbors = (
    #             self._adjacency_list[node_id]["in"]
    #             | self._adjacency_list[node_id]["out"]
    #         )

    #         # Remove self from neighbors (in case of self-loops)
    #         neighbors = neighbors - {node_id}

    #         if len(neighbors) < 2:
    #             continue

    #         # Count edges between neighbors
    #         edges_between = 0
    #         neighbors_list = list(neighbors)

    #         for i, n1 in enumerate(neighbors_list):
    #             for n2 in neighbors_list[i + 1 :]:
    #                 # Check if n1 and n2 are connected in either direction
    #                 if (
    #                     n2 in self._adjacency_list[n1]["out"]
    #                     or n1 in self._adjacency_list[n2]["out"]
    #                     or n2 in self._adjacency_list[n1]["in"]
    #                     or n1 in self._adjacency_list[n2]["in"]
    #                 ):
    #                     edges_between += 1

    #         # Clustering coefficient
    #         possible_edges = len(neighbors) * (len(neighbors) - 1) / 2
    #         if possible_edges > 0:
    #             clustering = edges_between / possible_edges
    #             self.analytics.node_metrics[node_id].clustering_coefficient = clustering
    #             total_coefficient += clustering
    #             nodes_with_coefficient += 1

    #     # Average clustering coefficient
    #     if nodes_with_coefficient > 0:
    #         self.analytics.avg_clustering_coefficient = (
    #             total_coefficient / nodes_with_coefficient
    #         )
    #     else:
    #         self.analytics.avg_clustering_coefficient = 0.0

    def _identify_terraform_special_nodes(self) -> None:
        """Identify Terraform-specific special nodes - FIXED"""
        print("🎯 Identifying special nodes...")

        metrics_list = list(self.analytics.node_metrics.values())
        if not metrics_list:
            return

        # Hub nodes: high out-degree AND meaningful connections
        hub_candidates = []
        for m in metrics_list:
            node = self._node_map[m.node_id]
            # Locals/variables with high out-degree are often configuration hubs
            if m.out_degree > max(
                2, self.analytics.avg_out_degree * 1.5
            ) and node.type in [NodeType.LOCAL, NodeType.RESOURCE, NodeType.PROVIDER]:
                hub_candidates.append(m)

        hub_candidates.sort(key=lambda m: m.out_degree, reverse=True)
        self.analytics.hub_nodes = [m.node_id for m in hub_candidates[:10]]

        # Authority nodes: high in-degree AND meaningful sinks
        authority_candidates = []
        for m in metrics_list:
            node = self._node_map[m.node_id]
            # Resources and outputs are meaningful authority nodes
            if m.in_degree > max(
                2, self.analytics.avg_in_degree * 1.5
            ) and node.type in [NodeType.RESOURCE, NodeType.OUTPUT, NodeType.LOCAL]:
                authority_candidates.append(m)

        authority_candidates.sort(key=lambda m: m.in_degree, reverse=True)
        self.analytics.authority_nodes = [m.node_id for m in authority_candidates[:10]]

        # Bottleneck nodes: high betweenness centrality
        bottleneck_candidates = [
            m for m in metrics_list if m.betweenness_centrality > 0.01
        ]  # Lower threshold
        bottleneck_candidates.sort(key=lambda m: m.betweenness_centrality, reverse=True)
        self.analytics.bottleneck_nodes = [
            m.node_id for m in bottleneck_candidates[:10]
        ]

        for m in bottleneck_candidates[:5]:
            m.is_bottleneck = True

        # Debug output to understand the graph structure
        print(
            f"   Top hubs by out-degree: {[(m.node_id, m.out_degree) for m in hub_candidates[:3]]}"
        )
        print(
            f"   Top authorities by in-degree: {[(m.node_id, m.in_degree) for m in authority_candidates[:3]]}"
        )
        print(
            f"   Top bottlenecks by betweenness: {[(m.node_id, m.betweenness_centrality) for m in bottleneck_candidates[:3]]}"
        )

    def _analyze_terraform_paths(self) -> None:
        """Analyze Terraform-specific dependency paths"""
        print("🛣️ Analyzing dependency paths...")

        # Find critical resource dependency paths
        self._find_resource_dependency_chains()

        # Find configuration propagation paths
        self._find_configuration_paths()

        # Compute path statistics
        self._compute_terraform_path_statistics()

    def _find_resource_dependency_chains(self) -> None:
        """Find dependency chains between resources"""
        resource_nodes = [
            node_id
            for node_id, node in self._node_map.items()
            if node.type == NodeType.RESOURCE
        ]

        critical_paths = []

        # Find long dependency chains between resources
        for resource in resource_nodes[:20]:  # Sample for performance
            paths = self._find_long_chains_from(resource, max_length=8)
            critical_paths.extend(paths)

        # Take top paths by length and complexity
        critical_paths.sort(key=len, reverse=True)
        self.analytics.critical_paths = [
            self._create_path_metrics(p) for p in critical_paths[:10]
        ]

    def _find_long_chains_from(
        self, start: str, max_length: int = 8
    ) -> List[List[str]]:
        """Find long dependency chains starting from a node"""
        chains = []
        stack = [(start, [start])]

        while stack:
            node, path = stack.pop()

            if len(path) >= max_length:
                chains.append(path)
                continue

            # Only follow resource dependencies for meaningful chains
            outgoing = [
                n
                for n in self._adjacency_list[node]["out"]
                if self._node_map[n].type == NodeType.RESOURCE
            ]

            for neighbor in outgoing:
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor]))

        return chains

    def _find_configuration_paths(self) -> None:
        """Find paths from variables to resources (configuration propagation)"""
        variable_nodes = [
            node_id
            for node_id, node in self._node_map.items()
            if node.type == NodeType.VARIABLE
        ]
        resource_nodes = [
            node_id
            for node_id, node in self._node_map.items()
            if node.type == NodeType.RESOURCE
        ]

        config_paths = []

        # Sample variables and resources for performance
        sample_vars = variable_nodes[:10]
        sample_resources = resource_nodes[:20]

        for var_node in sample_vars:
            for resource_node in sample_resources:
                paths = self._find_all_paths(var_node, resource_node, max_length=6)
                if paths:
                    # Take the shortest path as most relevant
                    shortest_path = min(paths, key=len)
                    config_paths.append(shortest_path)

        # Create path metrics
        self.analytics.high_risk_paths = [
            self._create_path_metrics(p) for p in config_paths[:15]
        ]

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
        """Create PathMetrics for a path"""
        metrics = PathMetrics(path=path, length=len(path))

        # Collect node types and calculate risk
        node_types = []
        risk_score = 0.0

        for i, node_id in enumerate(path):
            node = self._node_map[node_id]
            node_types.append(node.type)

            # Risk factors
            if node.type == NodeType.RESOURCE:
                risk_score += 2.0
            elif node.type == NodeType.LOCAL:
                risk_score += 1.0

            # Long chains are riskier
            risk_score += i * 0.5

            # Implicit dependencies are riskier
            if i < len(path) - 1:
                link = self._link_map.get((node_id, path[i + 1]))
                if link and link.link_type == LinkType.IMPLICIT:
                    risk_score += 3.0

        metrics.node_types = node_types
        metrics.risk_score = risk_score

        return metrics

    def _compute_terraform_path_statistics(self) -> None:
        """Compute Terraform-specific path statistics"""
        # Sample nodes for performance
        sample_nodes = list(self._node_map.keys())[:50]
        all_distances = []

        for source in sample_nodes:
            distances = self._bfs_distances(source)
            all_distances.extend(distances.values())

        if all_distances:
            self.analytics.avg_path_length = sum(all_distances) / len(all_distances)
            self.analytics.diameter = max(all_distances)

    def _bfs_distances(self, start: str) -> Dict[str, int]:
        """BFS to compute distances from start node"""
        distances = {start: 0}
        queue = deque([start])

        while queue:
            node = queue.popleft()
            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)

        return distances

    def _analyze_terraform_components(self) -> None:
        """Analyze Terraform-specific components"""
        print("🔗 Analyzing components...")

        visited = set()
        component_id = 0

        for node_id in self._node_map.keys():
            if node_id in visited:
                continue

            component = self._find_terraform_component(node_id)
            visited.update(component)

            if len(component) > 1:  # Only meaningful components
                metrics = self._compute_component_metrics(component_id, component)
                self.analytics.components[component_id] = metrics
                component_id += 1

        self.analytics.total_components = component_id

        # Find circular dependencies
        self._find_terraform_circular_dependencies()

    def _find_terraform_component(self, start: str) -> Set[str]:
        """Find connected component with Terraform-aware logic"""
        component = set()
        stack = [start]

        while stack:
            node = stack.pop()
            if node in component:
                continue

            component.add(node)

            # Add neighbors (consider both directions for Terraform)
            neighbors = (
                self._adjacency_list[node]["in"] | self._adjacency_list[node]["out"]
            )
            stack.extend(neighbors - component)

        return component

    def _compute_component_metrics(
        self, component_id: int, nodes: Set[str]
    ) -> ComponentMetrics:
        """Compute metrics for a component"""
        metrics = ComponentMetrics(
            component_id=component_id, node_ids=nodes, size=len(nodes)
        )

        # Count internal edges
        internal_edges = 0
        for node in nodes:
            for neighbor in self._adjacency_list[node]["out"]:
                if neighbor in nodes:
                    internal_edges += 1

        # Density
        max_possible = len(nodes) * (len(nodes) - 1)
        if max_possible > 0:
            metrics.density = internal_edges / max_possible

        # Classify component type
        metrics.component_type = self._classify_terraform_component(
            nodes, internal_edges
        )

        return metrics

    def _classify_terraform_component(
        self, nodes: Set[str], edge_count: int
    ) -> ComponentType:
        """Classify component type for Terraform"""
        if len(nodes) == 1:
            return ComponentType.ISOLATED

        # Check if it's a resource cluster
        resource_count = sum(
            1 for n in nodes if self._node_map[n].type == NodeType.RESOURCE
        )
        if resource_count / len(nodes) > 0.7:
            return ComponentType.COMPLEX

        # Check for tree structure
        if edge_count == len(nodes) - 1:
            return ComponentType.TREE

        return ComponentType.COMPLEX

    def _find_terraform_circular_dependencies(self) -> None:
        """Find circular dependencies in Terraform graph"""
        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs(node, path):
            if node in recursion_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                if len(cycle) > 1:  # Meaningful cycle
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self._adjacency_list[node]["out"]:
                dfs(neighbor, path + [neighbor])

            recursion_stack.remove(node)

        # Start from each node not yet visited
        for node_id in self._node_map.keys():
            if node_id not in visited:
                dfs(node_id, [node_id])

        # Remove duplicates and store
        unique_cycles = []
        for cycle in cycles:
            normalized = tuple(sorted(cycle))  # Normalize for comparison
            if normalized not in unique_cycles:
                unique_cycles.append(normalized)
                self.analytics.circular_dependencies.append(cycle)

    def _analyze_resource_clusters(self) -> None:
        """Analyze clusters of related resources"""
        print("🏗️ Analyzing resource clusters...")

        # Group resources by provider and type
        provider_clusters = defaultdict(set)
        type_clusters = defaultdict(set)

        for node_id, node in self._node_map.items():
            if node.type == NodeType.RESOURCE and node.data.resource_type:
                # Cluster by provider
                provider = (
                    node.data.resource_type.split("_")[0]
                    if "_" in node.data.resource_type
                    else "unknown"
                )
                provider_clusters[provider].add(node_id)

                # Cluster by resource type
                type_clusters[node.data.resource_type].add(node_id)

        # Create cluster metrics
        cluster_id = 0
        all_clusters = list(provider_clusters.values()) + list(type_clusters.values())

        for cluster_nodes in all_clusters:
            if len(cluster_nodes) > 1:  # Meaningful clusters
                metrics = self._compute_cluster_metrics(cluster_id, cluster_nodes)
                self.analytics.clusters[cluster_id] = metrics
                cluster_id += 1

    def _compute_cluster_metrics(
        self, cluster_id: int, nodes: Set[str]
    ) -> ClusterMetrics:
        """Compute metrics for a resource cluster"""
        metrics = ClusterMetrics(cluster_id=cluster_id, node_ids=nodes)

        # Analyze cluster composition
        type_counts = defaultdict(int)
        provider_counts = defaultdict(int)

        for node_id in nodes:
            node = self._node_map[node_id]
            type_counts[node.type] += 1
            if node.data.provider:
                provider_counts[node.data.provider] += 1

        if type_counts:
            metrics.dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        if provider_counts:
            metrics.dominant_provider = max(
                provider_counts.items(), key=lambda x: x[1]
            )[0]

        return metrics

    def _analyze_provider_relationships(self) -> None:
        """Analyze relationships between different providers"""
        provider_nodes = defaultdict(list)

        for node in self._node_map.values():
            if node.data.provider:
                provider_nodes[node.data.provider].append(node.id)

        # Provider distribution
        for provider, nodes in provider_nodes.items():
            self.analytics.provider_distribution[provider] = len(nodes)

        # Provider coupling
        providers = list(provider_nodes.keys())
        for i, provider_a in enumerate(providers):
            for provider_b in providers[i + 1 :]:
                coupling = self._calculate_provider_coupling(
                    provider_a, provider_b, provider_nodes
                )
                if coupling > 0:
                    self.analytics.provider_coupling[(provider_a, provider_b)] = (
                        coupling
                    )

    def _calculate_provider_coupling(
        self, provider_a: str, provider_b: str, provider_nodes: Dict[str, List[str]]
    ) -> int:
        """Calculate coupling between two providers"""
        coupling = 0
        nodes_a = provider_nodes[provider_a]
        nodes_b = provider_nodes[provider_b]

        for node_a in nodes_a:
            for node_b in nodes_b:
                # Check for dependencies in both directions
                if (
                    node_b in self._adjacency_list[node_a]["out"]
                    or node_a in self._adjacency_list[node_b]["out"]
                ):
                    coupling += 1

        return coupling

    def _analyze_module_structure(self) -> None:
        """Analyze module structure in Terraform configuration"""
        # Group nodes by logical modules based on naming and relationships
        module_groups = defaultdict(set)

        for node_id, node in self._node_map.items():
            # Use node ID patterns to infer modules
            if "." in node_id:
                parts = node_id.split(".")
                if parts[0] == "module":
                    # module.module_name.resource
                    module_groups[parts[1]].add(node_id)
                elif parts[0] == "local":
                    # local.module_name.attribute
                    if len(parts) > 1:
                        module_groups[parts[1]].add(node_id)
                else:
                    # provider_resource.name - group by provider
                    provider = parts[0].split("_")[0] if "_" in parts[0] else "core"
                    module_groups[provider].add(node_id)
            else:
                module_groups["root"].add(node_id)

        # Module distribution
        for module, nodes in module_groups.items():
            if len(nodes) > 1:  # Only meaningful modules
                self.analytics.module_distribution[module] = len(nodes)

        # Module depth (simplified)
        for node in self._node_map.values():
            depth = self._calculate_terraform_depth(node.id)
            self.analytics.module_depth_distribution[depth] = (
                self.analytics.module_depth_distribution.get(depth, 0) + 1
            )

    def _calculate_terraform_depth(self, node_id: str) -> int:
        """Calculate depth in Terraform dependency tree"""
        # BFS from root nodes to find depth
        visited = set()
        queue = deque()

        # Find root nodes (no incoming dependencies)
        for nid in self._node_map.keys():
            if len(self._adjacency_list[nid]["in"]) == 0:
                queue.append((nid, 0))
                visited.add(nid)

        depths = {}
        while queue:
            current, depth = queue.popleft()
            depths[current] = depth

            for neighbor in self._adjacency_list[current]["out"]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return depths.get(node_id, 0)

    def _detect_terraform_anomalies(self) -> None:
        """Detect Terraform-specific anomalies"""
        print("🚨 Detecting anomalies...")

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Isolated resources (should have dependencies)
            if (
                node.type == NodeType.RESOURCE
                and metrics.total_degree == 0
                and node.data.state != NodeState.UNUSED
            ):
                self.analytics.isolated_nodes.append(node_id)

            # Orphaned nodes (no inputs but has outputs)
            if metrics.in_degree == 0 and metrics.out_degree > 0:
                # Variables are expected to have no inputs
                if node.type != NodeType.VARIABLE:
                    self.analytics.orphaned_nodes.append(node_id)

            # Unused nodes (no outputs but has inputs)
            if metrics.out_degree == 0 and metrics.in_degree > 0:
                # Outputs are expected to have no outputs
                if node.type != NodeType.OUTPUT:
                    self.analytics.unused_nodes.append(node_id)

            # Over-connected nodes
            avg_degree = self.analytics.avg_in_degree + self.analytics.avg_out_degree
            if avg_degree > 0 and metrics.total_degree > avg_degree * 3:
                self.analytics.over_connected_nodes.append(node_id)

            # State-based anomalies
            if node.data.state in [NodeState.UNRESOLVED, NodeState.INVALID]:
                self.analytics.dependency_violations.append(
                    f"Invalid state: {node_id} has state {node.data.state}"
                )

    def _analyze_terraform_risks(self) -> None:
        """Analyze Terraform-specific risks"""
        print("⚠️ Analyzing risks...")

        risk_scores = []

        for node_id, metrics in self.analytics.node_metrics.items():
            node = self._node_map[node_id]

            # Base risk score
            risk_score = 0.0

            # Critical nodes are high risk
            if metrics.is_critical:
                risk_score += 10.0

            # Bottleneck nodes are high risk
            if metrics.is_bottleneck:
                risk_score += 8.0

            # High complexity
            if metrics.complexity_level == ComplexityLevel.CRITICAL:
                risk_score += 6.0
            elif metrics.complexity_level == ComplexityLevel.HIGH:
                risk_score += 3.0

            # Resource-specific risks
            if node.type == NodeType.RESOURCE:
                risk_score += 2.0

                # Count dependencies
                risk_score += min(metrics.total_degree * 0.5, 5.0)

            # State risks
            if node.data.state in [NodeState.UNRESOLVED, NodeState.INVALID]:
                risk_score += 8.0
            elif node.data.state in [NodeState.UNUSED, NodeState.ORPHAN]:
                risk_score += 3.0

            risk_scores.append((node_id, risk_score))

        # Sort and store high-risk nodes
        risk_scores.sort(key=lambda x: x[1], reverse=True)
        self.analytics.high_risk_nodes = risk_scores[:15]

        # Find implicit dependency risks
        self._find_implicit_dependency_risks()

    def _find_implicit_dependency_risks(self) -> None:
        """Find risks related to implicit dependencies"""
        for link in self.graph.links:
            if link.link_type == LinkType.IMPLICIT:
                source_node = self._node_map[link.source]
                target_node = self._node_map[link.target]

                # Implicit dependencies between different types are riskier
                if source_node.type != target_node.type:
                    self.analytics.dependency_violations.append(
                        f"Cross-type implicit dependency: {link.source} ({source_node.type}) -> {link.target} ({target_node.type})"
                    )

    def _compute_terraform_complexity(self) -> None:
        """Compute Terraform-specific complexity metrics"""
        print("📈 Computing complexity metrics...")

        # Cyclomatic complexity (simplified)
        self.analytics.cyclomatic_complexity = (
            self.analytics.total_edges
            - self.analytics.total_nodes
            + 2 * self.analytics.total_components
        )

        # Coupling score (external dependencies)
        total_external = 0
        total_dependencies = 0

        for node_id in self._node_map.keys():
            node = self._node_map[node_id]
            for neighbor in self._adjacency_list[node_id]["out"]:
                total_dependencies += 1

                # Check if this is cross-provider
                if (
                    node.data.provider
                    and self._node_map[neighbor].data.provider
                    and node.data.provider != self._node_map[neighbor].data.provider
                ):
                    total_external += 1

        self.analytics.coupling_score = (
            total_external / total_dependencies if total_dependencies > 0 else 0
        )

        # Cohesion score (simplified)
        if self.analytics.clusters:
            cohesion_scores = [
                len(cluster.node_ids) / self.analytics.total_nodes
                for cluster in self.analytics.clusters.values()
            ]
            self.analytics.cohesion_score = sum(cohesion_scores) / len(cohesion_scores)
        else:
            self.analytics.cohesion_score = 0.0

        # Maintainability index (Terraform-specific)
        self.analytics.maintainability_index = (
            self._calculate_terraform_maintainability()
        )

    def _calculate_terraform_maintainability(self) -> float:
        """Calculate Terraform-specific maintainability index"""
        base_score = 100.0

        # Penalties
        penalties = 0.0

        # Size penalty
        penalties += min(self.analytics.total_nodes * 0.1, 20.0)
        penalties += min(self.analytics.total_edges * 0.05, 15.0)

        # Complexity penalty
        penalties += min(self.analytics.cyclomatic_complexity * 0.2, 25.0)

        # Coupling penalty
        penalties += self.analytics.coupling_score * 15.0

        # Risk penalty
        penalties += len(self.analytics.high_risk_nodes) * 0.5
        penalties += len(self.analytics.circular_dependencies) * 3.0
        penalties += len(self.analytics.dependency_violations) * 1.0

        # Anomaly penalty
        penalties += len(self.analytics.isolated_nodes) * 0.3
        penalties += len(self.analytics.orphaned_nodes) * 0.5
        penalties += len(self.analytics.unused_nodes) * 0.2

        final_score = max(0.0, base_score - penalties)
        return final_score
