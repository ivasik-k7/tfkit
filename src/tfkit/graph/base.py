from typing import Dict, Optional

from tfkit.dependency.models import (
    DependencyType,
    ObjectDependencies,
    TerraformDependency,
)
from tfkit.graph.models import (
    GraphData,
    Link,
    LinkType,
    Node,
    NodeData,
    NodeState,
    NodeType,
)
from tfkit.parser.models import (
    BaseTerraformObject,
    TerraformCatalog,
    TerraformDataSource,
    TerraformResource,
)


class TerraformGraphBuilder:
    """
    Builds a GraphData object (Nodes and Links) from the TerraformCatalog
    and the dependency analysis results.
    """

    # Mapping from DependencyType (from dependency/models) to LinkType (from graph/models)
    DEPENDENCY_TYPE_TO_LINK_TYPE: Dict[DependencyType, LinkType] = {
        DependencyType.DIRECT: LinkType.DIRECT,
        DependencyType.IMPLICIT: LinkType.IMPLICIT,
        DependencyType.EXPLICIT: LinkType.EXPLICIT,
        DependencyType.PROVIDER: LinkType.PROVIDER_RELATIONSHIP,
        DependencyType.PROVIDER_CONFIG: LinkType.PROVIDER_CONFIG,
        # DependencyType.MODULE_CALL: LinkType.MODULE_CALL,
        # DependencyType.LIFECYCLE: LinkType.LIFECYCLE,
        DependencyType.CONFIGURATION: LinkType.CONFIGURATION,
        DependencyType.OUTPUT: LinkType.EXPORT,
        DependencyType.DATA_REFERENCE: LinkType.DATA_REFERENCE,
        DependencyType.TERRAFORM_BLOCK: LinkType.CONFIGURATION,
        DependencyType.MOVED: LinkType.EXPLICIT,  # Treat moved blocks as explicit dependencies
    }

    # Mapping from BaseTerraformObject.object_type (via value) to NodeType (from graph/models)
    OBJECT_TYPE_TO_NODE_TYPE: Dict[str, NodeType] = {
        "resource": NodeType.RESOURCE,
        "data": NodeType.DATA,
        "module": NodeType.MODULE,
        "variable": NodeType.VARIABLE,
        "output": NodeType.OUTPUT,
        "provider": NodeType.PROVIDER,
        "local": NodeType.LOCAL,
        "terraform": NodeType.TERRAFORM,
    }

    def __init__(self, catalog: TerraformCatalog):
        self.catalog = catalog
        self.graph_data = GraphData()

    def build_graph(
        self,
        dependency_map: Dict[str, ObjectDependencies],
    ) -> GraphData:
        """
        Main method to build the graph.

        :param dependency_map: The result dictionary from TerraformDependencyBuilder.
        :return: A populated GraphData object.
        """

        for address, obj_deps in dependency_map.items():
            node = self._build_node_from_address(address, obj_deps)
            if node:
                self.graph_data.add_node(node)

        for _address, obj_deps in dependency_map.items():
            for dep in obj_deps.depends_on:
                self._add_link(dep)

        self._calculate_node_counts()

        return self.graph_data

    def _get_node_type(self, address: str) -> NodeType:
        """Determines the appropriate NodeType based on the address structure."""
        if address == "terraform":
            return NodeType.TERRAFORM

        parts = address.split(".")

        if parts[0] == "var":
            return NodeType.VARIABLE
        if parts[0] == "local":
            return NodeType.LOCAL
        if parts[0] == "module":
            return NodeType.MODULE
        if parts[0] == "data":
            return NodeType.DATA
        if parts[0] == "resource":
            return NodeType.RESOURCE
        if parts[0] == "output":
            return NodeType.OUTPUT
        if parts[0] == "provider" or len(parts) > 1:
            return NodeType.PROVIDER

        # Fallback to catalog object type if available
        obj = self.catalog.get_by_address(address)
        if obj and hasattr(obj, "object_type"):
            obj_type_val = getattr(obj, "object_type").value  # noqa
            return self.OBJECT_TYPE_TO_NODE_TYPE.get(obj_type_val, NodeType.RESOURCE)

        # Default for unknown or implicitly created nodes (e.g., provider aliases not in main blocks)
        return NodeType.RESOURCE

    def _get_link_type(self, dep_type: DependencyType) -> LinkType:
        """Maps a DependencyType to a LinkType."""
        return self.DEPENDENCY_TYPE_TO_LINK_TYPE.get(dep_type, LinkType.IMPLICIT)

    def _extract_nodedata(
        self, obj: Optional[BaseTerraformObject], obj_deps: ObjectDependencies
    ) -> NodeData:
        """Populates NodeData from a BaseTerraformObject."""
        data = NodeData(
            dependency_count=len(obj_deps.depends_on),
            reference_count=len(obj_deps.referenced_by),
        )

        if obj is None:
            # Handle "terraform" block or missing/unknown objects
            data.state = NodeState.CONFIGURATION
            return data

        # Common attributes
        data.source_file = getattr(obj, "source_file", None)
        data.line_number = getattr(obj, "line_number", None)

        # Terraform Meta-Arguments
        data.depends_on = (
            getattr(obj, "depends_on", [])
            if isinstance(getattr(obj, "depends_on", []), list)
            else []
        )
        data.count = getattr(obj, "count", None)
        data.for_each = getattr(obj, "for_each", None)
        data.lifecycle_rules = getattr(obj, "lifecycle", None)
        data.attributes = getattr(obj, "attributes", {})

        # Resource/Data Specific
        if isinstance(obj, (TerraformResource, TerraformDataSource)):
            data.provider = getattr(obj, "provider", None)
            data.resource_type = getattr(obj, "resource_type", None) or getattr(
                obj, "data_type", None
            )

        # Module path
        # Assuming the catalog has a way to get the module path if not directly on the object
        address_parts = obj_deps.address.split(".")
        if address_parts[0] == "module":
            data.module_path = address_parts[1:]

        # Initial State Guessing (can be refined later)
        if obj_deps.address == "terraform":
            data.state = NodeState.CONFIGURATION
        elif isinstance(obj, TerraformResource) or isinstance(obj, TerraformDataSource):
            if not obj_deps.referenced_by:
                data.state = NodeState.LEAF  # Nothing depends on it
            elif not obj_deps.depends_on:
                data.state = NodeState.HUB  # Depends on nothing, many depend on it
            else:
                data.state = NodeState.ACTIVE
        elif obj.object_type.value in {"variable", "local"}:
            data.state = NodeState.CONFIG_PROVIDER  # Provides configuration value
        elif obj.object_type.value == "output":
            data.state = NodeState.CONFIG_CONSUMER  # Consumes values to export
        else:
            data.state = NodeState.UNKNOWN

        return data

    def _build_node_from_address(
        self, address: str, obj_deps: ObjectDependencies
    ) -> Optional[Node]:
        """Creates a Node object."""

        tf_obj = self.catalog.get_by_address(address)

        # If the object is not found in the catalog (e.g., a synthetic node like an unaliased provider)
        if (
            tf_obj is None
            and address != "terraform"
            and not address.startswith("provider.")
        ):
            # This is an unknown reference, likely outside the current scope
            return None

        node_type = self._get_node_type(address)
        node_data = self._extract_nodedata(tf_obj, obj_deps)

        # Name is usually the last part of the address (e.g., 'vpc' from 'resource.aws_vpc.vpc')
        name = address.split(".")[-1]

        if node_type == NodeType.RESOURCE or node_type == NodeType.DATA:
            # For resources/data, the name should be the full type.name
            name = f"{address.split('.')[-2]}.{address.split('.')[-1]}"
        elif node_type == NodeType.PROVIDER:
            name = address

        return Node(
            id=address,
            name=name,
            type=node_type,
            data=node_data,
            # Position and group can be set later by a layout/grouping algorithm
            position=None,
            group=None,
        )

    def _add_link(self, dep: TerraformDependency) -> None:
        """Creates a Link object and adds it to the graph."""

        # Only create a link if both source and target nodes exist in the final graph.
        # This filters out dependencies on external/unknown objects.
        if (
            dep.source_address not in self.graph_data.nodes
            or dep.target_address not in self.graph_data.nodes
        ):
            return

        link_type = self._get_link_type(dep.dependency_type)

        # reference_path is derived from attribute_path, split by '.'
        ref_path = dep.attribute_path.split(".") if dep.attribute_path else None

        self.graph_data.add_link(
            Link(
                source=dep.source_address,
                target=dep.target_address,
                link_type=link_type,
                # Link strength can be calculated based on type, but defaults to 1.0
                strength=1.0,
                reference_path=ref_path,
            )
        )

    def _calculate_node_counts(self):
        """
        Ensures dependency/reference counts on NodeData are correct based on final Links.
        This is an optional cleanup/verification step.
        """
        for node in self.graph_data.nodes.values():
            # Recalculate based on the links that were actually added to the graph
            incoming_links = [l for l in self.graph_data.links if l.target == node.id]  # noqa: E741
            outgoing_links = [l for l in self.graph_data.links if l.source == node.id]  # noqa: E741

            node.data.dependency_count = len(outgoing_links)
            node.data.reference_count = len(incoming_links)

            # Optional: Refine state based on final connectivity
            if node.data.state == NodeState.ACTIVE:
                if node.data.dependency_count == 0 and node.data.reference_count > 0:
                    node.data.state = NodeState.HUB
                elif node.data.reference_count == 0 and node.data.dependency_count > 0:
                    node.data.state = NodeState.LEAF
                elif node.data.reference_count == 0 and node.data.dependency_count == 0:
                    node.data.state = NodeState.ORPHAN
