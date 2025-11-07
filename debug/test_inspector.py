"""
Sample Terraform configuration and test script.
This demonstrates the full capabilities of the Terraform Inspector.
"""

from pathlib import Path
from typing import Any, Dict


def mock_hcl_loads() -> Dict[str, Any]:
    """
    Mocks the behavior of an HCL parser (like hcl.loads) for demonstration purposes.
    In a real-world scenario, you MUST use the actual hcl library.
    """
    # This is simplified and only handles the key-value pairs we know are in the file.
    # The actual HCL parser handles complex logic, comments, and syntax rules.
    data = {
        "environment": "staging",
        "machine_size": "medium",
        "instance_count": 3,
        "enable_monitoring": True,
        "tags": {
            "Project": "MultiCloudApp",
            "ManagedBy": "Terraform",
            "Owner": "EngineeringTeam",
        },
        "aws_region": "eu-west-1",
        "gcp_region": "europe-west3",
        "gcp_zone": "europe-west3-a",
        "azure_region": "West Europe",
        "azure_subscription_id": "00000000-0000-0000-0000-000000000000",
        "azure_tenant_id": "11111111-1111-1111-1111-111111111111",
        "unused_variable": "test-graph-ignore",
    }
    return data


def run_complete_test():
    """Run a complete test of the Terraform Inspector."""
    import json
    import traceback

    from tfkit.inspector.builder import TerraformGraphBuilder
    from tfkit.inspector.models import (
        TerraformObjectType,
    )
    from tfkit.inspector.parser import TerraformParser
    from tfkit.inspector.resolver import ReferenceResolver

    print("\n" + "=" * 80)
    print("TERRAFORM INSPECTOR - COMPLETE TEST")
    print("=" * 80)

    examples_path = Path("./examples")

    print("\n[1] Parsing Terraform module...")
    parser = TerraformParser()
    module = parser.parse_module(examples_path)

    print(f"    Files parsed: {len(module.files)}")
    print(f"    Total blocks: {sum(len(f.blocks) for f in module.files)}")
    print(f"    Resources: {len(module._global_resource_index)}")
    print(f"    Variables: {len(module._global_variable_index)}")
    print(f"    Providers: {len(module._global_provider_index)}")
    print(f"    Outputs: {len(module._global_output_index)}")

    print("\n[2] Block structure:")
    for file in module.files:
        print(f"\n    {Path(file.file_path).name}:")
        for block in file.blocks:
            address_info = f"{block.block_type.value}: {block.address}"
            if block.block_type == TerraformObjectType.PROVIDER:
                address_info = f"PROVIDER: {block.address} ({block.labels[0]})"

            print(f"      • {address_info}")
            if block.source_location:
                print(
                    f"        Line {block.source_location.line_start}-{block.source_location.line_end}"
                )
            if block.dependencies:
                print(f"        Dependencies: {len(block.dependencies)}")

    print("\n[3] Reference & Meta-Argument Analysis (Showcase):")

    total_refs = 0

    referencing_blocks = list(module._global_resource_index.values()) + list(
        module._global_module_index.values()
    )

    for block in referencing_blocks:
        for attr in block.attributes.values():
            total_refs += len(attr.value.references)

    print(f"    Total references found: {total_refs}")

    print("\n    Example references & meta-arguments:")

    examples_shown = set()

    # 3.1. Attribute References (Resource, Module, Data)
    for block in referencing_blocks:
        if len(examples_shown) >= 5:
            break

        for attr_name, attr in block.attributes.items():
            if attr.value.references and attr_name not in examples_shown:
                ref = attr.value.references[0]
                print(f"        🔗 Attribute ({block.address}.{attr_name})")
                print(f"        → Ref: {ref.full_reference}")
                examples_shown.add(attr_name)
                if len(examples_shown) >= 5:
                    break

    # 3.2. Meta-Argument Showcase (Count, For_Each, Provider, Lifecycle)

    meta_examples = 0
    for block in referencing_blocks:
        if meta_examples >= 5:
            break

        if block.count and meta_examples < 5:
            print(f"      ⚙️ Meta-Arg (Count): {block.address}")
            print(f"        → Value: {block.count.raw_value}")
            meta_examples += 1

        if block.for_each and meta_examples < 5:
            print(f"      ⚙️ Meta-Arg (For_Each): {block.address}")
            print(f"        → Value: {block.for_each.raw_value}")
            meta_examples += 1

        if block.explicit_provider and meta_examples < 5:
            print(f"      ☁️ Meta-Arg (Provider): {block.address}")
            print(f"        → Value: {block.explicit_provider.raw_value}")
            meta_examples += 1

        if block.lifecycle and meta_examples < 5:
            print(f"      ♻️ Meta-Arg (Lifecycle): {block.address}")
            print(f"        → Keys: {list(block.lifecycle.keys())}")
            meta_examples += 1

    print("\n[4] Provider Configuration Lookup:")

    all_providers = list(module._global_provider_index.values())
    print(f"    Total unique provider configs found: {len(all_providers)}")

    for provider_block in all_providers[:5]:
        provider_name = provider_block.labels[0]
        alias = provider_block.attributes.get("alias")
        is_aliased = alias is not None
        alias_info = f"({alias.value.raw_value})" if is_aliased else " (Default)"

        print(f"    → Address: **{provider_block.address}** {alias_info}")
        print(f"      Config Key: **{provider_name}**")

        looked_up = module.get_block(provider_block.address)
        lookup_status = "✓ Found" if looked_up else "✗ NOT Found"
        print(f"      Lookup by Address: {lookup_status}")

    print("\n[5] Resolving references...")
    terraform_vars = mock_hcl_loads()

    resolver = ReferenceResolver(module, terraform_vars)

    try:
        resolver.resolve_module()
        print("    ✓ Resolution completed successfully")
    except Exception as e:
        print(f"    ✗ Resolution failed: {e}")
        traceback.print_exc()
        return

    print("\n[6] Resolved local values:")
    for local_block in module._global_local_index.values():
        value_attr = local_block.attributes.get("value")
        if (
            value_attr
            and hasattr(value_attr.value, "is_fully_resolved")
            and value_attr.value.is_fully_resolved
        ):
            print(f"    local.{local_block.name}")
            print(f"      Raw:      {value_attr.value.raw_value}")
            print(f"      Resolved: {value_attr.value.resolved_value}")

    print("\n[7] Resolved resource attributes (sample):")
    sample_block = module.get_block("google_compute_network.vpc") or next(
        iter(module._global_resource_index.values()), None
    )
    if sample_block:
        print(f"    Block: {sample_block.address}")
        resolved_attr = next(
            (
                a
                for a in sample_block.attributes.values()
                if hasattr(a.value, "resolved_value")
            ),
            None,
        )
        if resolved_attr:
            print(f"      Attribute: {resolved_attr.name}")
            print(f"      Resolved: {resolved_attr.value.resolved_value}")
        else:
            print("      (No resolvable attributes to display)")

    print("\n[8] Dependency graph:")
    for block in list(module._global_resource_index.values())[:5]:
        print(f"    {block.address}")
        if block.dependencies:
            for dep in list(block.dependencies)[:3]:
                print(f"      ↳ {dep}")
        else:
            print("      ↳ (no dependencies)")

    print("\n[9] Exporting results...")

    module_dict = module.to_dict()
    with open("test_module_full.json", "w") as f:
        json.dump(module_dict, f, indent=2)
    print("    ✓ test_module_full.json")

    summary = {
        "module": {
            "path": module.root_path,
            "files": len(module.files),
            "statistics": module_dict.get("summary", {}),
        },
        "resources": [
            {
                "address": block.address,
                "type": block.resource_type,
                "location": block.source_location.to_dict()
                if block.source_location
                else None,
                "dependencies": list(block.dependencies),
                "attribute_count": len(block.attributes),
                "meta_args_detected": [
                    k
                    for k, v in [
                        ("count", block.count),
                        ("for_each", block.for_each),
                        ("provider", block.explicit_provider),
                    ]
                    if v is not None
                ],
            }
            for block in module._global_resource_index.values()
        ],
        "locals": [
            {
                "name": block.name,
                "raw_value": block.attributes["value"].value.raw_value,
                "resolved_value": block.attributes["value"].value.resolved_value
                if hasattr(block.attributes["value"].value, "resolved_value")
                else None,
            }
            for block in module._global_local_index.values()
            if "value" in block.attributes
        ],
        "providers": [
            {"address": p.address, "type": p.labels[0]}
            for p in module._global_provider_index.values()
        ],
    }

    with open("test_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("    ✓ test_summary.json")

    print("\n[10] Statistics:")

    total_lines = 0
    for f in module.files:
        try:
            total_lines += len(parser._get_file_lines(f.file_path))
        except AttributeError:
            pass

    print(f"    Total lines of Terraform: {total_lines}")
    print(
        f"    Total attributes: {sum(len(b.attributes) for f in module.files for b in f.blocks)}"
    )
    resolved_count = sum(
        1
        for f in module.files
        for b in f.blocks
        for a in b.attributes.values()
        if hasattr(a.value, "is_fully_resolved")
        and a.value.is_fully_resolved
        and a.value.references
    )

    print(f"    References resolved: {resolved_count}")
    print(
        f"    Functions evaluated: {sum(len(a.value.functions) for f in module.files for b in f.blocks for a in b.attributes.values() if hasattr(a.value, 'functions'))}"
    )

    print("[11] Graph")
    graph_builder = TerraformGraphBuilder()
    graph = graph_builder.build_graph(module)

    graph_data = graph.to_dict()

    resource_id = "aws_vpc.main"
    dependencies = graph.get_edges_from(resource_id)
    print(f"Dependencies of {resource_id}:")
    for dep in dependencies:
        print(f"  - {dep.target_id} ({dep.edge_type.value})")

    print(f"Graph built with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print("Node types:", graph_data["summary"]["node_types"])

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  • test_module_full.json  - Complete module structure")
    print("  • test_summary.json      - Summary with resolved values")
    print(f"  • {examples_path}/              - Sample Terraform files")


if __name__ == "__main__":
    run_complete_test()
