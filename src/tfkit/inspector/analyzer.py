"""
Comprehensive Terraform Dependency Analyzer.
Analyzes and resolves all dependencies between Terraform blocks.
"""

import re
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from tfkit.inspector.models import (
    ReferenceType,
    TerraformBlock,
    TerraformModule,
    TerraformObjectType,
    TerraformReference,
)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""

    address: str
    block: TerraformBlock
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    depth: int = 0
    is_variable: bool = False
    is_local: bool = False
    is_output: bool = False
    is_resource: bool = False


@dataclass
class DependencyAnalysis:
    """Complete dependency analysis results."""

    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    dependency_graph: Dict[str, Set[str]] = field(default_factory=dict)
    reverse_dependency_graph: Dict[str, Set[str]] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    orphaned_nodes: Set[str] = field(default_factory=set)
    root_nodes: Set[str] = field(default_factory=set)
    leaf_nodes: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "total_nodes": len(self.nodes),
            "total_dependencies": sum(
                len(deps) for deps in self.dependency_graph.values()
            ),
            "execution_order": self.execution_order,
            "circular_dependencies": self.circular_dependencies,
            "orphaned_nodes": list(self.orphaned_nodes),
            "root_nodes": list(self.root_nodes),
            "leaf_nodes": list(self.leaf_nodes),
            "nodes": {
                address: {
                    "address": node.address,
                    "type": node.block.block_type.value,
                    "dependencies": list(node.dependencies),
                    "dependents": list(node.dependents),
                    "depth": node.depth,
                }
                for address, node in self.nodes.items()
            },
        }


# ========================================================================
# EXPORT STRATEGY PATTERN
# ========================================================================


class ExportStrategy(ABC):
    """Abstract base class for export strategies."""

    @abstractmethod
    def export(self, analysis: DependencyAnalysis, output_file: str) -> None:
        """
        Export dependency analysis in specific format.

        Args:
            analysis: DependencyAnalysis to export
            output_file: Path to output file
        """
        pass


class DOTExportStrategy(ExportStrategy):
    """Export dependency graph in DOT format for visualization."""

    def export(self, analysis: DependencyAnalysis, output_file: str) -> None:
        """Export to DOT format."""
        with open(output_file, "w") as f:
            f.write("digraph TerraformDependencies {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box];\n\n")

            # Define nodes with colors based on type
            for address, node in analysis.nodes.items():
                color = self._get_node_color(node)
                label = address.replace('"', '\\"')
                f.write(
                    f'  "{address}" [label="{label}", style=filled, fillcolor="{color}"];\n'
                )

            f.write("\n")

            # Define edges
            for from_addr, deps in analysis.dependency_graph.items():
                for to_addr in deps:
                    f.write(f'  "{from_addr}" -> "{to_addr}";\n')

            f.write("}\n")

    def _get_node_color(self, node: DependencyNode) -> str:
        """Get color for node based on type."""
        if node.is_variable:
            return "lightblue"
        elif node.is_local:
            return "lightgreen"
        elif node.is_output:
            return "lightyellow"
        elif node.is_resource:
            return "lightcoral"
        else:
            return "lightgray"


class MermaidExportStrategy(ExportStrategy):
    """Export dependency graph in Mermaid JS format."""

    def export(self, analysis: DependencyAnalysis, output_file: str) -> None:
        """Export to Mermaid format."""
        with open(output_file, "w") as f:
            f.write("graph TD\n")
            f.write(
                "    classDef variable fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n"
            )
            f.write("    classDef local fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n")
            f.write(
                "    classDef output fill:#fffde7,stroke:#f57f17,stroke-width:2px\n"
            )
            f.write(
                "    classDef resource fill:#ffebee,stroke:#c62828,stroke-width:2px\n"
            )
            f.write("    classDef data fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px\n")
            f.write(
                "    classDef module fill:#fff3e0,stroke:#ef6c00,stroke-width:2px\n"
            )
            f.write(
                "    classDef provider fill:#fff9c4,stroke:#f9a825,stroke-width:2px\n"
            )
            f.write(
                "    classDef default fill:#f5f5f5,stroke:#616161,stroke-width:2px\n\n"
            )

            # Group nodes by depth for better layout
            depth_groups = defaultdict(list)
            for address, node in analysis.nodes.items():
                depth_groups[node.depth].append((address, node))

            # Add subgraphs for each depth level
            for depth, nodes in sorted(depth_groups.items()):
                if depth == 0:
                    f.write(f"    %% Depth {depth} - Root nodes\n")
                else:
                    f.write(f"    %% Depth {depth}\n")

                for address, node in sorted(nodes):
                    node_id = self._sanitize_id(address)
                    label = self._create_node_label(node)
                    class_name = self._get_node_class(node)

                    f.write(f'    {node_id}["{label}"]\n')
                    f.write(f"    class {node_id} {class_name}\n")
                f.write("\n")

            # Add dependencies as edges
            f.write("    %% Dependencies\n")
            for from_addr, deps in analysis.dependency_graph.items():
                for to_addr in deps:
                    from_id = self._sanitize_id(from_addr)
                    to_id = self._sanitize_id(to_addr)
                    f.write(f"    {from_id} --> {to_id}\n")

            # Highlight circular dependencies
            if analysis.circular_dependencies:
                f.write("\n    %% Circular Dependencies (highlighted)\n")
                f.write(
                    "    linkStyle default fill:none,stroke:#ff0000,stroke-width:2px,stroke-dasharray:5,5\n"
                )
                for i, cycle in enumerate(analysis.circular_dependencies):
                    f.write(f"    %% Cycle {i + 1}\n")
                    for j in range(len(cycle)):
                        # from_node = self._sanitize_id(cycle[j])
                        # to_node = self._sanitize_id(cycle[(j + 1) % len(cycle)])
                        f.write(
                            f"    linkStyle {self._get_edge_index(analysis, cycle[j], cycle[(j + 1) % len(cycle)])} stroke:#ff0000,stroke-width:3px,stroke-dasharray:0\n"
                        )

    def _sanitize_id(self, address: str) -> str:
        """Convert address to valid Mermaid ID."""
        # Replace problematic characters
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", address)
        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = "n" + sanitized
        return sanitized

    def _create_node_label(self, node: DependencyNode) -> str:
        """Create a formatted label for the node."""
        type_emoji = self._get_type_emoji(node)
        short_address = self._shorten_address(node.address)

        lines = [
            f"{type_emoji} {node.block.block_type.value.upper()}",
            f"`{short_address}`",
            f"Depth: {node.depth}",
            f"╭─ Dependencies: {len(node.dependencies)}",
            f"╰─ Dependents: {len(node.dependents)}",
        ]
        return "<br>".join(lines)

    def _get_type_emoji(self, node: DependencyNode) -> str:
        """Get emoji for node type."""
        emoji_map = {
            "variable": "📝",
            "local": "💬",
            "output": "📤",
            "resource": "🛠️",
            "data": "📊",
            "module": "📦",
            "provider": "⚙️",
        }

        node_type = node.block.block_type.value.lower()
        for key, emoji in emoji_map.items():
            if key in node_type:
                return emoji
        return "📄"

    def _get_node_class(self, node: DependencyNode) -> str:
        """Get CSS class for node based on type."""
        class_map = {
            "variable": "variable",
            "local": "local",
            "output": "output",
            "resource": "resource",
            "data": "data",
            "module": "module",
            "provider": "provider",
        }

        node_type = node.block.block_type.value.lower()
        for key, class_name in class_map.items():
            if key in node_type:
                return class_name
        return "default"

    def _shorten_address(self, address: str) -> str:
        """Shorten long addresses for better display."""
        if len(address) > 30:
            parts = address.split(".")
            if len(parts) > 3:
                return f"{parts[0]}.{parts[1]}...{parts[-1]}"
            elif len(parts) > 2:
                return f"{parts[0]}...{parts[-1]}"
        return address

    def _get_edge_index(
        self, analysis: DependencyAnalysis, from_addr: str, to_addr: str
    ) -> int:
        """Calculate edge index for styling (simplified)."""
        # This is a simplified implementation - in practice you'd need to track edge indices
        edge_count = 0
        for addr, deps in analysis.dependency_graph.items():
            for dep in deps:
                if addr == from_addr and dep == to_addr:
                    return edge_count
                edge_count += 1
        return 0


class ExportContext:
    """Context class for managing export strategies."""

    def __init__(self):
        self._strategies: Dict[str, ExportStrategy] = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default export strategies."""
        self.register_strategy("dot", DOTExportStrategy())
        self.register_strategy("mermaid", MermaidExportStrategy())

    def register_strategy(self, format_name: str, strategy: ExportStrategy):
        """
        Register a new export strategy.

        Args:
            format_name: Name of the format
            strategy: ExportStrategy instance
        """
        self._strategies[format_name.lower()] = strategy

    def get_strategy(self, format_name: str) -> ExportStrategy:
        """
        Get export strategy for specified format.

        Args:
            format_name: Name of the format

        Returns:
            ExportStrategy instance

        Raises:
            ValueError: If format is not supported
        """
        format_name = format_name.lower()
        if format_name not in self._strategies:
            supported_formats = ", ".join(self._strategies.keys())
            raise ValueError(
                f"Unsupported format: {format_name}. Supported formats: {supported_formats}"
            )
        return self._strategies[format_name]

    def export(
        self, analysis: DependencyAnalysis, output_file: str, format_name: str
    ) -> None:
        """
        Export analysis using specified format.

        Args:
            analysis: DependencyAnalysis to export
            output_file: Path to output file
            format_name: Name of the format to use
        """
        strategy = self.get_strategy(format_name)
        strategy.export(analysis, output_file)

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return list(self._strategies.keys())


class DependencyAnalyzer:
    """
    Analyzes Terraform module dependencies.
    Builds comprehensive dependency graphs and provides analysis utilities.
    """

    def __init__(self, module: TerraformModule):
        """
        Initialize analyzer with a Terraform module.

        Args:
            module: Parsed TerraformModule to analyze
        """
        self.module = module
        self.analysis = DependencyAnalysis()
        self.export_context = ExportContext()

    def analyze(self) -> DependencyAnalysis:
        """
        Perform complete dependency analysis.

        Returns:
            DependencyAnalysis with all computed information
        """
        # Step 1: Build nodes
        self._build_nodes()

        # Step 2: Extract dependencies from references
        self._extract_dependencies()

        # Step 3: Build dependency graphs
        self._build_dependency_graphs()

        # Step 4: Detect circular dependencies
        self._detect_circular_dependencies()

        # Step 5: Compute execution order (topological sort)
        self._compute_execution_order()

        # Step 6: Identify special nodes
        self._identify_special_nodes()

        # Step 7: Compute depths
        self._compute_depths()

        return self.analysis

    def export(self, output_file: str, format_name: str = "dot") -> None:
        """
        Export dependency analysis in specified format.

        Args:
            output_file: Path to output file
            format_name: Export format (dot, json, csv, graphml, txt)

        Raises:
            ValueError: If format is not supported
        """
        self.export_context.export(self.analysis, output_file, format_name)

    def get_supported_export_formats(self) -> List[str]:
        """
        Get list of supported export formats.

        Returns:
            List of supported format names
        """
        return self.export_context.get_supported_formats()

    # ========================================================================
    # STEP 1: BUILD NODES
    # ========================================================================

    def _build_nodes(self):
        """Build dependency nodes from all blocks in the module."""
        for file in self.module.files:
            for block in file.blocks:
                node = DependencyNode(
                    address=block.address,
                    block=block,
                    is_variable=block.block_type == TerraformObjectType.VARIABLE,
                    is_local=block.block_type == TerraformObjectType.LOCAL,
                    is_output=block.block_type == TerraformObjectType.OUTPUT,
                    is_resource=block.block_type == TerraformObjectType.RESOURCE,
                )
                self.analysis.nodes[block.address] = node

    # ========================================================================
    # STEP 2: EXTRACT DEPENDENCIES
    # ========================================================================

    def _extract_dependencies(self):
        """Extract all dependencies from block references."""
        for address, node in self.analysis.nodes.items():
            block = node.block

            # Extract from explicit depends_on
            for dep in block.depends_on:
                self._add_dependency(address, dep)

            # Extract from count/for_each meta-arguments
            if block.count:
                for ref in block.count.references:
                    dep = self._resolve_reference_to_address(ref)
                    if dep:
                        self._add_dependency(address, dep)

            if block.for_each:
                for ref in block.for_each.references:
                    dep = self._resolve_reference_to_address(ref)
                    if dep:
                        self._add_dependency(address, dep)

            # Extract from all attributes
            for attr in block.attributes.values():
                for ref in attr.value.references:
                    dep = self._resolve_reference_to_address(ref)
                    if dep:
                        self._add_dependency(address, dep)

                # Recursively extract from nested attributes
                self._extract_from_nested_attributes(address, attr.nested_attributes)

    def _extract_from_nested_attributes(self, address: str, nested_attrs: Dict):
        """Recursively extract dependencies from nested attributes."""
        for attr in nested_attrs.values():
            for ref in attr.value.references:
                dep = self._resolve_reference_to_address(ref)
                if dep:
                    self._add_dependency(address, dep)

            if attr.nested_attributes:
                self._extract_from_nested_attributes(address, attr.nested_attributes)

    def _resolve_reference_to_address(self, ref: TerraformReference) -> Optional[str]:
        """
        Resolve a TerraformReference to a block address.

        Args:
            ref: TerraformReference to resolve

        Returns:
            Block address string or None if cannot be resolved
        """
        # For variable, local, module, output references, the target is the address
        if ref.reference_type in (
            ReferenceType.VARIABLE,
            ReferenceType.LOCAL,
            ReferenceType.MODULE,
        ):
            return ref.target

        # For resource and data source references, the target is the address
        if ref.reference_type in (ReferenceType.RESOURCE, ReferenceType.DATA_SOURCE):
            return ref.target

        # Path, terraform, count, each, self references don't create dependencies
        return None

    def _add_dependency(self, from_address: str, to_address: str):
        """Add a dependency relationship."""
        if from_address == to_address:
            return  # Skip self-dependencies

        # Only add if the target exists
        if to_address in self.analysis.nodes:
            node = self.analysis.nodes[from_address]
            node.dependencies.add(to_address)

    # ========================================================================
    # STEP 3: BUILD DEPENDENCY GRAPHS
    # ========================================================================

    def _build_dependency_graphs(self):
        """Build forward and reverse dependency graphs."""
        # Forward graph: A -> B means A depends on B
        for address, node in self.analysis.nodes.items():
            self.analysis.dependency_graph[address] = node.dependencies.copy()

        # Reverse graph: A -> B means B depends on A (A is depended upon by B)
        self.analysis.reverse_dependency_graph = defaultdict(set)
        for address, deps in self.analysis.dependency_graph.items():
            for dep in deps:
                self.analysis.reverse_dependency_graph[dep].add(address)

        # Update dependents in nodes
        for address, dependents in self.analysis.reverse_dependency_graph.items():
            if address in self.analysis.nodes:
                self.analysis.nodes[address].dependents = dependents.copy()

    # ========================================================================
    # STEP 4: DETECT CIRCULAR DEPENDENCIES
    # ========================================================================

    def _detect_circular_dependencies(self):
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            """DFS to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.analysis.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.analysis.nodes:
            if node not in visited:
                dfs(node, [])

        self.analysis.circular_dependencies = cycles

    # ========================================================================
    # STEP 5: COMPUTE EXECUTION ORDER
    # ========================================================================

    def _compute_execution_order(self):
        """
        Compute execution order using Kahn's algorithm (topological sort).
        If circular dependencies exist, returns partial order.
        """
        # Create a copy of the dependency graph
        in_degree = {}
        for node in self.analysis.nodes:
            in_degree[node] = len(self.analysis.dependency_graph.get(node, set()))

        # Queue of nodes with no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])

        execution_order = []

        while queue:
            # Process nodes in stable order (alphabetically)
            current_batch = sorted(queue)
            queue.clear()

            for node in current_batch:
                execution_order.append(node)

                # Reduce in-degree for all dependents
                for dependent in self.analysis.reverse_dependency_graph.get(
                    node, set()
                ):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        self.analysis.execution_order = execution_order

        # Check if all nodes were processed
        if len(execution_order) != len(self.analysis.nodes):
            # Some nodes couldn't be ordered (circular dependencies)
            remaining = set(self.analysis.nodes.keys()) - set(execution_order)
            # Add remaining nodes at the end
            self.analysis.execution_order.extend(sorted(remaining))

    # ========================================================================
    # STEP 6: IDENTIFY SPECIAL NODES
    # ========================================================================

    def _identify_special_nodes(self):
        """Identify root nodes, leaf nodes, and orphaned nodes."""
        for address, node in self.analysis.nodes.items():
            # Root nodes: no dependencies (inputs)
            if not node.dependencies:
                self.analysis.root_nodes.add(address)

            # Leaf nodes: no dependents (outputs)
            if not node.dependents:
                self.analysis.leaf_nodes.add(address)

            # Orphaned nodes: no dependencies and no dependents
            if not node.dependencies and not node.dependents:
                self.analysis.orphaned_nodes.add(address)

    # ========================================================================
    # STEP 7: COMPUTE DEPTHS
    # ========================================================================

    def _compute_depths(self):
        """Compute depth of each node in the dependency tree."""
        # Depth = longest path from any root node
        depths = dict.fromkeys(self.analysis.nodes, -1)

        def compute_depth(node: str, visited: Set[str]) -> int:
            """Recursively compute depth."""
            if node in visited:
                return 0  # Circular dependency, return 0

            if depths[node] != -1:
                return depths[node]

            visited.add(node)

            dependencies = self.analysis.dependency_graph.get(node, set())
            if not dependencies:
                depth = 0
            else:
                depth = 1 + max(
                    compute_depth(dep, visited.copy())
                    for dep in dependencies
                    if dep in self.analysis.nodes
                )

            depths[node] = depth
            return depth

        for node in self.analysis.nodes:
            if depths[node] == -1:
                compute_depth(node, set())

        # Update node depths
        for address, depth in depths.items():
            self.analysis.nodes[address].depth = depth

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_dependencies(self, address: str, recursive: bool = False) -> Set[str]:
        """
        Get dependencies of a block.

        Args:
            address: Block address
            recursive: If True, get all transitive dependencies

        Returns:
            Set of dependency addresses
        """
        if address not in self.analysis.nodes:
            return set()

        if not recursive:
            return self.analysis.dependency_graph.get(address, set()).copy()

        # BFS to get all transitive dependencies
        visited = set()
        queue = deque([address])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for dep in self.analysis.dependency_graph.get(current, set()):
                if dep not in visited:
                    queue.append(dep)

        visited.discard(address)  # Remove self
        return visited

    def get_dependents(self, address: str, recursive: bool = False) -> Set[str]:
        """
        Get dependents of a block (what depends on this block).

        Args:
            address: Block address
            recursive: If True, get all transitive dependents

        Returns:
            Set of dependent addresses
        """
        if address not in self.analysis.nodes:
            return set()

        if not recursive:
            return self.analysis.reverse_dependency_graph.get(address, set()).copy()

        # BFS to get all transitive dependents
        visited = set()
        queue = deque([address])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for dep in self.analysis.reverse_dependency_graph.get(current, set()):
                if dep not in visited:
                    queue.append(dep)

        visited.discard(address)  # Remove self
        return visited

    def get_dependency_chain(
        self, from_address: str, to_address: str
    ) -> Optional[List[str]]:
        """
        Find the dependency chain from one block to another.

        Args:
            from_address: Starting block
            to_address: Target block

        Returns:
            List of addresses forming the chain, or None if no path exists
        """
        if (
            from_address not in self.analysis.nodes
            or to_address not in self.analysis.nodes
        ):
            return None

        # BFS to find shortest path
        queue = deque([(from_address, [from_address])])
        visited = {from_address}

        while queue:
            current, path = queue.popleft()

            if current == to_address:
                return path

            for dep in self.analysis.dependency_graph.get(current, set()):
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, path + [dep]))

        return None

    def get_critical_path(self) -> List[str]:
        """
        Get the critical path (longest dependency chain).

        Returns:
            List of addresses forming the critical path
        """
        max_depth = 0
        deepest_node = None

        for address, node in self.analysis.nodes.items():
            if node.depth > max_depth:
                max_depth = node.depth
                deepest_node = address

        if not deepest_node:
            return []

        # Backtrack to find the path
        path = [deepest_node]
        current = deepest_node

        while True:
            deps = self.analysis.dependency_graph.get(current, set())
            if not deps:
                break

            # Find dependency with depth = current_depth - 1
            current_depth = self.analysis.nodes[current].depth
            next_node = None

            for dep in deps:
                if self.analysis.nodes[dep].depth == current_depth - 1:
                    next_node = dep
                    break

            if not next_node:
                break

            path.append(next_node)
            current = next_node

        path.reverse()
        return path
