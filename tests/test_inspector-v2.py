"""
Test script for enhanced Terraform reference extraction and dependency analysis.
"""

import json
from pathlib import Path

from tfkit.inspector.analyzer import DependencyAnalyzer
from tfkit.inspector.parser import TerraformParser


def test_reference_extraction(module_path: str):
    """Test comprehensive reference extraction."""
    print("=" * 80)
    print("TESTING ENHANCED REFERENCE EXTRACTION")
    print("=" * 80)

    parser = TerraformParser()
    module = parser.parse_module(module_path)

    print(f"\nParsed module: {module.root_path}")
    print(f"Files: {len(module.files)}")
    print(f"Total blocks: {sum(len(f.blocks) for f in module.files)}")

    # Test reference extraction for each block
    print("\n" + "-" * 80)
    print("REFERENCE EXTRACTION BY BLOCK")
    print("-" * 80)

    total_refs = 0
    blocks_with_refs = 0

    for file in module.files:
        print(f"\n📄 File: {Path(file.file_path).name}")

        for block in file.blocks:
            all_refs = set()

            # Collect references from all attributes
            for attr in block.attributes.values():
                for ref in attr.value.references:
                    all_refs.add(ref.full_reference)

            # Collect from count/for_each
            if block.count:
                for ref in block.count.references:
                    all_refs.add(ref.full_reference)

            if block.for_each:
                for ref in block.for_each.references:
                    all_refs.add(ref.full_reference)

            if all_refs:
                blocks_with_refs += 1
                total_refs += len(all_refs)

                print(f"\n  📦 {block.address}")
                print(f"     Type: {block.block_type.value}")
                print(f"     References ({len(all_refs)}):")

                # Group by reference type
                by_type = {}
                for ref_str in sorted(all_refs):
                    # Parse to get type
                    ref_type = ref_str.split(".")[0]
                    if ref_type not in by_type:
                        by_type[ref_type] = []
                    by_type[ref_type].append(ref_str)

                for ref_type, refs in sorted(by_type.items()):
                    print(f"       {ref_type}:")
                    for ref in refs:
                        print(f"         • {ref}")

    print(f"\n📊 Summary:")
    print(f"   Total references extracted: {total_refs}")
    print(f"   Blocks with references: {blocks_with_refs}")

    return module


def test_dependency_analysis(module):
    """Test comprehensive dependency analysis."""
    print("\n" + "=" * 80)
    print("TESTING DEPENDENCY ANALYSIS")
    print("=" * 80)

    analyzer = DependencyAnalyzer(module)
    analysis = analyzer.analyze()

    print(f"\n📊 Analysis Summary:")
    print(f"   Total nodes: {len(analysis.nodes)}")
    print(
        f"   Total dependencies: {sum(len(deps) for deps in analysis.dependency_graph.values())}"
    )
    print(f"   Root nodes (no dependencies): {len(analysis.root_nodes)}")
    print(f"   Leaf nodes (no dependents): {len(analysis.leaf_nodes)}")
    print(f"   Orphaned nodes: {len(analysis.orphaned_nodes)}")
    print(f"   Circular dependencies: {len(analysis.circular_dependencies)}")

    # Show root nodes
    print("\n🌱 Root Nodes (inputs):")
    for address in sorted(analysis.root_nodes):
        node = analysis.nodes[address]
        print(f"   • {address} ({node.block.block_type.value})")

    # Show leaf nodes
    print("\n🍃 Leaf Nodes (outputs):")
    for address in sorted(analysis.leaf_nodes):
        node = analysis.nodes[address]
        dependents_count = len(node.dependents)
        print(f"   • {address} ({node.block.block_type.value})")

    # Show nodes by depth
    print("\n📏 Nodes by Depth:")
    by_depth = {}
    for address, node in analysis.nodes.items():
        depth = node.depth
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(address)

    for depth in sorted(by_depth.keys()):
        nodes = by_depth[depth]
        print(f"   Depth {depth}: {len(nodes)} nodes")
        for address in sorted(nodes)[:5]:  # Show first 5
            print(f"     • {address}")
        if len(nodes) > 5:
            print(f"     ... and {len(nodes) - 5} more")

    # Show execution order (first and last 10)
    print("\n⚙️  Execution Order:")
    print("   First 10:")
    for i, address in enumerate(analysis.execution_order[:10], 1):
        print(f"     {i:2d}. {address}")

    if len(analysis.execution_order) > 20:
        print(f"   ... ({len(analysis.execution_order) - 20} more)")

    print("   Last 10:")
    for i, address in enumerate(
        analysis.execution_order[-10:], len(analysis.execution_order) - 9
    ):
        print(f"     {i:2d}. {address}")

    # Show circular dependencies
    if analysis.circular_dependencies:
        print("\n🔄 Circular Dependencies:")
        for i, cycle in enumerate(analysis.circular_dependencies, 1):
            print(f"   Cycle {i}:")
            print(f"     {' -> '.join(cycle)}")
    else:
        print("\n✅ No circular dependencies detected")

    # Show critical path
    critical_path = analyzer.get_critical_path()
    if critical_path:
        print(f"\n🎯 Critical Path (length: {len(critical_path)}):")
        for i, address in enumerate(critical_path, 1):
            node = analysis.nodes[address]
            print(f"   {i:2d}. {address} (depth: {node.depth})")

    return analysis


def test_dependency_queries(module, analysis):
    """Test dependency query utilities."""
    print("\n" + "=" * 80)
    print("TESTING DEPENDENCY QUERIES")
    print("=" * 80)

    analyzer = DependencyAnalyzer(module)
    analyzer.analysis = analysis

    # Find a resource with dependencies
    resource_address = None
    for address, node in analysis.nodes.items():
        if node.is_resource and node.dependencies:
            resource_address = address
            break

    if resource_address:
        print(f"\n🔍 Analyzing: {resource_address}")

        # Direct dependencies
        direct_deps = analyzer.get_dependencies(resource_address, recursive=False)
        print(f"\n   Direct dependencies ({len(direct_deps)}):")
        for dep in sorted(direct_deps)[:10]:
            print(f"     • {dep}")

        # All transitive dependencies
        all_deps = analyzer.get_dependencies(resource_address, recursive=True)
        print(f"\n   All transitive dependencies ({len(all_deps)}):")
        for dep in sorted(all_deps)[:10]:
            print(f"     • {dep}")
        if len(all_deps) > 10:
            print(f"     ... and {len(all_deps) - 10} more")

        # Direct dependents
        direct_dependents = analyzer.get_dependents(resource_address, recursive=False)
        print(f"\n   Direct dependents ({len(direct_dependents)}):")
        for dep in sorted(direct_dependents):
            print(f"     • {dep}")

        # All transitive dependents
        all_dependents = analyzer.get_dependents(resource_address, recursive=True)
        print(f"\n   All transitive dependents ({len(all_dependents)}):")
        for dep in sorted(all_dependents)[:10]:
            print(f"     • {dep}")
        if len(all_dependents) > 10:
            print(f"     ... and {len(all_dependents) - 10} more")


def test_complex_references(module):
    """Test extraction of complex reference patterns."""
    print("\n" + "=" * 80)
    print("TESTING COMPLEX REFERENCE PATTERNS")
    print("=" * 80)

    test_cases = {
        "Interpolations": [],
        "For expressions": [],
        "Conditionals": [],
        "Function calls": [],
        "Nested structures": [],
    }

    for file in module.files:
        for block in file.blocks:
            for attr in block.attributes.values():
                raw = str(attr.value.raw_value)

                # Check for interpolations
                if "${" in raw:
                    if "for " in raw:
                        test_cases["For expressions"].append(
                            (block.address, attr.name, raw[:80])
                        )
                    elif "?" in raw and ":" in raw:
                        test_cases["Conditionals"].append(
                            (block.address, attr.name, raw[:80])
                        )
                    else:
                        test_cases["Interpolations"].append(
                            (block.address, attr.name, raw[:80])
                        )

                # Check for function calls
                if attr.value.functions:
                    test_cases["Function calls"].append(
                        (block.address, attr.name, attr.value.functions[0].name)
                    )

                # Check for nested structures
                if (
                    isinstance(attr.value.raw_value, (dict, list))
                    and attr.value.references
                ):
                    test_cases["Nested structures"].append(
                        (block.address, attr.name, len(attr.value.references))
                    )

    for category, cases in test_cases.items():
        if cases:
            print(f"\n{category} ({len(cases)} found):")
            for case in cases[:5]:
                if len(case) == 3:
                    print(f"   • {case[0]}.{case[1]}")
                    print(f"     Value: {case[2]}")
            if len(cases) > 5:
                print(f"   ... and {len(cases) - 5} more")


def export_results(module, analysis, output_dir: str):
    """Export analysis results to files."""
    print("\n" + "=" * 80)
    print("EXPORTING RESULTS")
    print("=" * 80)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Export module structure
    module_dict = module.to_dict()
    with open(output_path / "module_structure.json", "w") as f:
        json.dump(module_dict, f, indent=2)
    print(f"✅ Exported: module_structure.json")

    # Export dependency analysis
    analysis_dict = analysis.to_dict()
    with open(output_path / "dependency_analysis.json", "w") as f:
        json.dump(analysis_dict, f, indent=2)
    print(f"✅ Exported: dependency_analysis.json")

    analyzer = DependencyAnalyzer(module)
    analyzer.analysis = analysis
    analyzer.export("dependencies.dot", "dot")  # DotGraph visualization
    analyzer.export("dependencies.mmd", "mermaid")
    print(f"   (Use 'dot -Tpng dependency_graph.dot -o graph.png' to visualize)")

    print(f"\n📁 All results saved to: {output_path.absolute()}")


def main():
    """Run all tests."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_enhanced.py <module_path>")
        print("Example: python test_enhanced.py ./examples")
        sys.exit(1)

    module_path = sys.argv[1]

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         TERRAFORM INSPECTOR - REFERENCE EXTRACTION TEST           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Test 1: Reference extraction
    module = test_reference_extraction(module_path)

    # Test 2: Dependency analysis
    analysis = test_dependency_analysis(module)

    # Test 3: Dependency queries
    test_dependency_queries(module, analysis)

    # Test 4: Complex references
    test_complex_references(module)

    # Export results
    export_results(module, analysis, "./test_output")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
