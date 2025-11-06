"""
Enhanced Terraform Inspector with comprehensive metadata extraction and reference resolution.
"""

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


@dataclass
class TerraformReference:
    """Represents a reference to another Terraform object."""

    reference_type: ReferenceType
    target: str  # e.g., "aws_vpc.main", "var.environment"
    attribute_path: List[str] = field(
        default_factory=list
    )  # e.g., ["id"] or ["tags", "Name"]
    full_reference: str = ""
    is_resolvable: bool = False
    resolved_value: Any = None

    def __post_init__(self):
        if not self.full_reference:
            self.full_reference = self._build_full_reference()

    def _build_full_reference(self) -> str:
        parts = [self.reference_type.value, self.target]
        if self.attribute_path:
            parts.extend(self.attribute_path)
        return ".".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.reference_type.value,
            "target": self.target,
            "attribute_path": self.attribute_path,
            "full_reference": self.full_reference,
            "is_resolvable": self.is_resolvable,
            "resolved_value": self._serialize_value(self.resolved_value)
            if self.resolved_value
            else None,
        }

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple)):
            return [TerraformReference._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: TerraformReference._serialize_value(v) for k, v in value.items()}
        return str(value)


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
                return self._terraform_index
            elif address == "locals":
                return self._local_index
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
