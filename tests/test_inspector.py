"""
Sample Terraform configuration and test script.
This demonstrates the full capabilities of the Terraform Inspector.
"""

from pathlib import Path


def run_complete_test():
    """Run a complete test of the Terraform Inspector."""
    import json

    from tfkit.inspector.parser import TerraformParser
    from tfkit.inspector.resolver import ReferenceResolver

    print("\n" + "=" * 80)
    print("TERRAFORM INSPECTOR - COMPLETE TEST")
    print("=" * 80)

    examples_path = Path("./examples")

    # Parse module
    print("\n[1] Parsing Terraform module...")
    parser = TerraformParser()
    module = parser.parse_module(examples_path)

    print(f"    Files parsed: {len(module.files)}")
    print(f"    Total blocks: {sum(len(f.blocks) for f in module.files)}")
    print(f"    Resources: {len(module._global_resource_index)}")
    print(f"    Variables: {len(module._global_variable_index)}")
    print(f"    Locals: {len(module._global_local_index)}")
    print(f"    Outputs: {len(module._global_output_index)}")

    # Show parsed structure
    print("\n[2] Block structure:")
    for file in module.files:
        print(f"\n    {Path(file.file_path).name}:")
        for block in file.blocks:
            print(f"      • {block.block_type.value}: {block.address}")
            if block.source_location:
                print(
                    f"        Line {block.source_location.line_start}-{block.source_location.line_end}"
                )
            if block.dependencies:
                print(f"        Dependencies: {len(block.dependencies)}")

    # Analyze references
    print("\n[3] Reference analysis:")
    total_refs = 0
    for block in module._global_resource_index.values():
        for attr in block.attributes.values():
            total_refs += len(attr.value.references)

    print(f"    Total references found: {total_refs}")

    # Show some reference examples
    print("\n    Example references:")
    count = 0
    for block in module._global_resource_index.values():
        for attr_name, attr in block.attributes.items():
            if attr.value.references and count < 5:
                for ref in attr.value.references[:1]:
                    print(f"      {block.address}.{attr_name}")
                    print(f"        → {ref.full_reference}")
                    count += 1
                    if count >= 5:
                        break

    # Resolve references
    print("\n[4] Resolving references...")
    terraform_vars = {
        "environment": "production",
        "region": "eu-west-1",
        "vpc_cidr": "10.100.0.0/16",
        "availability_zones": ["eu-west-1a", "eu-west-1b"],
        "tags": {
            "Project": "WebApp",
            "ManagedBy": "Terraform",
            "Team": "Platform",
        },
    }

    print(f"    Using variables: {list(terraform_vars.keys())}")

    resolver = ReferenceResolver(module, terraform_vars)

    try:
        resolver.resolve_module()
        print("    ✓ Resolution completed successfully")
    except Exception as e:
        print(f"    ✗ Resolution failed: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n[5] Resolved local values:")
    for local_block in module._global_local_index.values():
        value_attr = local_block.attributes.get("value")
        if value_attr and value_attr.value.is_fully_resolved:
            print(f"    local.{local_block.name}")
            print(f"      Raw:      {value_attr.value.raw_value}")
            print(f"      Resolved: {value_attr.value.resolved_value}")

    # Show resolved resource attributes
    print("\n[6] Resolved resource attributes (sample):")
    vpc_block = module.get_block("google_compute_network.vpc")
    print(vpc_block.to_dict())

    print("\n[7] Dependency graph:")
    for block in list(module._global_resource_index.values())[:5]:
        print(f"    {block.address}")
        if block.dependencies:
            for dep in block.dependencies:
                print(f"      ↳ {dep}")
        else:
            print("      ↳ (no dependencies)")

    # Export results
    print("\n[8] Exporting results...")

    # Full module export
    module_dict = module.to_dict()
    with open("test_module_full.json", "w") as f:
        json.dump(module_dict, f, indent=2)
    print("    ✓ test_module_full.json")

    # Summary export
    summary = {
        "module": {
            "path": module.root_path,
            "files": len(module.files),
            "statistics": module_dict["summary"],
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
            }
            for block in module._global_resource_index.values()
        ],
        "locals": [
            {
                "name": block.name,
                "raw_value": block.attributes["value"].value.raw_value,
                "resolved_value": block.attributes["value"].value.resolved_value,
            }
            for block in module._global_local_index.values()
            if "value" in block.attributes
        ],
    }

    with open("test_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("    ✓ test_summary.json")

    # Statistics
    print("\n[9] Statistics:")
    print(
        f"    Total lines of Terraform: {sum(len(parser._get_file_lines(f.file_path)) for f in module.files)}"
    )
    print(
        f"    Total attributes: {sum(len(b.attributes) for f in module.files for b in f.blocks)}"
    )
    print(
        f"    References resolved: {sum(1 for f in module.files for b in f.blocks for a in b.attributes.values() if a.value.is_fully_resolved and a.value.references)}"
    )
    print(
        f"    Functions evaluated: {sum(len(a.value.functions) for f in module.files for b in f.blocks for a in b.attributes.values())}"
    )

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  • test_module_full.json  - Complete module structure")
    print("  • test_summary.json      - Summary with resolved values")
    print(f"  • {examples_path}/              - Sample Terraform files")


if __name__ == "__main__":
    run_complete_test()
