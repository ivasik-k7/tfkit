"""
Enhanced Terraform Inspector with comprehensive metadata extraction and reference resolution.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

# ============================================================================
# ENUMS AND TYPE DEFINITIONS
# ============================================================================


class TerraformObjectType(Enum):
    """Types of Terraform objects."""

    RESOURCE = "resource"
    DATA_SOURCE = "data"
    MODULE = "module"
    VARIABLE = "variable"
    OUTPUT = "output"
    LOCAL = "local"
    PROVIDER = "provider"
    TERRAFORM = "terraform"
    MOVED = "moved"
    IMPORT = "import"
    UNKNOWN = "unknown"


class AttributeType(Enum):
    """Types of attribute values."""

    STRING = "string"
    NUMBER = "number"
    BOOL = "bool"
    LIST = "list"
    MAP = "map"
    OBJECT = "object"
    SET = "set"
    NULL = "null"
    REFERENCE = "reference"
    INTERPOLATION = "interpolation"
    FUNCTION = "function"
    EXPRESSION = "expression"


class ReferenceType(Enum):
    """Types of references in Terraform."""

    VARIABLE = "var"
    LOCAL = "local"
    RESOURCE = "resource"
    DATA_SOURCE = "data"
    MODULE = "module"
    PATH = "path"
    TERRAFORM = "terraform"
    FUNCTION = "function"
    COUNT = "count"
    EACH = "each"
    SELF = "self"


# ============================================================================
# CORE DATA MODELS
# ============================================================================


@dataclass
class SourceLocation:
    """Location information for any element in source code."""

    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_start}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
        }


class ReferenceResolutionState(Enum):
    """State of reference resolution."""

    UNRESOLVED = "unresolved"
    RESOLVING = "resolving"  # Currently being resolved (for cycle detection)
    RESOLVED = "resolved"
    CIRCULAR = "circular"
    UNRESOLVABLE = "unresolvable"  # External dependency or unknown target
    PARTIALLY_RESOLVED = "partially_resolved"  # Some attributes resolved, others not


class ReferenceScope(Enum):
    """Scope of the reference."""

    LOCAL = "local"  # Within same locals block
    MODULE = "module"  # Within same module
    CROSS_MODULE = "cross_module"  # Across module boundaries
    EXTERNAL = "external"  # External to configuration (data sources, etc.)


@dataclass
class ResolutionContext:
    """Context for reference resolution."""

    current_depth: int = 0
    max_depth: int = 50
    visited_references: Set[str] = field(default_factory=set)
    resolution_path: List[str] = field(default_factory=list)
    module_context: Optional["TerraformModule"] = None


@dataclass
class ResolutionResult:
    """Result of reference resolution attempt."""

    value: Any = None
    state: ReferenceResolutionState = ReferenceResolutionState.UNRESOLVED
    resolution_path: List[str] = field(default_factory=list)
    dependencies_used: Set[str] = field(default_factory=set)
    partial_results: Dict[str, Any] = field(
        default_factory=dict
    )  # For partial resolution
    error_message: Optional[str] = None
    resolution_time_ms: float = 0.0

    @property
    def is_successful(self) -> bool:
        return self.state in [
            ReferenceResolutionState.RESOLVED,
            ReferenceResolutionState.PARTIALLY_RESOLVED,
        ]

    @property
    def is_fully_resolved(self) -> bool:
        return self.state == ReferenceResolutionState.RESOLVED


@dataclass
class ReferenceDependencyGraph:
    """Graph structure for reference dependencies."""

    dependencies: Dict[str, Set[str]] = field(
        default_factory=dict
    )  # ref -> dependencies
    dependents: Dict[str, Set[str]] = field(default_factory=dict)  # ref -> dependents
    resolution_order: List[str] = field(
        default_factory=list
    )  # Optimal resolution order

    def add_dependency(self, reference: str, depends_on: str) -> None:
        """Add a dependency relationship."""
        if reference not in self.dependencies:
            self.dependencies[reference] = set()
        self.dependencies[reference].add(depends_on)

        if depends_on not in self.dependents:
            self.dependents[depends_on] = set()
        self.dependents[depends_on].add(reference)

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            if node in recursion_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self.dependencies.get(node, set()):
                dfs(neighbor, path + [neighbor])

            recursion_stack.remove(node)

        for node in self.dependencies:
            if node not in visited:
                dfs(node, [node])

        return cycles

    def calculate_resolution_order(self) -> List[str]:
        """Calculate optimal resolution order using topological sort."""
        in_degree = dict.fromkeys(self.dependencies, 0)

        # Calculate in-degrees
        for _node, deps in self.dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
                else:
                    in_degree[dep] = 1

        # Initialize with nodes having no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)

            for dependent in self.dependents.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Add any remaining nodes (cycles)
        remaining = [node for node, degree in in_degree.items() if degree > 0]
        order.extend(remaining)

        self.resolution_order = order
        return order


@dataclass
class TerraformReference:
    """Representation of a Terraform reference with advanced resolution capabilities."""

    reference_type: ReferenceType
    target: str  # Full target address e.g., "aws_vpc.main", "var.environment"
    attribute_path: List[str] = field(default_factory=list)  # Attribute access path

    full_reference: str = ""
    source_location: Optional[SourceLocation] = None
    scope: ReferenceScope = ReferenceScope.MODULE

    resolution_state: ReferenceResolutionState = ReferenceResolutionState.UNRESOLVED
    resolution_result: Optional[ResolutionResult] = None

    direct_dependencies: Set[str] = field(default_factory=set)
    all_dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    resolution_attempts: int = 0
    resolution_history: List[ResolutionResult] = field(default_factory=list)

    is_sensitive: bool = False
    is_computed: bool = False
    is_conditional: bool = False
    complexity_score: int = 0  # Estimated resolution complexity (0-100)

    _resolved_value: Any = None
    _dependency_graph: Optional[ReferenceDependencyGraph] = None

    def __post_init__(self):
        if not self.full_reference:
            self.full_reference = self._build_full_reference()

        self.complexity_score = self._calculate_complexity()

    def _build_full_reference(self) -> str:
        """Build the complete reference string."""
        parts = [self.reference_type.value]

        # Handle special cases
        if self.reference_type == ReferenceType.DATA_SOURCE:
            # data.aws_vpc.main -> data.aws_vpc.main
            parts.extend(
                self.target.split(".") if "." in self.target else [self.target]
            )
        elif self.reference_type == ReferenceType.RESOURCE:
            # aws_vpc.main -> aws_vpc.main
            parts.extend(
                self.target.split(".") if "." in self.target else [self.target]
            )
        else:
            # var.name -> var.name
            parts.append(self.target)

        # Add attribute path
        if self.attribute_path:
            parts.extend(self.attribute_path)

        return ".".join(parts)

    def _calculate_complexity(self) -> int:
        """Calculate resolution complexity score."""
        score = 0

        type_complexity = {
            ReferenceType.LOCAL: 1,
            ReferenceType.VARIABLE: 2,
            ReferenceType.RESOURCE: 5,
            ReferenceType.DATA_SOURCE: 8,
            ReferenceType.MODULE: 10,
            ReferenceType.FUNCTION: 15,
            ReferenceType.PATH: 1,
            ReferenceType.TERRAFORM: 3,
            ReferenceType.COUNT: 2,
            ReferenceType.EACH: 2,
            ReferenceType.SELF: 4,
        }

        score += type_complexity.get(self.reference_type, 5)

        score += len(self.attribute_path) * 2

        if self.scope == ReferenceScope.CROSS_MODULE:
            score += 10
        elif self.scope == ReferenceScope.EXTERNAL:
            score += 20

        if self.is_conditional:
            score += 5

        if self.is_computed:
            score += 3

        if self.is_sensitive:
            score += 2

        return min(score, 100)

    @property
    def is_resolved(self) -> bool:
        """Check if reference is successfully resolved."""
        return self.resolution_state in [
            ReferenceResolutionState.RESOLVED,
            ReferenceResolutionState.PARTIALLY_RESOLVED,
        ]

    @property
    def is_circular(self) -> bool:
        """Check if reference is part of circular dependency."""
        return self.resolution_state == ReferenceResolutionState.CIRCULAR

    @property
    def resolved_value(self) -> Any:
        """Get resolved value with safety checks."""
        if self.resolution_result and self.is_resolved:
            return self.resolution_result.value
        return self._resolved_value

    @resolved_value.setter
    def resolved_value(self, value: Any) -> None:
        """Set resolved value with state management."""
        self._resolved_value = value
        if value is not None:
            self.resolution_state = ReferenceResolutionState.RESOLVED
        else:
            self.resolution_state = ReferenceResolutionState.UNRESOLVED

    def add_dependency(self, dependency: "TerraformReference") -> None:
        """Add a dependency relationship."""
        dep_string = dependency.full_reference
        self.direct_dependencies.add(dep_string)

        # Update transitive dependencies
        self.all_dependencies.add(dep_string)
        self.all_dependencies.update(dependency.all_dependencies)

        # Update dependents of the dependency
        dependency.dependents.add(self.full_reference)

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Attempt to resolve this reference."""
        import time

        start_time = time.time()

        self.resolution_attempts += 1
        context.current_depth += 1

        # Check for circular reference
        if self.full_reference in context.visited_references:
            result = ResolutionResult(
                state=ReferenceResolutionState.CIRCULAR,
                resolution_path=context.resolution_path.copy(),
                error_message=f"Circular reference detected: {' -> '.join(context.resolution_path + [self.full_reference])}",
            )
            self._record_resolution(result, start_time)
            return result

        # Check depth limit
        if context.current_depth > context.max_depth:
            result = ResolutionResult(
                state=ReferenceResolutionState.UNRESOLVABLE,
                resolution_path=context.resolution_path.copy(),
                error_message=f"Maximum resolution depth ({context.max_depth}) exceeded",
            )
            self._record_resolution(result, start_time)
            return result

        # Update context
        context.visited_references.add(self.full_reference)
        context.resolution_path.append(self.full_reference)

        try:
            # Attempt resolution based on reference type
            resolution_method = self._get_resolution_method()
            result = resolution_method(context)

        except Exception as e:
            result = ResolutionResult(
                state=ReferenceResolutionState.UNRESOLVABLE,
                resolution_path=context.resolution_path.copy(),
                error_message=f"Resolution error: {str(e)}",
            )
        finally:
            # Cleanup context
            context.visited_references.remove(self.full_reference)
            context.resolution_path.pop()
            context.current_depth -= 1

        self._record_resolution(result, start_time)
        return result

    def _get_resolution_method(self):
        """Get the appropriate resolution method for this reference type."""
        resolution_methods = {
            ReferenceType.LOCAL: self._resolve_local,
            ReferenceType.VARIABLE: self._resolve_variable,
            ReferenceType.RESOURCE: self._resolve_resource,
            ReferenceType.DATA_SOURCE: self._resolve_data_source,
            ReferenceType.MODULE: self._resolve_module,
            ReferenceType.FUNCTION: self._resolve_function,
        }
        return resolution_methods.get(self.reference_type, self._resolve_generic)

    def _resolve_local(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve local reference."""
        if not context.module_context:
            return ResolutionResult(
                state=ReferenceResolutionState.UNRESOLVABLE,
                error_message="No module context provided for local resolution",
            )

        local_block = context.module_context.get_local(self.target)
        if not local_block:
            return ResolutionResult(
                state=ReferenceResolutionState.UNRESOLVABLE,
                error_message=f"Local '{self.target}' not found",
            )

        value_attr = local_block.attributes.get("value")
        if not value_attr:
            return ResolutionResult(
                state=ReferenceResolutionState.UNRESOLVABLE,
                error_message=f"Local '{self.target}' has no value attribute",
            )

        return ResolutionResult(
            value=value_attr.value.raw_value,
            state=ReferenceResolutionState.RESOLVED,
            dependencies_used={self.target},
        )

    def _resolve_variable(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve variable reference."""
        # Similar implementation to _resolve_local but for variables
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVED,  # Variables often need external input
            error_message="Variable resolution requires external input",
        )

    def _resolve_resource(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve resource reference."""
        # Implementation for resource attribute resolution
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVABLE,  # Resources often computed
            error_message="Resource attributes are computed at apply time",
        )

    def _resolve_data_source(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve data source reference."""
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVABLE,  # Data sources need provider
            error_message="Data source resolution requires provider configuration",
        )

    def _resolve_module(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve module reference."""
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVABLE,  # Modules need full resolution
            error_message="Module output resolution requires module instantiation",
        )

    def _resolve_function(self, context: ResolutionContext) -> ResolutionResult:
        """Resolve function call."""
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVABLE,  # Functions need evaluation
            error_message="Function evaluation requires runtime context",
        )

    def _resolve_generic(self, context: ResolutionContext) -> ResolutionResult:
        """Generic resolution fallback."""
        return ResolutionResult(
            state=ReferenceResolutionState.UNRESOLVABLE,
            error_message=f"No resolution method for reference type: {self.reference_type}",
        )

    def _record_resolution(self, result: ResolutionResult, start_time: float) -> None:
        """Record resolution attempt and update state."""
        result.resolution_time_ms = (time.time() - start_time) * 1000
        self.resolution_history.append(result)
        self.resolution_state = result.state
        self.resolution_result = result

        if result.is_successful:
            self._resolved_value = result.value

    def get_resolution_tree(self) -> Dict[str, Any]:
        """Get tree representation of resolution dependencies."""
        tree = {
            "reference": self.full_reference,
            "state": self.resolution_state.value,
            "resolved_value": self._serialize_value(self.resolved_value),
            "dependencies": [],
        }

        for dep in sorted(self.direct_dependencies):
            tree["dependencies"].append(dep)

        return tree

    def to_dict(self, include_resolution_history: bool = False) -> Dict[str, Any]:
        """Convert to comprehensive dictionary representation."""
        result = {
            "type": self.reference_type.value,
            "target": self.target,
            "attribute_path": self.attribute_path,
            "full_reference": self.full_reference,
            "scope": self.scope.value,
            "resolution_state": self.resolution_state.value,
            "is_resolved": self.is_resolved,
            "is_circular": self.is_circular,
            "direct_dependencies": sorted(self.direct_dependencies),
            "all_dependencies": sorted(self.all_dependencies),
            "dependents": sorted(self.dependents),
            "resolution_attempts": self.resolution_attempts,
            "complexity_score": self.complexity_score,
            "is_sensitive": self.is_sensitive,
            "is_computed": self.is_computed,
            "is_conditional": self.is_conditional,
        }

        if self.source_location:
            result["source_location"] = self.source_location.to_dict()

        if self.resolution_result:
            result["resolution_result"] = {
                "value": self._serialize_value(self.resolution_result.value),
                "state": self.resolution_result.state.value,
                "resolution_path": self.resolution_result.resolution_path,
                "dependencies_used": sorted(self.resolution_result.dependencies_used),
                "error_message": self.resolution_result.error_message,
                "resolution_time_ms": self.resolution_result.resolution_time_ms,
            }

        if include_resolution_history and self.resolution_history:
            result["resolution_history"] = [
                {
                    "value": self._serialize_value(hist.value),
                    "state": hist.state.value,
                    "resolution_path": hist.resolution_path,
                    "error_message": hist.error_message,
                    "resolution_time_ms": hist.resolution_time_ms,
                }
                for hist in self.resolution_history
            ]

        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Safely serialize any value for JSON output."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [TerraformReference._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: TerraformReference._serialize_value(v) for k, v in value.items()}
        if isinstance(value, set):
            return [TerraformReference._serialize_value(v) for v in sorted(value)]
        return str(value)

    def __str__(self) -> str:
        return f"TerraformReference({self.full_reference}, state={self.resolution_state.value})"

    def __repr__(self) -> str:
        return f"TerraformReference(type={self.reference_type.value}, target={self.target}, state={self.resolution_state.value})"


@dataclass
class TerraformFunction:
    """Represents a Terraform function call."""

    name: str
    arguments: List[Any] = field(default_factory=list)
    raw_expression: str = ""
    is_evaluable: bool = False
    evaluated_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arguments": [self._serialize_arg(arg) for arg in self.arguments],
            "raw_expression": self.raw_expression,
            "is_evaluable": self.is_evaluable,
            "evaluated_value": self.evaluated_value,
        }

    @staticmethod
    def _serialize_arg(arg: Any) -> Any:
        if isinstance(arg, TerraformReference):
            return {"_ref": arg.to_dict()}
        if isinstance(arg, TerraformFunction):
            return {"_func": arg.to_dict()}
        if isinstance(arg, (str, int, float, bool, type(None))):
            return arg
        if isinstance(arg, (list, tuple)):
            return [TerraformFunction._serialize_arg(a) for a in arg]
        if isinstance(arg, dict):
            return {k: TerraformFunction._serialize_arg(v) for k, v in arg.items()}
        return str(arg)


@dataclass
class AttributeValue:
    """Enhanced attribute value with full metadata."""

    raw_value: Any
    value_type: AttributeType
    is_computed: bool = False
    is_sensitive: bool = False
    is_required: bool = False

    # Reference and expression metadata
    references: List[TerraformReference] = field(default_factory=list)
    functions: List[TerraformFunction] = field(default_factory=list)
    has_interpolation: bool = False
    interpolation_parts: List[Union[str, TerraformReference, TerraformFunction]] = (
        field(default_factory=list)
    )

    # Resolved value (after reference resolution)
    resolved_value: Any = None
    is_fully_resolved: bool = False

    # Source information
    source_location: Optional[SourceLocation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_value": self._serialize(self.raw_value),
            "value_type": self.value_type.value,
            "is_computed": self.is_computed,
            "is_sensitive": self.is_sensitive,
            "is_required": self.is_required,
            "references": [ref.to_dict() for ref in self.references],
            "functions": [func.to_dict() for func in self.functions],
            "has_interpolation": self.has_interpolation,
            "resolved_value": self._serialize(self.resolved_value)
            if self.resolved_value
            else None,
            "is_fully_resolved": self.is_fully_resolved,
            "source_location": self.source_location.to_dict()
            if self.source_location
            else None,
        }

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple)):
            return [AttributeValue._serialize(v) for v in value]
        if isinstance(value, dict):
            return {k: AttributeValue._serialize(v) for k, v in value.items()}
        if isinstance(value, set):
            return list(value)
        return str(value)


@dataclass
class TerraformAttribute:
    """Represents a single attribute in a Terraform block."""

    name: str
    value: AttributeValue
    description: Optional[str] = None

    # Nested block information (if this attribute represents a block)
    is_block: bool = False
    block_type: Optional[str] = None
    nested_attributes: Dict[str, "TerraformAttribute"] = field(default_factory=dict)

    # Meta-argument flags
    is_meta_argument: bool = False
    meta_argument_type: Optional[str] = None  # "count", "for_each", "depends_on", etc.

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "value": self.value.to_dict(),
            "is_block": self.is_block,
        }

        if self.description:
            result["description"] = self.description

        if self.block_type:
            result["block_type"] = self.block_type

        if self.nested_attributes:
            result["nested_attributes"] = {
                k: v.to_dict() for k, v in self.nested_attributes.items()
            }

        if self.is_meta_argument:
            result["is_meta_argument"] = True
            result["meta_argument_type"] = self.meta_argument_type

        return result


@dataclass
class TerraformBlock:
    """Represents a complete Terraform block (resource, module, etc.)."""

    block_type: TerraformObjectType
    resource_type: Optional[str] = None  # e.g., "aws_vpc" for resources
    name: Optional[str] = None  # e.g., "main" in resource "aws_vpc" "main"
    labels: List[str] = field(default_factory=list)  # All labels in order

    # Attributes
    attributes: Dict[str, TerraformAttribute] = field(default_factory=dict)

    # Meta-arguments
    count: Optional[AttributeValue] = None
    for_each: Optional[AttributeValue] = None
    depends_on: List[str] = field(default_factory=list)
    explicit_provider: Optional[AttributeValue] = None
    lifecycle: Dict[str, Any] = field(default_factory=dict)

    # Dynamic blocks
    dynamic_blocks: List[Dict[str, Any]] = field(default_factory=list)

    # Source location
    source_location: Optional[SourceLocation] = None

    # Dependencies (computed)
    dependencies: Set[str] = field(default_factory=set)

    # Full address (e.g., "aws_vpc.main", "module.vpc")
    address: str = ""

    def __post_init__(self):
        if not self.address:
            self.address = self._build_address()
        self._compute_dependencies()

    def _build_address(self) -> str:
        """Build the full Terraform address for this block."""
        parts = []

        address_prefixes = {
            TerraformObjectType.RESOURCE: self.resource_type,  # resource "type" "name" -> type.name
            TerraformObjectType.DATA_SOURCE: f"data.{self.resource_type}",  # data "type" "name" -> data.type.name
            TerraformObjectType.MODULE: "module",
            TerraformObjectType.LOCAL: "local",
            TerraformObjectType.VARIABLE: "var",
            TerraformObjectType.OUTPUT: "output",
        }

        prefix = address_prefixes.get(self.block_type)

        if prefix:
            if "." in prefix:
                parts.extend(prefix.split("."))
            else:
                parts.append(prefix)

            if self.name:
                parts.append(self.name)
        elif self.block_type in (
            TerraformObjectType.TERRAFORM,
            TerraformObjectType.PROVIDER,
        ):
            parts = [self.block_type.value]
            if self.name:
                parts.append(self.name)
        else:
            parts = [self.block_type.value]
            if self.name:
                parts.append(self.name)

        return ".".join([p for p in parts if p is not None])

    def _compute_dependencies(self):
        """
        Compute all dependencies from attributes and meta-arguments.
        Enhanced to check count/for_each/explicit_provider as they often hold references.
        """
        self.dependencies.clear()

        def add_refs_from_attr_value(attr_value: Optional[AttributeValue]):
            if attr_value:
                for ref in attr_value.references:
                    self.dependencies.add(ref.target)

        self.dependencies.update(self.depends_on)

        add_refs_from_attr_value(self.count)
        add_refs_from_attr_value(self.for_each)
        add_refs_from_attr_value(self.explicit_provider)

        for attr in self.attributes.values():
            add_refs_from_attr_value(attr.value)

            self._extract_nested_dependencies(attr)

    def _extract_nested_dependencies(self, attr: TerraformAttribute):
        """Recursively extract dependencies from nested attributes."""
        for nested_attr in attr.nested_attributes.values():
            for ref in nested_attr.value.references:
                self.dependencies.add(ref.target)
            self._extract_nested_dependencies(nested_attr)

    def get_attribute(self, path: str) -> Optional[TerraformAttribute]:
        """
        Get an attribute by path (e.g., "vpc.cidr_block").
        """
        parts = path.split(".")
        current = self.attributes.get(parts[0])

        if not current:
            return None

        for part in parts[1:]:
            if not current.nested_attributes:
                return None
            current = current.nested_attributes.get(part)
            if not current:
                return None

        return current

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "block_type": self.block_type.value,
            "address": self.address,
            "attributes": {k: v.to_dict() for k, v in self.attributes.items()},
            "dependencies": list(self.dependencies),
        }

        if self.resource_type:
            result["resource_type"] = self.resource_type

        if self.name:
            result["name"] = self.name

        if self.labels:
            result["labels"] = self.labels

        if self.count:
            result["count"] = self.count.to_dict()

        if self.for_each:
            result["for_each"] = self.for_each.to_dict()

        if self.depends_on:
            result["depends_on"] = self.depends_on

        if self.explicit_provider:
            result["explicit_provider"] = self.explicit_provider.to_dict()

        if self.lifecycle:
            result["lifecycle"] = self.lifecycle

        if self.dynamic_blocks:
            result["dynamic_blocks"] = self.dynamic_blocks

        if self.source_location:
            result["source_location"] = self.source_location.to_dict()

        return result


@dataclass
class TerraformFile:
    """Represents a complete Terraform file."""

    file_path: str
    blocks: List[TerraformBlock] = field(default_factory=list)

    _resource_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _data_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _module_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _variable_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _output_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _local_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _provider_index: Dict[str, TerraformBlock] = field(default_factory=dict, repr=False)
    _terraform_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self):
        self._rebuild_indexes()

    def _rebuild_indexes(self):
        """Rebuild lookup indexes."""
        self._resource_index.clear()
        self._data_index.clear()
        self._module_index.clear()
        self._variable_index.clear()
        self._output_index.clear()
        self._local_index.clear()
        self._provider_index.clear()
        self._terraform_index.clear()

        for block in self.blocks:
            # All general blocks are indexed by their full address (e.g., "module.vpc", "aws_vpc.main")
            if block.block_type == TerraformObjectType.RESOURCE:
                self._resource_index[block.address] = block
            elif block.block_type == TerraformObjectType.DATA_SOURCE:
                self._data_index[block.address] = block
            elif block.block_type == TerraformObjectType.MODULE:
                self._module_index[block.address] = block
            elif block.block_type == TerraformObjectType.VARIABLE:
                self._variable_index[block.address] = block
            elif block.block_type == TerraformObjectType.OUTPUT:
                self._output_index[block.address] = block
            elif block.block_type == TerraformObjectType.LOCAL:
                self._local_index[block.address] = block
            elif block.block_type == TerraformObjectType.PROVIDER:
                alias_attr = block.attributes.get("alias")

                provider_key = block.address

                if (
                    alias_attr
                    and alias_attr.value
                    and isinstance(alias_attr.value.raw_value, str)
                ):
                    alias_value = alias_attr.value.raw_value.strip('"')
                    provider_key = f"{block.address}.{alias_value}"

                self._provider_index[provider_key] = block
            elif block.block_type == TerraformObjectType.TERRAFORM:
                self._terraform_index[block.address] = block

    def get_block(self, address: str) -> Optional[TerraformBlock]:
        """Get a block by its address (Enhanced logic)."""
        if address.startswith("data."):
            return self._data_index.get(address)
        elif address.startswith("module."):
            return self._module_index.get(address)
        elif address.startswith("var."):
            return self._variable_index.get(address)
        elif address.startswith("output."):
            return self._output_index.get(address)
        elif address.startswith("local."):
            return self._local_index.get(address)
        elif address.startswith("provider."):
            return self._provider_index.get(address)
        return self._resource_index.get(address) or self._terraform_index.get(address)

    def get_resources(self) -> List[TerraformBlock]:
        """Get all resources."""
        return list(self._resource_index.values())

    def get_data_sources(self) -> List[TerraformBlock]:
        """Get all data sources."""
        return list(self._data_index.values())

    def get_modules(self) -> List[TerraformBlock]:
        """Get all modules."""
        return list(self._module_index.values())

    def get_terraform_blocks(self) -> List[TerraformBlock]:
        """Get all terraform configuration blocks."""
        return list(self._terraform_index.values())

    def get_providers(
        self, provider_name: Optional[str] = None
    ) -> List[TerraformBlock]:
        """
        Get all provider configurations, optionally filtered by the base provider name (e.g., 'aws').
        """
        if not provider_name:
            return list(self._provider_index.values())

        prefix = f"provider.{provider_name}"
        return [
            block
            for address, block in self._provider_index.items()
            if address == prefix or address.startswith(f"{prefix}.")
        ]

    def get_provider(self, provider_alias_or_name: str) -> Optional[TerraformBlock]:
        """
        Get a specific provider configuration by its full address (including alias, e.g., 'aws.us-east-1')
        or by its default address ('aws').
        """
        address = f"provider.{provider_alias_or_name}"
        block = self._provider_index.get(address)
        if block:
            return block

        if "." not in provider_alias_or_name:
            address = f"provider.{provider_alias_or_name}"
            return self._provider_index.get(address)

        return None

    def get_terraform_settings(self) -> Optional[TerraformBlock]:
        """Get the terraform settings block."""
        terraform_blocks = self.get_terraform_blocks()
        return terraform_blocks[0] if terraform_blocks else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "blocks": [block.to_dict() for block in self.blocks],
            "summary": {
                "total_blocks": len(self.blocks),
                "resources": len(self._resource_index),
                "data_sources": len(self._data_index),
                "modules": len(self._module_index),
                "variables": len(self._variable_index),
                "outputs": len(self._output_index),
                "locals": len(self._local_index),
                "providers": len(self._provider_index),
                "terraform_blocks": len(self._terraform_index),
            },
        }


@dataclass
class TerraformModule:
    """Represents a complete Terraform module (collection of files)."""

    root_path: str
    files: List[TerraformFile] = field(default_factory=list)

    # Global indexes across all files
    _global_resource_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )
    _global_module_index: Dict[str, Any] = field(
        default_factory=dict,
        repr=False,
    )
    _global_variable_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )
    _global_output_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )
    _global_local_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )
    _global_provider_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )
    _global_terraform_index: Dict[str, TerraformBlock] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self):
        self._rebuild_global_indexes()

    def _rebuild_global_indexes(self):
        """Rebuild global indexes from all files."""
        self._global_resource_index.clear()
        self._global_variable_index.clear()
        self._global_output_index.clear()
        self._global_local_index.clear()
        self._global_provider_index.clear()
        self._global_terraform_index.clear()
        self._global_module_index.clear()

        for file in self.files:
            self._global_resource_index.update(file._resource_index)
            self._global_resource_index.update(file._data_index)
            self._global_module_index.update(file._module_index)
            self._global_variable_index.update(file._variable_index)
            self._global_output_index.update(file._output_index)
            self._global_local_index.update(file._local_index)
            self._global_provider_index.update(file._provider_index)
            self._global_terraform_index.update(file._terraform_index)

    def _get_index_by_address(
        self, address: str
    ) -> Optional[Dict[str, TerraformBlock]]:
        if "." not in address:
            if address == "terraform":
                return self._global_terraform_index
            elif address == "locals":
                return self._global_local_index
            else:
                return None

        prefix = address.split(".")[0]

        if prefix == "data":
            return self._global_resource_index
        elif prefix == "module":
            return self._global_module_index
        elif prefix == "var":
            return self._global_variable_index
        elif prefix == "output":
            return self._global_output_index
        elif prefix == "provider":
            return self._global_provider_index

        return self._global_resource_index

    def get_block(self, address: str) -> Optional[TerraformBlock]:
        """
        Get a block by its address, using intelligent index lookup.
        """
        target_index = self._get_index_by_address(address)

        if target_index:
            return target_index.get(address)

        return self._global_terraform_index.get(address)

    def get_resource(self, address: str) -> Optional[TerraformBlock]:
        """Get a resource block by address."""
        return self._global_resource_index.get(address)

    def get_variable(self, name: str) -> Optional[TerraformBlock]:
        """Get a variable block by name."""
        return self._global_variable_index.get(f"var.{name}")

    def get_output(self, name: str) -> Optional[TerraformBlock]:
        """Get an output block by name."""
        return self._global_output_index.get(f"output.{name}")

    def get_module(self, address: str) -> Optional[Any]:
        """Get a module block by address."""
        return self._global_module_index.get(address)

    def get_local(self, name: str) -> Optional[TerraformBlock]:
        """Get a local value block by name."""
        return self._global_local_index.get(f"local.{name}")

    def get_provider(self, provider_name: str) -> Optional[TerraformBlock]:
        """Get a provider configuration by provider name (uses label[0] as key)."""
        return self._global_provider_index.get(provider_name)

    def get_all_providers(self) -> List[TerraformBlock]:
        """Get all provider configurations."""
        return list(self._global_provider_index.values())

    def get_terraform_settings(self) -> Optional[TerraformBlock]:
        """Get the terraform settings block."""
        terraform_blocks = list(self._global_terraform_index.values())
        return terraform_blocks[0] if terraform_blocks else None

    def get_required_providers(self) -> Dict[str, Any]:
        """
        Extract required_providers from terraform blocks.

        Returns:
            Dictionary of provider names to their configuration
        """
        terraform_settings = self.get_terraform_settings()
        if not terraform_settings:
            return {}

        required_providers_attr = terraform_settings.attributes.get(
            "required_providers"
        )
        if not required_providers_attr:
            return {}

        # Access the value based on the TerraformAttribute structure
        # Try different possible attribute names to get the actual value
        if hasattr(required_providers_attr, "value") and required_providers_attr.value:
            raw_value = required_providers_attr.value
        elif hasattr(required_providers_attr, "raw_value"):
            raw_value = required_providers_attr.raw_value
        else:
            return {}

        # Handle the case where value is a list containing the dict
        if isinstance(raw_value, list) and len(raw_value) > 0:
            # Extract the first element if it's a dict
            if isinstance(raw_value[0], dict):
                return raw_value[0]
            else:
                return {}
        elif isinstance(raw_value, dict):
            return raw_value
        else:
            return {}

    def get_provider_versions(self) -> Dict[str, str]:
        """
        Extract provider versions from required_providers.

        Returns:
            Dictionary mapping provider names to version constraints
        """
        required_providers = self.get_required_providers()
        versions = {}

        for provider_name, config in required_providers.items():
            if isinstance(config, dict) and "version" in config:
                versions[provider_name] = config["version"]
            elif isinstance(config, str):
                versions[provider_name] = config

        return versions

    def resolve_reference(self, reference: TerraformReference) -> Optional[Any]:
        """
        Resolve a reference to its actual value.

        Args:
            reference: The reference to resolve

        Returns:
            Resolved value or None if not found
        """
        # This is a placeholder - will be implemented in the resolver
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "root_path": self.root_path,
            "files": [f.to_dict() for f in self.files],
            "summary": {
                "total_files": len(self.files),
                "total_resources": len(self._global_resource_index),
                "total_modules": len(self._global_module_index),
                "total_variables": len(self._global_variable_index),
                "total_outputs": len(self._global_output_index),
                "total_locals": len(self._global_local_index),
                "total_providers": len(self._global_provider_index),
                "total_terraform_blocks": len(self._global_terraform_index),
            },
            "providers": {
                "required_providers": self.get_required_providers(),
                "provider_versions": self.get_provider_versions(),
                "configured_providers": list(self._global_provider_index.keys()),
            },
        }
